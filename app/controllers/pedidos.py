"""Controller de acompanhamento de pedido e tela do PIX (US07, US09)."""
from __future__ import annotations

import segno
from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from ..models import pedido as pedido_model
from ..models import parse_iso
from ..services import RegraNegocioErro
from ..services.status import FLUXO

bp = Blueprint("pedidos", __name__)


def _carregar(codigo: str) -> dict:
    pedido_model.expirar_pix_vencidos()
    pedido = pedido_model.buscar_por_codigo(codigo)
    if pedido is None:
        abort(404)
    return pedido


@bp.get("/pedidos")
def meus_pedidos():
    codigo = (request.args.get("codigo") or "").strip().upper()
    if codigo:
        if pedido_model.buscar_por_codigo(codigo):
            return redirect(url_for("pedidos.acompanhar", codigo=codigo))
        flash("Não encontramos um pedido com esse código. Confira as 8 letras/números.", "erro")
    return render_template("pedidos/meus_pedidos.html", codigos=session.get("meus_pedidos", []))


@bp.get("/pedido/<codigo>")
def acompanhar(codigo: str):
    pedido = _carregar(codigo)
    if pedido["status"] == "AGUARDANDO_PAGAMENTO" and pedido["pg_metodo"] == "PIX":
        return redirect(url_for("pedidos.pix", codigo=pedido["codigo"]))
    passos_feitos = {h["status"]: h["data_hora"] for h in pedido["historico"]}
    return render_template("pedidos/acompanhar.html", pedido=pedido, fluxo=FLUXO, passos_feitos=passos_feitos)


@bp.get("/pedido/<codigo>/pix")
def pix(codigo: str):
    pedido = _carregar(codigo)
    if pedido["pg_metodo"] != "PIX" or pedido["status"] != "AGUARDANDO_PAGAMENTO":
        return redirect(url_for("pedidos.acompanhar", codigo=pedido["codigo"]))
    qr_svg = segno.make(pedido["codigo_pix"], error="m").svg_data_uri(scale=5, dark="#3b1f2b")
    expira_ts = int(parse_iso(pedido["expira_em"]).timestamp())
    return render_template("pedidos/pix.html", pedido=pedido, qr_svg=qr_svg, expira_ts=expira_ts)


@bp.post("/pedido/<codigo>/pix/confirmar")
def confirmar_pix(codigo: str):
    """SIMULAÇÃO do aviso do banco (webhook). Em produção, quem chama é o gateway, não o cliente."""
    try:
        pedido_model.expirar_pix_vencidos()
        pedido_model.confirmar_pix(codigo)
        flash("Pagamento PIX confirmado! Seu pedido foi enviado para a cozinha.", "sucesso")
    except RegraNegocioErro as e:
        flash(e.mensagem, "erro")
    return redirect(url_for("pedidos.acompanhar", codigo=codigo))
