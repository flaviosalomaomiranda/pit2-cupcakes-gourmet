"""Regras de pagamento (US07).

IMPORTANTE (limite de escopo do MVP acadêmico): não há integração real com banco/gateway.
- PIX: geramos um "Copia e Cola" no formato oficial EMV/BR Code (com CRC16), mas a
  confirmação do banco é SIMULADA por um botão que faz o papel do webhook do gateway.
- Cartão: validação real de formato (Luhn, validade, CVV); a autorização é SIMULADA.
  O número completo nunca é salvo — só os 4 últimos dígitos.
"""
from __future__ import annotations

import re
from datetime import date

from . import ValidacaoErro

# Cartões de teste: terminação 0002 simula "recusado"; 0119 simula "saldo insuficiente".
_RECUSAS_SIMULADAS = {
    "0002": "Cartão recusado pelo emissor. Tente outra forma de pagamento.",
    "0119": "Saldo insuficiente. Verifique os dados ou tente outra forma de pagamento.",
}


def luhn_valido(numero: str) -> bool:
    digitos = [int(c) for c in numero if c.isdigit()]
    if len(digitos) < 13:
        return False
    soma = 0
    for i, d in enumerate(reversed(digitos)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        soma += d
    return soma % 10 == 0


def validar_cartao(numero: str, validade: str, cvv: str, nome: str, hoje: date | None = None) -> str:
    """Valida os campos do cartão e devolve só os 4 últimos dígitos."""
    hoje = hoje or date.today()
    num = re.sub(r"\D", "", numero or "")
    if not (13 <= len(num) <= 19) or not luhn_valido(num):
        raise ValidacaoErro("Número do cartão inválido.", campo="numero_cartao")
    if len((nome or "").strip()) < 3:
        raise ValidacaoErro("Informe o nome impresso no cartão.", campo="nome_cartao")
    m = re.fullmatch(r"\s*(\d{2})\s*/\s*(\d{2}|\d{4})\s*", validade or "")
    if not m:
        raise ValidacaoErro("Validade deve estar no formato MM/AA.", campo="validade")
    mes, ano = int(m.group(1)), int(m.group(2))
    ano = ano + 2000 if ano < 100 else ano
    if not 1 <= mes <= 12:
        raise ValidacaoErro("Mês de validade inválido.", campo="validade")
    if (ano, mes) < (hoje.year, hoje.month):
        raise ValidacaoErro("Cartão vencido.", campo="validade")
    if not re.fullmatch(r"\d{3,4}", (cvv or "").strip()):
        raise ValidacaoErro("CVV deve ter 3 ou 4 números.", campo="cvv")
    return num[-4:]


def autorizar_cartao_simulado(final: str) -> tuple[bool, str]:
    """Simula a resposta do gateway. Retorna (aprovado, motivo_recusa)."""
    if final in _RECUSAS_SIMULADAS:
        return False, _RECUSAS_SIMULADAS[final]
    return True, ""


# ------------------------------- PIX ----------------------------------

def _campo(id_: str, valor: str) -> str:
    return f"{id_}{len(valor):02d}{valor}"


def crc16_ccitt(payload: str) -> str:
    crc = 0xFFFF
    for byte in payload.encode("utf-8"):
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if crc & 0x8000 else (crc << 1)
            crc &= 0xFFFF
    return f"{crc:04X}"


def gerar_pix_copia_e_cola(chave: str, valor_centavos: int, txid: str,
                           nome_loja: str = "DOCE NUVEM CUPCAKES", cidade: str = "PORTO VELHO") -> str:
    """Gera payload PIX estático no padrão EMV QRCPS (BR Code) do Banco Central."""
    if valor_centavos <= 0:
        raise ValidacaoErro("Valor do PIX deve ser positivo.")
    txid = re.sub(r"[^A-Za-z0-9]", "", txid)[:25] or "***"
    conta = _campo("00", "br.gov.bcb.pix") + _campo("01", chave)
    valor = f"{valor_centavos / 100:.2f}"
    payload = (
        _campo("00", "01")
        + _campo("26", conta)
        + _campo("52", "0000")
        + _campo("53", "986")
        + _campo("54", valor)
        + _campo("58", "BR")
        + _campo("59", nome_loja[:25])
        + _campo("60", cidade[:15])
        + _campo("62", _campo("05", txid))
        + "6304"
    )
    return payload + crc16_ccitt(payload)
