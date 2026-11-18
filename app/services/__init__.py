"""Regras de negócio puras (sem acesso a banco nem HTTP): fáceis de testar isoladamente."""
from __future__ import annotations

class ValidacaoErro(ValueError):
    """Dado de entrada inválido. A mensagem é segura para exibir ao usuário."""

    def __init__(self, mensagem: str, campo: str | None = None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.campo = campo


class RegraNegocioErro(Exception):
    """Operação válida no formato, mas proibida pelas regras do negócio."""

    def __init__(self, mensagem: str):
        super().__init__(mensagem)
        self.mensagem = mensagem


def formatar_brl(centavos: int) -> str:
    """1250 -> 'R$ 12,50'  |  123456 -> 'R$ 1.234,56'"""
    sinal = "-" if centavos < 0 else ""
    centavos = abs(int(centavos))
    reais, cents = divmod(centavos, 100)
    reais_fmt = f"{reais:,}".replace(",", ".")
    return f"{sinal}R$ {reais_fmt},{cents:02d}"
