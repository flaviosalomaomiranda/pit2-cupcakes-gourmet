"""Camada CONTROLLER do MVC: Blueprints que recebem requisições, chamam o Model e escolhem a View."""
from flask import current_app, session

from ..services.carrinho import Carrinho


def carrinho_da_sessao() -> Carrinho:
    return Carrinho(session.get("carrinho"), qtd_max=current_app.config["QTD_MAX_POR_ITEM"])


def salvar_carrinho(carrinho: Carrinho) -> None:
    session["carrinho"] = carrinho.para_dict()
    session.modified = True
