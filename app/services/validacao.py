"""Validação e limpeza dos dados digitados no checkout."""
import re

from . import ValidacaoErro

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")


def _texto(dados: dict, campo: str, rotulo: str, minimo: int, maximo: int, obrigatorio=True) -> str:
    valor = re.sub(r"\s+", " ", (dados.get(campo) or "")).strip()
    if not valor and not obrigatorio:
        return ""
    if len(valor) < minimo:
        raise ValidacaoErro(f"{rotulo} é obrigatório." if not valor else f"{rotulo} muito curto.", campo=campo)
    if len(valor) > maximo:
        raise ValidacaoErro(f"{rotulo} deve ter no máximo {maximo} caracteres.", campo=campo)
    return valor


def validar_cliente(dados: dict) -> dict:
    nome = _texto(dados, "nome", "Nome", 3, 80)
    telefone = re.sub(r"\D", "", dados.get("telefone") or "")
    if len(telefone) not in (10, 11):
        raise ValidacaoErro("Telefone deve ter DDD + número (10 ou 11 dígitos).", campo="telefone")
    email = (dados.get("email") or "").strip().lower()
    if not _EMAIL_RE.match(email) or len(email) > 120:
        raise ValidacaoErro("E-mail inválido.", campo="email")
    return {"nome": nome, "telefone": telefone, "email": email}


def validar_endereco(dados: dict) -> dict:
    return {
        "logradouro": _texto(dados, "logradouro", "Rua/avenida", 3, 120),
        "numero": _texto(dados, "numero", "Número", 1, 10),
        "bairro": _texto(dados, "bairro", "Bairro", 2, 60),
        "complemento": _texto(dados, "complemento", "Complemento", 0, 60, obrigatorio=False),
    }


def validar_mensagem_presente(texto: str | None) -> str:
    texto = re.sub(r"\s+", " ", texto or "").strip()
    if len(texto) > 140:
        raise ValidacaoErro("A mensagem do presente deve ter no máximo 140 caracteres.", campo="mensagem_presente")
    return texto
