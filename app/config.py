"""Configuração da aplicação, lida de variáveis de ambiente com padrões seguros para desenvolvimento."""
import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    # Em produção defina SECRET_KEY no ambiente. Sem ela, gera uma chave aleatória por execução
    # (as sessões são perdidas ao reiniciar, mas nunca usamos uma chave fixa e conhecida).
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DATABASE = os.environ.get("CUPCAKES_DB", str(BASE_DIR / "instance" / "cupcakes.db"))
    ADMIN_USUARIO = os.environ.get("ADMIN_USUARIO", "admin")
    ADMIN_SENHA = os.environ.get("ADMIN_SENHA", "cupcake123")

    VALOR_EMBALAGEM_PRESENTE_CENTAVOS = 500
    PIX_VALIDADE_MINUTOS = 15
    QTD_MAX_POR_ITEM = 50
    PIX_CHAVE_LOJA = "pix@docenuvem.com.br"

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    TESTING = False


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "chave-de-teste"
