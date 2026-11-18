"""Acesso ao banco SQLite: uma conexão por requisição, criação do esquema e carga inicial."""
from __future__ import annotations

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
    aplicar_migracoes(db)
    db.execute(
        "INSERT INTO usuario_admin (usuario, senha_hash) VALUES (?, ?)",
        (current_app.config["ADMIN_USUARIO"], generate_password_hash(current_app.config["ADMIN_SENHA"])),
    )
    db.commit()


def _colunas(db, tabela: str) -> set[str]:
    return {r[1] for r in db.execute(f"PRAGMA table_info({tabela})").fetchall()}


def aplicar_migracoes(db=None) -> list[str]:
    """Aplica, em ordem, os scripts de database/migracoes ainda não aplicados.

    A versão do banco fica em PRAGMA user_version. Assim, um banco que já tem pedidos
    (por exemplo, durante os testes com usuários) é atualizado sem perder dados.
    """
    db = db or get_db()
    aplicadas = []
    versao = db.execute("PRAGMA user_version").fetchone()[0]
    for arq in sorted((SQL_DIR / "migracoes").glob("*.sql")):
        numero = int(arq.name.split("_")[0])
        if numero <= versao:
            continue
        if numero == 1:  # colunas novas em bancos criados antes da v1.1
            cols = _colunas(db, "cupcake")
            if "ilustracao" not in cols:
                db.execute("ALTER TABLE cupcake ADD COLUMN ilustracao TEXT NOT NULL DEFAULT 'cupcake' "
                           "CHECK (ilustracao IN ('cupcake', 'lata', 'garrafa'))")
            if "enfeite" not in cols:
                db.execute("ALTER TABLE cupcake ADD COLUMN enfeite TEXT NOT NULL DEFAULT 'cereja' CHECK (enfeite IN "
                           "('cereja','morango','chocolate','limao','ervas','acai','cupuacu','coco','nenhum'))")
        db.executescript(arq.read_text(encoding="utf-8"))
        db.execute(f"PRAGMA user_version = {numero}")
        db.commit()
        aplicadas.append(arq.name)
    return aplicadas


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
