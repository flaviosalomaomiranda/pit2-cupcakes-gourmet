"""Controller da vitrine (US01, US02, US03)."""
from __future__ import annotations

from flask import Blueprint, abort, make_response, render_template, request

from ..models import cupcake as cupcake_model

bp = Blueprint("vitrine", __name__)


@bp.get("/")
def index():
    categoria = request.args.get("categoria") or None
    busca = (request.args.get("q") or "").strip() or None
    categorias = cupcake_model.listar_categorias()
    if categoria and categoria not in {c["slug"] for c in categorias}:
        categoria = None  # filtro inválido vira "Todos" em vez de erro
    cupcakes = cupcake_model.listar_cupcakes(categoria, busca)
    return render_template("vitrine/index.html", cupcakes=cupcakes, categorias=categorias,
                           categoria_ativa=categoria, busca=busca or "")


@bp.get("/img/cupcake/<int:cupcake_id>.svg")
def imagem(cupcake_id: int):
    """Ilustração vetorial leve (≈1 KB) gerada com a cor da cobertura do sabor."""
    cupcake = cupcake_model.buscar_cupcake(cupcake_id)
    if cupcake is None:
        abort(404)
    svg = render_template("vitrine/cupcake.svg", cor=cupcake["cor_cobertura"], salgado=cupcake["categoria_slug"] == "salgados")
    resp = make_response(svg)
    resp.headers["Content-Type"] = "image/svg+xml; charset=utf-8"
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp


@bp.get("/cupcake/<int:cupcake_id>")
def detalhe(cupcake_id: int):
    cupcake = cupcake_model.buscar_cupcake(cupcake_id)
    if cupcake is None:
        abort(404)
    return render_template("vitrine/detalhe.html", cupcake=cupcake)
