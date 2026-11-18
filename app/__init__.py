"""Fábrica da aplicação Flask — Doce Nuvem Cupcakes Gourmet.

Arquitetura MVC:
  Model      -> app/models (acesso a dados) + app/services (regras de negócio)
  View       -> app/templates (Jinja2/HTML) + app/static (CSS/JS)
  Controller -> app/controllers (Blueprints Flask: recebem a requisição e decidem a resposta)
"""
from __future__ import annotations

import logging
import secrets
from datetime import timedelta, timezone
from zoneinfo import ZoneInfo

from flask import Flask, abort, render_template, request, session

from . import db
from .config import Config
from .models import parse_iso
from .services import formatar_brl
from .services.frete import formatar_cep
from .services.status import ROTULOS

try:
    FUSO_LOJA = ZoneInfo("America/Porto_Velho")
except Exception:  # Windows sem base de fusos (pacote tzdata ausente): Porto Velho é UTC-4 o ano todo
    FUSO_LOJA = timezone(timedelta(hours=-4), "America/Porto_Velho")


def create_app(config_obj=Config, **overrides) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_obj)
    app.config.update(overrides)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    db.init_app(app)

    with app.app_context():
        if not db.banco_existe():
            db.init_db()
            app.logger.info("Banco criado automaticamente em %s", app.config["DATABASE"])
        else:
            for m in db.aplicar_migracoes():
                app.logger.info("Migração aplicada: %s", m)

    from .controllers import admin, carrinho, checkout, pedidos, vitrine
    for bp in (vitrine.bp, carrinho.bp, checkout.bp, pedidos.bp, admin.bp):
        app.register_blueprint(bp)

    _registrar_seguranca(app)
    _registrar_filtros(app)
    _registrar_erros(app)
    return app


def _registrar_seguranca(app: Flask) -> None:
    """Proteção CSRF simples: todo POST precisa do token da sessão."""

    def csrf_token() -> str:
        if "_csrf" not in session:
            session["_csrf"] = secrets.token_urlsafe(32)
        return session["_csrf"]

    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def verificar_csrf():
        if request.method == "POST":
            enviado = request.form.get("_csrf") or request.headers.get("X-CSRF-Token")
            if not enviado or not secrets.compare_digest(enviado, session.get("_csrf", "")):
                abort(400, description="Sessão expirada ou formulário inválido. Recarregue a página e tente de novo.")

    @app.after_request
    def cabecalhos_seguranca(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "same-origin")
        resp.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; frame-ancestors 'none'",
        )
        return resp


def _registrar_filtros(app: Flask) -> None:
    app.jinja_env.filters["brl"] = formatar_brl
    app.jinja_env.filters["cep"] = formatar_cep
    app.jinja_env.filters["status"] = lambda s: ROTULOS.get(s, s)

    def telefone(t: str) -> str:
        t = t or ""
        if len(t) == 11:
            return f"({t[:2]}) {t[2:7]}-{t[7:]}"
        if len(t) == 10:
            return f"({t[:2]}) {t[2:6]}-{t[6:]}"
        return t

    app.jinja_env.filters["telefone"] = telefone

    def data_local(iso: str, fmt="%d/%m/%Y %H:%M") -> str:
        try:
            return parse_iso(iso).astimezone(FUSO_LOJA).strftime(fmt)
        except (TypeError, ValueError):
            return iso or ""

    app.jinja_env.filters["data_local"] = data_local

    @app.context_processor
    def contexto_global():
        itens = session.get("carrinho") or {}
        total = 0
        for q in itens.values():
            try:
                total += int(q)
            except (TypeError, ValueError):
                pass
        return {"qtd_carrinho": total, "admin_logado": bool(session.get("admin_id"))}


def _registrar_erros(app: Flask) -> None:
    @app.errorhandler(400)
    def erro_400(e):
        return render_template("errors/erro.html", codigo=400, titulo="Requisição inválida",
                               mensagem=getattr(e, "description", "")), 400

    @app.errorhandler(404)
    def erro_404(_e):
        return render_template("errors/erro.html", codigo=404, titulo="Página não encontrada",
                               mensagem="O endereço acessado não existe ou o produto saiu do cardápio."), 404

    @app.errorhandler(500)
    def erro_500(e):
        app.logger.exception("Erro interno: %s", e)
        return render_template("errors/erro.html", codigo=500, titulo="Algo deu errado",
                               mensagem="Tivemos um problema inesperado. Seu carrinho foi preservado; tente novamente."), 500
