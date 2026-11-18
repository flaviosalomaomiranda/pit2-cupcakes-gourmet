"""TESTES DE INTEGRAÇÃO — percorrem Controller + Model + banco SQLite real via cliente HTTP do Flask.

Cada teste referencia a história de usuário (US) ou o caso de uso (UC) que valida.
"""
import re
import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from tests.conftest import DADOS_CLIENTE, encher_carrinho_e_frete, pegar_csrf


def _codigo_da_url(resp) -> str:
    return re.search(r"/pedido/([A-Z0-9]{8})", resp.headers["Location"]).group(1)


# ------------------------------------------------------------- vitrine
def test_us01_vitrine_lista_todos_os_cupcakes_com_preco(client):
    html = client.get("/").get_data(as_text=True)
    assert html.count('class="card"') == 11
    assert "Red Velvet" in html and "R$ 12,50" in html


def test_us02_filtro_por_categoria(client):
    html = client.get("/?categoria=diet").get_data(as_text=True)
    assert html.count('class="card"') == 2 and "Chocolate Diet" in html and "Red Velvet" not in html


def test_us02_busca_por_ingrediente(client):
    html = client.get("/?q=castanha").get_data(as_text=True)
    assert "Açaí com Castanha" in html and html.count('class="card"') == 1


def test_us02_busca_sem_resultado_mostra_mensagem(client):
    assert "Nenhum cupcake encontrado" in client.get("/?q=pizza").get_data(as_text=True)


def test_us02_categoria_invalida_vira_todos(client):
    assert client.get("/?categoria=<script>").get_data(as_text=True).count('class="card"') == 11


def test_us03_detalhe_mostra_ingredientes_e_alergenicos(client):
    html = client.get("/cupcake/1").get_data(as_text=True)
    assert "Ingredientes" in html and "cream cheese" in html and "Contém:" in html


def test_detalhe_inexistente_retorna_404_amigavel(client):
    r = client.get("/cupcake/9999")
    assert r.status_code == 404 and "Página não encontrada" in r.get_data(as_text=True)


def test_imagem_svg_do_cupcake(client):
    r = client.get("/img/cupcake/1.svg")
    assert r.status_code == 200 and r.mimetype == "image/svg+xml" and "#c0392b" in r.get_data(as_text=True)


# ------------------------------------------------------------- carrinho
def test_us04_adicionar_e_contador_do_topo(client, csrf):
    client.post("/carrinho/adicionar/1", data={"_csrf": csrf, "quantidade": 2})
    client.post("/carrinho/adicionar/7", data={"_csrf": csrf})
    html = client.get("/carrinho/").get_data(as_text=True)
    assert 'data-badge>3<' in html and "Red Velvet" in html and "Queijo e Ervas" in html


def test_us04_adicionar_via_javascript_retorna_json(client, csrf):
    r = client.post("/carrinho/adicionar/1", data={"_csrf": csrf}, headers={"X-Requested-With": "fetch"})
    assert r.get_json() == {"ok": True, "total_itens": 1}


def test_us04_mais_menos_e_zero_remove(client, csrf):
    client.post("/carrinho/adicionar/1", data={"_csrf": csrf})
    client.post("/carrinho/alterar/1", data={"_csrf": csrf, "acao": "mais"})
    assert "R$ 25,00" in client.get("/carrinho/").get_data(as_text=True)
    client.post("/carrinho/alterar/1", data={"_csrf": csrf, "acao": "menos"})
    client.post("/carrinho/alterar/1", data={"_csrf": csrf, "acao": "menos"})
    assert "Seu carrinho está vazio" in client.get("/carrinho/").get_data(as_text=True)


def test_us04_carrinho_vazio_tem_botao_ver_cupcakes(client):
    html = client.get("/carrinho/").get_data(as_text=True)
    assert "Seu carrinho está vazio" in html and "Ver cupcakes" in html


def test_us04_limite_de_50_por_sabor(client, csrf):
    client.post("/carrinho/adicionar/1", data={"_csrf": csrf, "quantidade": 50})
    r = client.post("/carrinho/adicionar/1", data={"_csrf": csrf, "quantidade": 1}, follow_redirects=True)
    assert "Limite de 50" in r.get_data(as_text=True)


def test_us05_embalagem_presente_soma_ao_total(client, csrf):
    encher_carrinho_e_frete(client, csrf, itens=((1, 1),))
    client.post("/carrinho/embalagem", data={"_csrf": csrf, "embalagem_presente": "1", "mensagem_presente": "Feliz aniversário!"})
    html = client.get("/carrinho/").get_data(as_text=True)
    assert "Embalagem presente" in html and "R$ 22,50" in html  # 12,50 + 5,00 + 5,00


