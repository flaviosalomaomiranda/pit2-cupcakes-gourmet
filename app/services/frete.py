"""Regra de negócio do frete por CEP (US08)."""
import re
from dataclasses import dataclass

from . import ValidacaoErro, RegraNegocioErro

MSG_FORA_DA_AREA = "Desculpe, ainda não entregamos nesta região."


@dataclass(frozen=True)
class Zona:
    id: int
    nome: str
    cep_inicio: int
    cep_fim: int
    valor_centavos: int
    prazo_minutos: int


def normalizar_cep(cep: str | None) -> int:
    """Aceita '76801-000', '76801000' ou ' 76.801-000 ' e devolve 76801000."""
    digitos = re.sub(r"\D", "", cep or "")
    if len(digitos) != 8:
        raise ValidacaoErro("Informe um CEP válido com 8 números (ex.: 76801-000).", campo="cep")
    if digitos == "00000000":
        raise ValidacaoErro("CEP inválido.", campo="cep")
    return int(digitos)


def formatar_cep(cep: int) -> str:
    s = f"{int(cep):08d}"
    return f"{s[:5]}-{s[5:]}"


def calcular_frete(cep: str | int, zonas: list[Zona]) -> Zona:
    """Devolve a zona que atende o CEP. Lança RegraNegocioErro se estiver fora da área."""
    cep_int = cep if isinstance(cep, int) else normalizar_cep(cep)
    for zona in zonas:
        if zona.cep_inicio <= cep_int <= zona.cep_fim:
            return zona
    raise RegraNegocioErro(MSG_FORA_DA_AREA)
