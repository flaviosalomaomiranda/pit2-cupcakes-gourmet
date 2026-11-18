"""TESTE DE SISTEMA (ponta a ponta) em navegador real (Chromium headless via Playwright).

Simula um cliente no celular e o lojista no computador, verificando o JavaScript da interface
(máscaras, contador do carrinho, prévia de frete, contagem do PIX) e salvando capturas de tela
em docs/img/telas/ — usadas na documentação de IHC e no manual.

Executar:  pip install playwright && python -m playwright install chromium
           python -m pytest tests_e2e -v
"""
import socket
import threading
from pathlib import Path

import pytest

playwright = pytest.importorskip("playwright.sync_api")

from playwright.sync_api import expect  # noqa: E402
from werkzeug.serving import make_server  # noqa: E402

from app import create_app  # noqa: E402
from app.config import TestConfig  # noqa: E402

TELAS = Path(__file__).resolve().parent.parent / "docs" / "img" / "telas"
CELULAR = {"width": 390, "height": 844}
DESKTOP = {"width": 1280, "height": 860}


def _porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def servidor(tmp_path_factory):
    app = create_app(TestConfig, DATABASE=str(tmp_path_factory.mktemp("e2e") / "e2e.db"))
    porta = _porta_livre()
    srv = make_server("127.0.0.1", porta, app, threaded=True)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{porta}"
    srv.shutdown()


@pytest.fixture(scope="module")
def navegador():
    with playwright.sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


def _foto(page, nome, pagina_inteira=True):
    TELAS.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(TELAS / f"{nome}.png"), full_page=pagina_inteira)


def test_fluxo_cliente_celular_pix_e_lojista(servidor, navegador):
    erros_js = []
    cel = navegador.new_context(viewport=CELULAR, device_scale_factor=2, is_mobile=True, has_touch=True)
    page = cel.new_page()
    page.on("pageerror", lambda e: erros_js.append(str(e)))
    # respostas 422 (validação) são esperadas; só nos interessam erros reais de script
    page.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text and erros_js.append(m.text))

    # 1. Vitrine
    page.goto(servidor + "/")
    assert page.locator(".card").count() == 11
    _foto(page, "01-vitrine-celular", pagina_inteira=False)

    # 2. Filtro regional + adicionar via JavaScript (sem recarregar)
    page.click(".filtros a:has-text(\"Regionais\")")
    page.wait_for_url("**categoria=regionais*")
    assert page.locator(".card").count() == 3
    page.locator(".card", has_text="Cupuaçu").locator("button").click()
    expect(page.locator("[data-badge]")).to_have_text("1")
    _foto(page, "02-filtro-regionais", pagina_inteira=False)

    # 3. Detalhe com ingredientes e alergênicos; quantidade com botões + e −
    page.goto(servidor + "/cupcake/10")
    page.click("[data-qtd-mais]")
    page.click("[data-qtd-mais]")
    assert page.input_value("#quantidade") == "3"
    _foto(page, "03-detalhe")
    page.click("text=Adicionar ao carrinho")
    assert page.locator("[data-badge]").inner_text() == "4"

    # 4. Carrinho: máscara do CEP, prévia do frete via API, embalagem presente
    page.goto(servidor + "/carrinho/")
    page.fill("#cep", "")
    page.type("#cep", "76810000")
    assert page.input_value("#cep") == "76810-000"
    expect(page.locator("[data-frete-resultado]")).to_contain_text("Zona Sul")
    page.click("text=Calcular")
    page.check("[data-toggle-mensagem]")
    page.fill("#mensagem_presente", "Feliz aniversário, mãe!")
    page.click("text=Salvar opção de embalagem")
    assert "Embalagem presente" in page.inner_text(".totais")
    _foto(page, "04-carrinho")

    # 5. Checkout com validação: e-mail errado mostra erro no campo
    page.click("text=Ir para pagamento")
    page.fill("#nome", "Maria da Silva")
    page.type("#telefone", "69999990000")
    assert page.input_value("#telefone") == "(69) 99999-0000"
    page.fill("#email", "maria-sem-arroba")
    page.fill("#logradouro", "Av. Sete de Setembro")
    page.fill("#numero", "123")
    page.fill("#bairro", "Centro")
    page.click("[data-enviar]")
    assert "E-mail inválido" in page.inner_text(".avisos")
    assert page.get_attribute("#email", "aria-invalid") == "true"
    _foto(page, "05-checkout-erro-validacao")
    page.fill("#email", "maria@exemplo.com")
    _foto(page, "06-checkout")
    page.click("[data-enviar]")

    # 6. PIX: QR Code, copia e cola, contagem regressiva
    page.wait_for_url("**/pix")
    assert page.locator(".pix__qr").is_visible()
    assert page.input_value("[data-copiar-origem]").startswith("000201")
    assert page.inner_text("[data-contagem]").startswith("1")  # 14:5x
    _foto(page, "07-pix")
    page.click("text=Simular confirmação do banco")
    page.wait_for_selector(".linha-tempo")
    codigo = page.url.rstrip("/").split("/")[-1]
    _foto(page, "08-acompanhar-recebido")

    # 7. Lojista no computador
    loja = navegador.new_context(viewport=DESKTOP)
    adm = loja.new_page()
    adm.on("pageerror", lambda e: erros_js.append(str(e)))
    adm.goto(servidor + "/admin/")
    adm.fill("#usuario", "admin")
    adm.fill("#senha", "errada")
    adm.click("button[type=submit]")
    assert "incorretos" in adm.inner_text(".avisos")
    adm.fill("#usuario", "admin")
    adm.fill("#senha", "cupcake123")
    adm.click("button[type=submit]")
    assert codigo in adm.inner_text(".pedidos")
    assert "PRESENTE" in adm.inner_text(".pedidos")
    _foto(adm, "09-painel-lojista", pagina_inteira=False)
    adm.click("text=Marcar “Em preparo”")
    adm.click("text=Marcar “Saiu para entrega”")
    _foto(adm, "10-painel-saiu-entrega", pagina_inteira=False)

    # 8. Cliente vê a atualização
    page.reload()
    assert page.locator(".linha-tempo__passo.feito").count() == 3
    _foto(page, "11-acompanhar-saiu-entrega")

    assert erros_js == [], f"Erros de JavaScript no navegador: {erros_js}"
    cel.close()
    loja.close()