def test_us08_frete_dentro_da_area(client, csrf):
    client.post("/carrinho/adicionar/1", data={"_csrf": csrf})
    r = client.post("/carrinho/frete", data={"_csrf": csrf, "cep": "76810-000"}, follow_redirects=True)
    html = r.get_data(as_text=True)
    assert "Zona Sul" in html and "R$ 8,00" in html and "Ir para pagamento" in html


def test_us08_frete_fora_da_area_bloqueia_pagamento(client, csrf):
    client.post("/carrinho/adicionar/1", data={"_csrf": csrf})
    html = client.post("/carrinho/frete", data={"_csrf": csrf, "cep": "01001-000"}, follow_redirects=True).get_data(as_text=True)
    assert "ainda não entregamos nesta região" in html and "Ir para pagamento" not in html


def test_us08_api_frete(client):
    assert client.get("/carrinho/api/frete?cep=76801000").get_json()["ok"] is True
    r = client.get("/carrinho/api/frete?cep=123")
    assert r.status_code == 422 and r.get_json()["ok"] is False


# ------------------------------------------------------------- checkout
def test_uc04_checkout_exige_carrinho(client):
    r = client.get("/checkout/")
    assert r.status_code == 302 and r.headers["Location"].endswith("/carrinho/")


def test_uc04_checkout_exige_frete(client, csrf):
    client.post("/carrinho/adicionar/1", data={"_csrf": csrf})
    assert client.get("/checkout/").status_code == 302


def test_uc04_cartao_aprovado_cria_pedido_recebido(client, csrf, app):
    encher_carrinho_e_frete(client, csrf, itens=((1, 2), (7, 1)))
    r = client.post("/checkout/", data={**DADOS_CLIENTE, "_csrf": csrf, "metodo": "CARTAO",
                                        "numero_cartao": "4111 1111 1111 1111", "nome_cartao": "MARIA SILVA",
                                        "validade": "12/35", "cvv": "123"})
    assert r.status_code == 302
    codigo = _codigo_da_url(r)
    with app.app_context():
        from app.db import get_db
        p = get_db().execute("SELECT * FROM pedido WHERE codigo = ?", (codigo,)).fetchone()
        assert p["status"] == "RECEBIDO"
        assert p["subtotal_centavos"] == 2 * 1250 + 990 and p["frete_centavos"] == 500
        assert p["total_centavos"] == 3990
        pg = get_db().execute("SELECT * FROM pagamento WHERE pedido_id = ?", (p["id"],)).fetchone()
        assert pg["status"] == "APROVADO" and pg["cartao_final"] == "1111"
    # carrinho é esvaziado após a compra
    assert "Seu carrinho está vazio" in client.get("/carrinho/").get_data(as_text=True)


def test_uc04_cartao_nunca_e_salvo_completo(client, csrf, app):
    encher_carrinho_e_frete(client, csrf)
    client.post("/checkout/", data={**DADOS_CLIENTE, "_csrf": csrf, "metodo": "CARTAO",
                                    "numero_cartao": "4111111111111111", "nome_cartao": "MARIA", "validade": "12/35", "cvv": "123"})
    with app.app_context():
        from app.db import get_db
        dump = "\n".join(get_db().iterdump())
    assert "4111111111111111" not in dump          # número completo nunca é gravado
    assert "cvv" not in dump.lower()               # não existe nem coluna de CVV


def test_uc04_cartao_recusado_nao_cria_pedido(client, csrf, app):
    encher_carrinho_e_frete(client, csrf)
    r = client.post("/checkout/", data={**DADOS_CLIENTE, "_csrf": csrf, "metodo": "CARTAO",
                                        "numero_cartao": "4000 0000 0000 0002", "nome_cartao": "MARIA", "validade": "12/35", "cvv": "123"})
    assert r.status_code == 422 and "recusado" in r.get_data(as_text=True).lower()
    with app.app_context():
        from app.db import get_db
        assert get_db().execute("SELECT COUNT(*) FROM pedido").fetchone()[0] == 0
    # dados digitados (exceto cartão) são preservados
    assert 'value="Maria da Silva"' in r.get_data(as_text=True)


