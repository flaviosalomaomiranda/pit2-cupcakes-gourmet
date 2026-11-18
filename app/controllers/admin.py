"""Controller do painel do lojista (US10)."""
from __future__ import annotations

import time
from functools import wraps

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from ..models import admin as admin_model
from ..models import pedido as pedido_model
from ..services import RegraNegocioErro
from ..services.status import PROXIMO_PELO_LOJISTA, ROTULOS

bp = Blueprint("admin", __name__, url_prefix="/admin")

_TENTATIVAS: dict[str, list[float]] = {}  # limite simples de força bruta por IP (memória do processo)
_MAX_TENTATIVAS, _JANELA_SEG = 5, 300


def login_obrigatorio(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Faça login para acessar o painel.", "erro")
            return redirect(url_for("admin.login"))
        return view(*args, **kwargs)
    return wrapper


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        ip = request.remote_addr or "?"
        agora = time.time()
        recentes = [t for t in _TENTATIVAS.get(ip, []) if agora - t < _JANELA_SEG]
        if len(recentes) >= _MAX_TENTATIVAS:
            flash("Muitas tentativas. Aguarde 5 minutos.", "erro")
            return render_template("admin/login.html"), 429
        admin = admin_model.autenticar(request.form.get("usuario"), request.form.get("senha"))
        if admin:
            _TENTATIVAS.pop(ip, None)
            carrinho = session.get("carrinho")
            session.clear()  # evita fixação de sessão
            if carrinho:
                session["carrinho"] = carrinho
            session["admin_id"] = admin["id"]
            session["admin_usuario"] = admin["usuario"]
            return redirect(url_for("admin.painel"))
        _TENTATIVAS[ip] = recentes + [agora]
        flash("Usuário ou senha incorretos.", "erro")
        return render_template("admin/login.html"), 401
    return render_template("admin/login.html")


@bp.post("/logout")
def logout():
    session.pop("admin_id", None)
    session.pop("admin_usuario", None)
    flash("Você saiu do painel.", "sucesso")
    return redirect(url_for("vitrine.index"))


@bp.get("/")
@login_obrigatorio
def painel():
    pedido_model.expirar_pix_vencidos()
    filtro = request.args.get("status") or None
    if filtro and filtro not in ROTULOS:
        filtro = None
    return render_template("admin/painel.html", pedidos=pedido_model.listar_para_painel(filtro),
                           contagem=pedido_model.contagem_por_status(), filtro=filtro,
                           proximo=PROXIMO_PELO_LOJISTA, rotulos=ROTULOS,
                           total_pagos=pedido_model.total_pedidos_pagos())


@bp.post("/pedido/<codigo>/avancar")
@login_obrigatorio
def avancar(codigo: str):
    atual = request.form.get("status_atual")
    novo = PROXIMO_PELO_LOJISTA.get(atual)
    try:
        if not novo:
            raise RegraNegocioErro("Este pedido não pode avançar.")
        pedido_model.atualizar_status(codigo, novo)
        flash(f"Pedido {codigo}: {ROTULOS[novo]}.", "sucesso")
    except RegraNegocioErro as e:
        flash(e.mensagem, "erro")
    return redirect(url_for("admin.painel", status=request.args.get("status")))


@bp.post("/pedido/<codigo>/cancelar")
@login_obrigatorio
def cancelar(codigo: str):
    try:
        pedido_model.atualizar_status(codigo, "CANCELADO")
        flash(f"Pedido {codigo} cancelado.", "sucesso")
    except RegraNegocioErro as e:
        flash(e.mensagem, "erro")
    return redirect(url_for("admin.painel"))


@bp.get("/api/resumo")
@login_obrigatorio
def api_resumo():
    """Consultado a cada 15 s pelo painel: se o total de pagos aumentar, toca o alerta sonoro."""
    pedido_model.expirar_pix_vencidos()
    return jsonify(total_pagos=pedido_model.total_pedidos_pagos())
