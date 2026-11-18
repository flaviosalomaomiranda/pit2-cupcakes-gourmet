"""Acesso ao banco SQLite: uma conexão por requisição, criação do esquema e carga inicial."""
import sqlite3
from pathlib import Path

import click
from flask import current_app, g
from werkzeug.security import generate_password_hash

SQL_DIR = Path(__file__).resolve().parent.parent / "database"


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        caminho = current_app.config["DATABASE"]
        if caminho != ":memory:":
            Path(caminho).parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(caminho, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Recria o banco a partir de schema.sql + seed.sql e cria o usuário administrador."""
    db = get_db()
    db.executescript((SQL_DIR / "schema.sql").read_text(encoding="utf-8"))
    db.executescript((SQL_DIR / "seed.sql").read_text(encoding="utf-8"))
    db.execute(
        "INSERT INTO usuario_admin (usuario, senha_hash) VALUES (?, ?)",
        (current_app.config["ADMIN_USUARIO"], generate_password_hash(current_app.config["ADMIN_SENHA"])),
    )
    db.commit()


def banco_existe() -> bool:
    db = get_db()
    row = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pedido'").fetchone()
    return row is not None


@click.command("init-db")
def init_db_command():
    """Comando: flask --app run init-db"""
    init_db()
    click.echo("Banco de dados criado e populado.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
