"""TESTES UNITÁRIOS — regras de negócio isoladas (sem banco e sem HTTP)."""
from datetime import date

import pytest

from app.services import RegraNegocioErro, ValidacaoErro, formatar_brl
from app.services.carrinho import Carrinho, LinhaCarrinho, calcular_totais
from app.services.frete import MSG_FORA_DA_AREA, Zona, calcular_frete, formatar_cep, normalizar_cep
from app.services.pagamento import (autorizar_cartao_simulado, crc16_ccitt, gerar_pix_copia_e_cola,
                                    luhn_valido, validar_cartao)
from app.services.status import validar_transicao
from app.services.validacao import validar_cliente, validar_endereco, validar_mensagem_presente

ZONAS = [Zona(1, "Centro", 76800000, 76803999, 500, 25), Zona(2, "Zona Sul", 76804000, 76820999, 800, 35)]


# ---------------- dinheiro ----------------
@pytest.mark.parametrize("centavos, esperado", [
    (0, "R$ 0,00"), (5, "R$ 0,05"), (1250, "R$ 12,50"), (123456, "R$ 1.234,56"), (-990, "-R$ 9,90"),
])
def test_formatar_brl(centavos, esperado):
    assert formatar_brl(centavos) == esperado


# ---------------- frete (US08) ----------------
@pytest.mark.parametrize("entrada", ["76801-000", "76801000", " 76.801-000 "])
def test_normalizar_cep_aceita_formatos(entrada):
    assert normalizar_cep(entrada) == 76801000


@pytest.mark.parametrize("entrada", ["", None, "1234", "768010001", "abcde-fgh", "00000-000"])
def test_normalizar_cep_rejeita_invalidos(entrada):
    with pytest.raises(ValidacaoErro):
        normalizar_cep(entrada)


def test_formatar_cep():
    assert formatar_cep(76801000) == "76801-000"
    assert formatar_cep(1001000) == "01001-000"


def test_calcular_frete_por_zona_e_limites():
    assert calcular_frete("76801-000", ZONAS).nome == "Centro"
    assert calcular_frete("76803-999", ZONAS).nome == "Centro"      # limite superior
    assert calcular_frete("76804-000", ZONAS).nome == "Zona Sul"    # limite inferior da próxima


def test_calcular_frete_fora_da_area():
    with pytest.raises(RegraNegocioErro) as e:
        calcular_frete("01001-000", ZONAS)
    assert e.value.mensagem == MSG_FORA_DA_AREA


# ---------------- carrinho (US04, US06) ----------------
def test_carrinho_adicionar_soma_quantidades():
    c = Carrinho()
    c.adicionar(1, 2)
    c.adicionar(1, 3)
    c.adicionar(2)
    assert c.quantidade_de(1) == 5 and c.quantidade_de(2) == 1 and c.total_itens == 6


def test_carrinho_definir_zero_remove_item():
    c = Carrinho({"1": 2})
    c.definir(1, 0)
    assert c.vazio


def test_carrinho_limite_por_sabor():
    c = Carrinho(qtd_max=50)
    c.adicionar(1, 50)
    with pytest.raises(ValidacaoErro):
        c.adicionar(1, 1)


@pytest.mark.parametrize("qtd", ["abc", -1, None])
def test_carrinho_rejeita_quantidade_invalida(qtd):
    with pytest.raises(ValidacaoErro):
        Carrinho().adicionar(1, qtd)


def test_carrinho_ignora_cookie_adulterado():
    c = Carrinho({"1": 2, "x": 3, "2": -5, "3": 999, "4": "lixo"})
    assert c.para_dict() == {"1": 2}


def test_carrinho_remove_produto_que_saiu_do_cardapio():
    c = Carrinho({"1": 2, "99": 1})
    linhas = c.montar_linhas({1: {"nome": "Red Velvet", "preco_centavos": 1250, "cor_cobertura": "#c0392b"}})
    assert [l.cupcake_id for l in linhas] == [1]
    assert c.quantidade_de(99) == 0


def test_calcular_totais_com_embalagem_e_frete():
    linhas = [LinhaCarrinho(1, "A", 1250, 2, "#fff"), LinhaCarrinho(2, "B", 990, 1, "#fff")]
    t = calcular_totais(linhas, embalagem_presente=True, valor_embalagem=500, frete=800)
    assert t == {"subtotal": 3490, "embalagem": 500, "frete": 800, "total": 4790}


def test_calcular_totais_sem_frete_ainda():
    t = calcular_totais([LinhaCarrinho(1, "A", 1000, 1, "#fff")], False, 500, None)
    assert t["total"] == 1000 and t["embalagem"] == 0


# ---------------- pagamento (US07) ----------------
@pytest.mark.parametrize("numero, ok", [
    ("4111 1111 1111 1111", True), ("4000000000000002", True), ("5555555555554444", True),
    ("4111111111111112", False), ("1234", False), ("", False),
])
def test_luhn(numero, ok):
    assert luhn_valido(numero) is ok


