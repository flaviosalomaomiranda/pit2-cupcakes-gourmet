"""Controller do checkout: dados do cliente, endereço e pagamento (US06, US07, UC04)."""
from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from ..models import pedido as pedido_model
from ..services import RegraNegocioErro, ValidacaoErro
from ..services.pagamento import autorizar_cartao_simulado, gerar_pix_copia_e_cola, validar_cartao
from ..services.validacao import validar_cliente, validar_endereco
from .carrinho import montar_resumo

bp = Blueprint("checkout", __name__, url_prefix="/checkout")


def _pre_condicoes(resumo):
    """Pré-condições do UC04: carrinho com itens e CEP atendido."""
    if not resumo["linhas"]:
        flash("Seu carrinho está vazio.", "erro")
        return redirect(url_for("carrinho.ver"))
    if not resumo["zona"]:
        flash(resumo["erro_frete"] or "Informe o CEP de entrega para calcular o frete.", "erro")
        return redirect(url_for("carrinho.ver"))
    return None


@bp.get("/")
def formulario():
    resumo = montar_resumo()
    bloqueio = _pre_condicoes(resumo)
    if bloqueio:
        return bloqueio
    return render_template("checkout/checkout.html", **resumo, form=session.get("checkout_form", {}), erro_campo=None)


@bp.post("/")
def finalizar():
    resumo = montar_resumo()
    bloqueio = _pre_condicoes(resumo)
    if bloqueio:
        return bloqueio

    form = request.form
    # Guarda o que foi digitado (exceto dados de cartão) para não obrigar a redigitar após um erro
    seguro = {k: form.get(k, "") for k in ("nome", "telefone", "email", "logradouro", "numero", "bairro",
                                           "complemento", "metodo")}
    session["checkout_form"] = seguro

    try:
        cliente = validar_cliente(form)
        endereco = validar_endereco(form)
        metodo = form.get("metodo")
        if metodo not in ("PIX", "CARTAO"):
            raise ValidacaoErro("Escolha a forma de pagamento.", campo="metodo")

        if metodo == "CARTAO":
            final = validar_cartao(form.get("numero_cartao"), form.get("validade"), form.get("cvv"), form.get("nome_cartao"))
            aprovado, motivo = autorizar_cartao_simulado(final)
            if not aprovado:
                # Fluxo alternativo do UC04: volta à escolha de pagamento, nenhum pedido é criado
                raise RegraNegocioErro(motivo)
            pagamento = {"metodo": "CARTAO", "status": "APROVADO", "cartao_final": final}
        else:
            # txid provisório; o código definitivo do pedido é gerado no Model
            pagamento = {
                "metodo": "PIX", "status": "PENDENTE",
                "codigo_pix": "",
                "expira_em": pedido_model.expira_em(current_app.config["PIX_VALIDADE_MINUTOS"]),
            }

        if metodo == "PIX":
            pagamento["codigo_pix"] = gerar_pix_copia_e_cola(
                current_app.config["PIX_CHAVE_LOJA"], resumo["totais"]["total"], txid="DOCENUVEM")

        codigo = pedido_model.criar_pedido(
            cliente=cliente, endereco=endereco, cep=int(resumo["cep"]), zona=resumo["zona"],
            linhas=resumo["linhas"], totais=resumo["totais"], embalagem_presente=resumo["presente"],
            mensagem_presente=resumo["mensagem_presente"] if resumo["presente"] else "", pagamento=pagamento,
        )
    except ValidacaoErro as e:
        flash(e.mensagem, "erro")
        return render_template("checkout/checkout.html", **resumo, form=seguro, erro_campo=e.campo), 422
    except RegraNegocioErro as e:
        flash(e.mensagem, "erro")
        return render_template("checkout/checkout.html", **resumo, form=seguro, erro_campo="pagamento"), 422

    current_app.logger.info("Pedido %s criado (%s)", codigo, pagamento["metodo"])
    for chave in ("carrinho", "embalagem_presente", "mensagem_presente", "checkout_form"):
        session.pop(chave, None)
    session.setdefault("meus_pedidos", [])
    session["meus_pedidos"] = ([codigo] + session["meus_pedidos"])[:10]

    if pagamento["metodo"] == "PIX":
        return redirect(url_for("pedidos.pix", codigo=codigo))
    flash("Pagamento aprovado! Seu pedido já foi enviado para a cozinha.", "sucesso")
    return redirect(url_for("pedidos.acompanhar", codigo=codigo))
