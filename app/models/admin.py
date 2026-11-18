"""Model: Usuário administrador (lojista)."""
from __future__ import annotations

from werkzeug.security import check_password_hash

from ..db import get_db


def autenticar(usuario: str, senha: str) -> dict | None:
    row = get_db().execute(
        "SELECT id, usuario, senha_hash FROM usuario_admin WHERE usuario = ?", ((usuario or "").strip(),)
    ).fetchone()
    if row and check_password_hash(row["senha_hash"], senha or ""):
        return {"id": row["id"], "usuario": row["usuario"]}
    return None