def test_validar_cartao_ok_devolve_so_final():
    final = validar_cartao("4111 1111 1111 1111", "12/30", "123", "MARIA SILVA", hoje=date(2026, 11, 17))
    assert final == "1111"


@pytest.mark.parametrize("numero, validade, cvv, nome, campo", [
    ("4111111111111112", "12/30", "123", "MARIA", "numero_cartao"),
    ("4111111111111111", "12/30", "123", "", "nome_cartao"),
    ("4111111111111111", "1230", "123", "MARIA", "validade"),
    ("4111111111111111", "13/30", "123", "MARIA", "validade"),
    ("4111111111111111", "10/26", "123", "MARIA", "validade"),   # vencido em nov/2026
    ("4111111111111111", "12/30", "12", "MARIA", "cvv"),
])
def test_validar_cartao_erros(numero, validade, cvv, nome, campo):
    with pytest.raises(ValidacaoErro) as e:
        validar_cartao(numero, validade, cvv, nome, hoje=date(2026, 11, 17))
    assert e.value.campo == campo


def test_validade_com_ano_de_4_digitos():
    assert validar_cartao("4111111111111111", "12/2030", "123", "MARIA", hoje=date(2026, 11, 17)) == "1111"


def test_cartao_do_mes_corrente_ainda_vale():
    assert validar_cartao("4111111111111111", "11/26", "123", "MARIA", hoje=date(2026, 11, 17)) == "1111"


def test_autorizacao_simulada():
    assert autorizar_cartao_simulado("1111") == (True, "")
    aprovado, motivo = autorizar_cartao_simulado("0002")
    assert not aprovado and "recusado" in motivo.lower()


def test_crc16_vetor_de_referencia():
    # Vetor oficial do CRC-16/CCITT-FALSE
    assert crc16_ccitt("123456789") == "29B1"


def test_pix_copia_e_cola_estrutura_e_crc():
    payload = gerar_pix_copia_e_cola("pix@docenuvem.com.br", 4790, "PEDIDO123")
    assert payload.startswith("000201")
    assert "br.gov.bcb.pix" in payload and "540547.90" in payload and "5802BR" in payload
    assert payload[-8:-4] == "6304"
    assert crc16_ccitt(payload[:-4]) == payload[-4:]


def test_pix_valor_invalido():
    with pytest.raises(ValidacaoErro):
        gerar_pix_copia_e_cola("x@y.com", 0, "T")


# ---------------- validação de dados ----------------
def test_validar_cliente_limpa_dados():
    c = validar_cliente({"nome": "  Ana   Lima ", "telefone": "(69) 98888-7777", "email": " ANA@X.COM "})
    assert c == {"nome": "Ana Lima", "telefone": "69988887777", "email": "ana@x.com"}


@pytest.mark.parametrize("dados, campo", [
    ({"nome": "Al", "telefone": "69988887777", "email": "a@b.com"}, "nome"),
    ({"nome": "Ana", "telefone": "9888", "email": "a@b.com"}, "telefone"),
    ({"nome": "Ana", "telefone": "69988887777", "email": "sem-arroba"}, "email"),
])
def test_validar_cliente_erros(dados, campo):
    with pytest.raises(ValidacaoErro) as e:
        validar_cliente(dados)
    assert e.value.campo == campo


def test_validar_endereco_complemento_opcional():
    e = validar_endereco({"logradouro": "Rua A", "numero": "1", "bairro": "Centro"})
    assert e["complemento"] == ""


def test_mensagem_presente_limite():
    assert validar_mensagem_presente("  Parabéns!  ") == "Parabéns!"
    with pytest.raises(ValidacaoErro):
        validar_mensagem_presente("x" * 141)


# ---------------- status (US09, US10) ----------------
@pytest.mark.parametrize("atual, novo", [
    ("AGUARDANDO_PAGAMENTO", "RECEBIDO"), ("RECEBIDO", "EM_PREPARO"),
    ("EM_PREPARO", "SAIU_PARA_ENTREGA"), ("SAIU_PARA_ENTREGA", "ENTREGUE"), ("RECEBIDO", "CANCELADO"),
])
def test_transicoes_validas(atual, novo):
    validar_transicao(atual, novo)


@pytest.mark.parametrize("atual, novo", [
    ("ENTREGUE", "EM_PREPARO"), ("RECEBIDO", "ENTREGUE"), ("CANCELADO", "RECEBIDO"),
    ("SAIU_PARA_ENTREGA", "CANCELADO"), ("RECEBIDO", "INEXISTENTE"),
])
def test_transicoes_invalidas(atual, novo):
    with pytest.raises(RegraNegocioErro):
        validar_transicao(atual, novo)