def test_uc04_validacao_mostra_campo_com_erro(client, csrf):
    encher_carrinho_e_frete(client, csrf)
    r = client.post("/checkout/", data={**DADOS_CLIENTE, "_csrf": csrf, "metodo": "PIX", "email": "invalido"})
    html = r.get_data(as_text=True)
    assert r.status_code == 422 and "E-mail inválido" in html and re.search(r'id="email"[^>]*aria-invalid="true"', html)


def test_uc04_pix_fluxo_completo(client, csrf, app):
    encher_carrinho_e_frete(client, csrf, itens=((9, 3),), cep="76825-000")
    r = client.post("/checkout/", data={**DADOS_CLIENTE, "_csrf": csrf, "metodo": "PIX"})
    codigo = _codigo_da_url(r)
    assert r.headers["Location"].endswith("/pix")
    html = client.get(f"/pedido/{codigo}/pix").get_data(as_text=True)
    assert "PIX Copia e Cola" in html and "data:image/svg+xml" in html and "000201" in html
    # acompanhar redireciona para o PIX enquanto não pago
    assert client.get(f"/pedido/{codigo}").status_code == 302
    # banco confirma (simulação do webhook)
    r = client.post(f"/pedido/{codigo}/pix/confirmar", data={"_csrf": csrf}, follow_redirects=True)
    html = r.get_data(as_text=True)
    assert "Pagamento PIX confirmado" in html and "Pedido recebido" in html
    # confirmar de novo é idempotente (não quebra nem duplica histórico)
    client.post(f"/pedido/{codigo}/pix/confirmar", data={"_csrf": csrf})
    with app.app_context():
        from app.db import get_db
        n = get_db().execute("SELECT COUNT(*) FROM historico_status h JOIN pedido p ON p.id=h.pedido_id "
                             "WHERE p.codigo=? AND h.status='RECEBIDO'", (codigo,)).fetchone()[0]
        assert n == 1


