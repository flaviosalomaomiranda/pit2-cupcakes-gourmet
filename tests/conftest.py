import re

import pytest

from app import create_app
from app.config import TestConfig


@pytest.fixture()
def app(tmp_path):
    """Cada teste recebe um banco novo e isolado (arquivo temporário)."""
    app = create_app(TestConfig, DATABASE=str(tmp_path / "teste.db"))
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


def pegar_csrf(client) -> str:
    """Abre uma página para gerar o token CSRF na sessão e o extrai do HTML."""
    html = client.get("/").get_data(as_text=True)
    return re.search(r'name="csrf-token" content="([^"]+)"', html).group(1)


@pytest.fixture()
def csrf(client):
    return pegar_csrf(client)


@pytest.fixture()
def db(app):
    from app.db import get_db
    with app.app_context():
        yield get_db()


def encher_carrinho_e_frete(client, csrf, itens=((1, 2),), cep="76801-000"):
    for cid, q in itens:
        client.post(f"/carrinho/adicionar/{cid}", data={"_csrf": csrf, "quantidade": q})
    client.post("/carrinho/frete", data={"_csrf": csrf, "cep": cep})


DADOS_CLIENTE = {
    "nome": "Maria da Silva", "telefone": "(69) 99999-0000", "email": "maria@exemplo.com",
    "logradouro": "Av. Sete de Setembro", "numero": "123", "bairro": "Centro", "complemento": "Apto 2",
}