def test_cartao_recusado_e_carrinho_vazio(servidor, navegador):
    ctx = navegador.new_context(viewport=DESKTOP)
    page = ctx.new_page()
    page.goto(servidor + "/carrinho/")
    assert "Seu carrinho está vazio" in page.inner_text("main")
    _foto(page, "12-carrinho-vazio", pagina_inteira=False)

    page.goto(servidor + "/")
    _foto(page, "13-vitrine-desktop", pagina_inteira=False)
    page.locator(".card", has_text="Red Velvet").locator("button").click()
    expect(page.locator("[data-badge]")).to_have_text("1")
    page.goto(servidor + "/carrinho/")
    page.fill("#cep", "76801-000")
    page.click("text=Calcular")
    page.click("text=Ir para pagamento")
    for campo, valor in {"#nome": "João Souza", "#telefone": "69988887777", "#email": "joao@exemplo.com",
                         "#logradouro": "Rua Dom Pedro II", "#numero": "50", "#bairro": "Centro"}.items():
        page.fill(campo, valor)
    page.check("input[value=CARTAO]")
    assert page.locator("[data-cartao]").is_visible()
    page.type("#numero_cartao", "4000000000000002")
    assert page.input_value("#numero_cartao") == "4000 0000 0000 0002"
    page.fill("#nome_cartao", "JOAO SOUZA")
    page.type("#validade", "1235")
    page.fill("#cvv", "123")
    page.click("[data-enviar]")
    assert "recusado" in page.inner_text(".avisos").lower()
    _foto(page, "14-cartao-recusado", pagina_inteira=False)

    # número inválido é barrado já no navegador (Luhn em JavaScript)
    page.check("input[value=CARTAO]")
    page.fill("#numero_cartao", "4111 1111 1111 1112")
    page.fill("#nome_cartao", "JOAO SOUZA")
    page.fill("#validade", "12/35")
    page.fill("#cvv", "123")
    page.click("[data-enviar]")
    assert page.inner_text(".erro-inline") == "Número do cartão inválido."

    page.goto(servidor + "/nao-existe")
    _foto(page, "15-erro-404", pagina_inteira=False)
    ctx.close()