def test_uc04_pix_expira_em_15_min_e_cancela(client, csrf, app):
    encher_carrinho_e_frete(client, csrf)
    codigo = _codigo_da_url(client.post("/checkout/", data={**DADOS_CLIENTE, "_csrf": csrf, "metodo": "PIX"}))
    with app.app_context():
        from app.db import get_db
        passado = (datetime.now(timezone.utc) - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        get_db().execute("UPDATE pagamento SET expira_em = ?", (passado,))
        get_db().commit()
    html = client.get(f"/pedido/{codigo}", follow_redirects=True).get_data(as_text=True)
    assert "Pedido cancelado" in html and "15 minutos" in html
    r = client.post(f"/pedido/{codigo}/pix/confirmar", data={"_csrf": csrf}, follow_redirects=True)
    assert "não está mais pendente" in r.get_data(as_text=True)


def test_us09_acompanhar_por_codigo(client, csrf):
    encher_carrinho_e_frete(client, csrf)
    codigo = _codigo_da_url(client.post("/checkout/", data={**DADOS_CLIENTE, "_csrf": csrf, "metodo": "CARTAO",
                                        "numero_cartao": "4111111111111111", "nome_cartao": "MARIA", "validade": "12/35", "cvv": "123"}))
    novo = client.application.test_client()  # outro aparelho, sem sessão
    r = novo.get(f"/pedidos?codigo={codigo.lower()}")
    assert r.status_code == 302 and codigo in r.headers["Location"]
    assert "Não encontramos" in novo.get("/pedidos?codigo=ZZZZZZZZ").get_data(as_text=True)


# ------------------------------------------------------------- painel (US10)
def _login(client, csrf, senha="cupcake123"):
    return client.post("/admin/login", data={"_csrf": csrf, "usuario": "admin", "senha": senha})


def test_us10_painel_exige_login(client):
    r = client.get("/admin/")
    assert r.status_code == 302 and "/admin/login" in r.headers["Location"]


def test_us10_login_senha_errada(client, csrf):
    r = _login(client, csrf, senha="errada")
    assert r.status_code == 401 and "incorretos" in r.get_data(as_text=True)


def test_us10_bloqueio_apos_5_tentativas(client, csrf):
    from app.controllers import admin as admin_ctrl
    admin_ctrl._TENTATIVAS.clear()
    for _ in range(5):
        _login(client, csrf, senha="errada")
    assert _login(client, csrf).status_code == 429
    admin_ctrl._TENTATIVAS.clear()


def test_us10_lojista_avanca_status_ate_entregue(client, csrf):
    encher_carrinho_e_frete(client, csrf)
    client.post("/carrinho/embalagem", data={"_csrf": csrf, "embalagem_presente": "1", "mensagem_presente": "Te amo"})
    codigo = _codigo_da_url(client.post("/checkout/", data={**DADOS_CLIENTE, "_csrf": csrf, "metodo": "CARTAO",
                                        "numero_cartao": "4111111111111111", "nome_cartao": "MARIA", "validade": "12/35", "cvv": "123"}))
    assert _login(client, csrf).status_code == 302
    csrf = pegar_csrf(client)  # o login renova a sessão
    html = client.get("/admin/").get_data(as_text=True)
    assert codigo in html and "PRESENTE" in html and "Te amo" in html and "Av. Sete de Setembro" in html
    for atual, esperado in [("RECEBIDO", "Em preparo"), ("EM_PREPARO", "Saiu para entrega"), ("SAIU_PARA_ENTREGA", "Entregue")]:
        r = client.post(f"/admin/pedido/{codigo}/avancar", data={"_csrf": csrf, "status_atual": atual}, follow_redirects=True)
        assert esperado in r.get_data(as_text=True)
    cliente_html = client.get(f"/pedido/{codigo}").get_data(as_text=True)
    assert cliente_html.count("linha-tempo__passo feito") == 4


def test_us10_concorrencia_status_desatualizado(client, csrf):
    encher_carrinho_e_frete(client, csrf)
    codigo = _codigo_da_url(client.post("/checkout/", data={**DADOS_CLIENTE, "_csrf": csrf, "metodo": "CARTAO",
                                        "numero_cartao": "4111111111111111", "nome_cartao": "MARIA", "validade": "12/35", "cvv": "123"}))
    _login(client, csrf)
    csrf = pegar_csrf(client)
    client.post(f"/admin/pedido/{codigo}/cancelar", data={"_csrf": csrf})
    r = client.post(f"/admin/pedido/{codigo}/avancar", data={"_csrf": csrf, "status_atual": "RECEBIDO"}, follow_redirects=True)
    assert "Não é possível passar" in r.get_data(as_text=True)


def test_us10_api_resumo_para_alerta(client, csrf):
    _login(client, csrf)
    assert client.get("/admin/api/resumo").get_json() == {"total_pagos": 0}


# ------------------------------------------------------------- segurança e robustez
def test_post_sem_csrf_e_rejeitado(client):
    r = client.post("/carrinho/adicionar/1", data={"quantidade": 1})
    assert r.status_code == 400 and "formulário inválido" in r.get_data(as_text=True)


def test_cabecalhos_de_seguranca(client):
    h = client.get("/").headers
    assert h["X-Frame-Options"] == "DENY" and "default-src 'self'" in h["Content-Security-Policy"]


def test_xss_na_busca_e_escapado(client):
    html = client.get("/?q=<script>alert(1)</script>").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in html and "&lt;script&gt;" in html


def test_sql_injection_na_busca_nao_quebra(client):
    assert client.get("/?q=' OR 1=1 --").status_code == 200


def test_preco_vem_do_banco_e_nao_do_navegador(client, csrf, app):
    with client.session_transaction() as s:
        s["carrinho"] = {"1": 1}
        s["preco_falso"] = 1
    client.post("/carrinho/frete", data={"_csrf": csrf, "cep": "76801000"})
    assert "R$ 17,50" in client.get("/carrinho/").get_data(as_text=True)  # 12,50 + 5,00


# ------------------------------------------------------------- banco de dados (restrições do projeto físico)
def test_banco_rejeita_total_inconsistente(app):
    with app.app_context():
        from app.db import get_db
        db = get_db()
        db.execute("INSERT INTO cliente (nome, telefone, email) VALUES ('Teste', '69999999999', 't@t.com')")
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("""INSERT INTO pedido (codigo, cliente_id, zona_entrega_id, cep, logradouro, numero, bairro,
                          subtotal_centavos, frete_centavos, total_centavos)
                          VALUES ('ABCDEFGH', 1, 1, 76801000, 'Rua X', '1', 'Centro', 1000, 500, 9999)""")


def test_banco_rejeita_status_invalido_e_fk(app):
    with app.app_context():
        from app.db import get_db
        db = get_db()
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("INSERT INTO cupcake (categoria_id, nome, descricao, ingredientes, preco_centavos) "
                       "VALUES (999, 'X Teste', 'd', 'i', 1000)")
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("INSERT INTO cupcake (categoria_id, nome, descricao, ingredientes, preco_centavos) "
                       "VALUES (1, 'Preço zero', 'd', 'i', 0)")
