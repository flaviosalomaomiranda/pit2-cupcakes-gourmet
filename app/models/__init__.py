"""Camada MODEL do MVC: acesso a dados (SQL parametrizado) e persistência das entidades."""
from datetime import datetime, timezone


def agora_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(texto: str) -> datetime:
    return datetime.strptime(texto, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
