"""Controller do carrinho (US04, US05, US06, US08)."""
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, session, url_for

from ..models import cupcake as cupcake_model
from ..models.zona import listar_zonas
from ..services import RegraNegocioErro, ValidacaoErro, formatar_brl
from ..services.carrinho import calcular_totais
from ..services.frete import calcular_frete, formatar_cep, normalizar_cep
from . import carrinho_da_sessao, salvar_carrinho

bp = Blueprint("carrinho", __name__, url_prefix="/carrinho")


def montar_resumo():
    """Usado pelo carrinho e pelo checkout: linhas + totais + frete calculado (se houver CEP)."""
    carrinho = carrinho_da_sessao()
    produtos = cupcake_model.mapa_cupcakes_ativos(carrinho.ids())
    linhas = carrinho.montar_linhas(produtos)
    salvar_carrinho(carrinho)  # remove itens que saíram do cardápio

    zona, erro_frete = None, None
    cep = session.get("cep")
    if cep:
        try:
            zona = calcular_frete(int(cep), listar_zonas())
        except RegraNegocioErro as e:
            erro_frete = e.mensagem
    presente = bool(session.get("embalagem_presente"))
    totais = calcular_totais(linhas, presente, current_app.config["VALOR_EMBALAGEM_PRESENTE_CENTAVOS"],
                             zona.valor_centavos if zona else None)
    return {"linhas": linhas, "totais": totais, "zona": zona, "erro_frete": erro_frete,
            "cep": cep, "presente": presente, "mensagem_presente": session.get("mensagem_presente", "")}


@bp.get("/")
def ver():
    return render_template("carrinho/carrinho.html", **montar_resumo(),
                           valor_embalagem=current_app.config["VALOR_EMBALAGEM_PRESENTE_CENTAVOS"])


@bp.post("/adicionar/<int:cupcake_id>")
def adicionar(cupcake_id: int):
    cupcake = cupcake_model.buscar_cupcake(cupcake_id)
    if cupcake is None:
        flash("Este cupcake não está mais disponível.", "erro")
        return redirect(url_for("vitrine.index"))
    carrinho = carrinho_da_sessao()
    via_js = request.headers.get("X-Requested-With") == "fetch"
    try:
        carrinho.adicionar(cupcake_id, request.form.get("quantidade", 1))
        salvar_carrinho(carrinho)
        if via_js:
            return jsonify(ok=True, total_itens=carrinho.total_itens)
        flash(f"{cupcake['nome']} adicionado ao carrinho.", "sucesso")
    except ValidacaoErro as e:
        if via_js:
            return jsonify(ok=False, mensagem=e.mensagem), 422
        flash(e.mensagem, "erro")
    destino = request.form.get("voltar")
    if destino == "detalhe":
        return redirect(url_for("vitrine.detalhe", cupcake_id=cupcake_id))
    return redirect(request.referrer if _referrer_interno() else url_for("vitrine.index"))


@bp.post("/alterar/<int:cupcake_id>")
def alterar(cupcake_id: int):
    carrinho = carrinho_da_sessao()
    acao = request.form.get("acao")
    try:
        atual = carrinho.quantidade_de(cupcake_id)
        if acao == "mais":
            carrinho.definir(cupcake_id, atual + 1)
        elif acao == "menos":
            carrinho.definir(cupcake_id, atual - 1)
        elif acao == "remover":
            carrinho.remover(cupcake_id)
        else:
            carrinho.definir(cupcake_id, request.form.get("quantidade"))
        salvar_carrinho(carrinho)
    except ValidacaoErro as e:
        flash(e.mensagem, "erro")
    return redirect(url_for("carrinho.ver"))


@bp.post("/frete")
def frete():
    try:
        cep = normalizar_cep(request.form.get("cep"))
        session["cep"] = cep
        zona = calcular_frete(cep, listar_zonas())
        flash(f"Entregamos em {formatar_cep(cep)} ({zona.nome}): {formatar_brl(zona.valor_centavos)} — "
              f"até {zona.prazo_minutos} min.", "sucesso")
    except ValidacaoErro as e:
        flash(e.mensagem, "erro")
    except RegraNegocioErro as e:
        flash(e.mensagem, "erro")
    return redirect(url_for("carrinho.ver"))


@bp.post("/embalagem")
def embalagem():
    from ..services.validacao import validar_mensagem_presente
    session["embalagem_presente"] = request.form.get("embalagem_presente") == "1"
    try:
        session["mensagem_presente"] = validar_mensagem_presente(request.form.get("mensagem_presente"))
    except ValidacaoErro as e:
        flash(e.mensagem, "erro")
    return redirect(url_for("carrinho.ver"))


@bp.get("/api/frete")
def api_frete():
    """Endpoint JSON usado pelo JavaScript para mostrar o frete antes de enviar o formulário."""
    try:
        zona = calcular_frete(request.args.get("cep", ""), listar_zonas())
        return jsonify(ok=True, zona=zona.nome, valor=formatar_brl(zona.valor_centavos), prazo=zona.prazo_minutos)
    except (ValidacaoErro, RegraNegocioErro) as e:
        return jsonify(ok=False, mensagem=e.mensagem), 422


def _referrer_interno() -> bool:
    ref = request.referrer or ""
    return ref.startswith(request.host_url)
