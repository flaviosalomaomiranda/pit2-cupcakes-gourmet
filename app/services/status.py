"""Máquina de estados do pedido (US09, US10). Impede saltos indevidos (ex.: ENTREGUE -> EM_PREPARO)."""
from __future__ import annotations

from . import RegraNegocioErro

ROTULOS = {
    "AGUARDANDO_PAGAMENTO": "Aguardando pagamento",
    "RECEBIDO": "Pedido recebido",
    "EM_PREPARO": "Em preparo",
    "SAIU_PARA_ENTREGA": "Saiu para entrega",
    "ENTREGUE": "Entregue",
    "CANCELADO": "Cancelado",
}

# Sequência exibida na linha do tempo do cliente
FLUXO = ["RECEBIDO", "EM_PREPARO", "SAIU_PARA_ENTREGA", "ENTREGUE"]

TRANSICOES = {
    "AGUARDANDO_PAGAMENTO": {"RECEBIDO", "CANCELADO"},
    "RECEBIDO": {"EM_PREPARO", "CANCELADO"},
    "EM_PREPARO": {"SAIU_PARA_ENTREGA", "CANCELADO"},
    "SAIU_PARA_ENTREGA": {"ENTREGUE"},
    "ENTREGUE": set(),
    "CANCELADO": set(),
}

# Ações que o lojista pode fazer no painel (o pagamento é quem leva a RECEBIDO)
PROXIMO_PELO_LOJISTA = {
    "RECEBIDO": "EM_PREPARO",
    "EM_PREPARO": "SAIU_PARA_ENTREGA",
    "SAIU_PARA_ENTREGA": "ENTREGUE",
}


def validar_transicao(atual: str, novo: str) -> None:
    if atual not in TRANSICOES or novo not in ROTULOS:
        raise RegraNegocioErro("Status desconhecido.")
    if novo not in TRANSICOES[atual]:
        raise RegraNegocioErro(f"Não é possível passar de '{ROTULOS[atual]}' para '{ROTULOS[novo]}'.")
