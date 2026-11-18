"""Gera docs/01-situacao-1-planejamento/05-dicionario-de-dados.md a partir do banco REAL.

Assim o dicionário nunca fica desatualizado em relação ao schema.sql:
    python scripts/gerar_dicionario_dados.py
"""
import re
import sqlite3
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "docs" / "01-situacao-1-planejamento" / "05-dicionario-de-dados.md"

DESCRICOES = {
    "categoria": ("Agrupamento de cupcakes usado nos filtros da vitrine (US02).", {
        "id": "Identificador da categoria.",
        "nome": "Nome exibido no filtro (ex.: Tradicionais).",
        "slug": "Identificador usado na URL (?categoria=diet); só letras minúsculas.",
    }),
    "cupcake": ("Produto do cardápio exibido na vitrine (US01, US03). Desde a v1.1 inclui bebidas.", {
        "id": "Identificador do cupcake.",
        "categoria_id": "Categoria à qual o cupcake pertence.",
        "nome": "Nome comercial do sabor.",
        "descricao": "Texto de apresentação do produto.",
        "ingredientes": "Lista de ingredientes (US03 — evitar problemas com alergias).",
        "alergenicos": "Alergênicos declarados (glúten, ovos, lactose…).",
        "preco_centavos": "Preço unitário em centavos (R$ 12,50 = 1250).",
        "cor_cobertura": "Cor hexadecimal usada na ilustração do produto.",
        "ativo": "1 = aparece na vitrine; 0 = fora do cardápio (exclusão lógica).",
        "ilustracao": "Tipo de desenho do produto: cupcake, lata ou garrafa (v1.1, bebidas).",
        "enfeite": "Enfeite desenhado no topo do cupcake (cereja, açaí, cupuaçu, coco…), para cada sabor ter imagem própria (v1.1).",
    }),
    "zona_entrega": ("Faixa de CEPs atendida, com valor e prazo do frete (US08).", {
        "id": "Identificador da zona.",
        "nome": "Nome da região (ex.: Zona Sul).",
        "cep_inicio": "Primeiro CEP da faixa (8 dígitos, sem hífen).",
        "cep_fim": "Último CEP da faixa (deve ser ≥ cep_inicio).",
        "valor_centavos": "Valor do frete em centavos.",
        "prazo_minutos": "Prazo estimado de entrega em minutos.",
    }),
    "cliente": ("Pessoa que realiza o pedido (compra como convidado no MVP).", {
        "id": "Identificador do cliente.",
        "nome": "Nome completo.",
        "telefone": "Celular/telefone só com dígitos (DDD + número).",
        "email": "E-mail em minúsculas.",
        "criado_em": "Data/hora de cadastro (UTC, ISO-8601).",
    }),
    "pedido": ("Cabeçalho do pedido, com endereço e valores congelados no momento da compra.", {
        "id": "Identificador interno.",
        "codigo": "Código público de 8 caracteres usado pelo cliente para acompanhar.",
        "cliente_id": "Cliente que fez o pedido.",
        "zona_entrega_id": "Zona de entrega usada no cálculo do frete.",
        "status": "Situação atual: AGUARDANDO_PAGAMENTO, RECEBIDO, EM_PREPARO, SAIU_PARA_ENTREGA, ENTREGUE, CANCELADO.",
        "embalagem_presente": "1 = cliente pediu caixa presente (US05).",
        "mensagem_presente": "Texto do cartão do presente (até 140 caracteres).",
        "cep": "CEP de entrega (8 dígitos).",
        "logradouro": "Rua/avenida de entrega.",
        "numero": "Número do endereço.",
        "bairro": "Bairro de entrega.",
        "complemento": "Complemento (opcional).",
        "subtotal_centavos": "Soma dos itens.",
        "embalagem_centavos": "Valor da embalagem presente (0 se não pediu).",
        "frete_centavos": "Valor do frete.",
        "total_centavos": "Total = subtotal + embalagem + frete (garantido por CHECK).",
        "criado_em": "Data/hora de criação (UTC).",
        "atualizado_em": "Data/hora da última mudança de status (UTC).",
    }),
    "item_pedido": ("Itens do pedido (associativa Pedido × Cupcake).", {
        "id": "Identificador do item.",
        "pedido_id": "Pedido ao qual o item pertence.",
        "cupcake_id": "Cupcake vendido.",
        "quantidade": "Quantidade (1 a 50 por sabor).",
        "preco_unitario_centavos": "Preço do cupcake no momento da compra (não muda se o cardápio mudar).",
        "subtotal_centavos": "quantidade × preço unitário (garantido por CHECK).",
    }),
    "pagamento": ("Pagamento do pedido (1:1). Nunca guarda o número completo do cartão (US07).", {
        "id": "Identificador do pagamento.",
        "pedido_id": "Pedido pago (único: um pagamento por pedido).",
        "metodo": "PIX ou CARTAO.",
        "status": "PENDENTE, APROVADO, RECUSADO ou EXPIRADO.",
        "codigo_pix": "Código PIX Copia e Cola (obrigatório se PIX; nulo se cartão).",
        "cartao_final": "Apenas os 4 últimos dígitos do cartão.",
        "motivo_recusa": "Mensagem devolvida pelo gateway em caso de recusa.",
        "expira_em": "Prazo de validade do PIX (15 minutos após a criação).",
        "atualizado_em": "Data/hora da última mudança (UTC).",
    }),
    "historico_status": ("Linha do tempo de cada pedido, exibida no acompanhamento (US09).", {
        "id": "Identificador do registro.",
        "pedido_id": "Pedido.",
        "status": "Status alcançado.",
        "data_hora": "Momento em que o status foi alcançado (UTC).",
    }),
    "usuario_admin": ("Usuário do painel do lojista (US10).", {
        "id": "Identificador do usuário.",
        "usuario": "Login do lojista.",
        "senha_hash": "Hash da senha (PBKDF2/scrypt do Werkzeug). A senha em texto nunca é gravada.",
    }),
}


def restricoes_da_coluna(ddl: str, coluna: str) -> str:
    linha = next((l for l in ddl.splitlines() if re.match(rf"\s+{coluna}\s", l)), "")
    partes = []
    if "PRIMARY KEY" in linha:
        partes.append("PK")
    if "REFERENCES" in linha:
        partes.append("FK → " + re.search(r"REFERENCES (\w+)", linha).group(1))
    if re.search(r"\bUNIQUE\b", linha):
        partes.append("UNIQUE")
    if "CHECK" in linha:
        partes.append("CHECK")
    m = re.search(r"DEFAULT (\([^)]*\)\)|'[^']*'|\S+)", linha)
    if m:
        partes.append(f"DEFAULT {m.group(1).rstrip(',')}")
    return ", ".join(partes) or "—"


def main():
    con = sqlite3.connect(":memory:")
    con.executescript((RAIZ / "database" / "schema.sql").read_text(encoding="utf-8"))
    linhas = ["# 5. Dicionário de dados", "",
              "> Gerado automaticamente a partir de `database/schema.sql` por `scripts/gerar_dicionario_dados.py`.",
              "> Convenções: valores monetários em **centavos** (INTEGER); datas em texto ISO-8601 UTC; "
              "booleanos como INTEGER 0/1 (padrão do SQLite).", ""]
    for tabela, (desc_tab, desc_cols) in DESCRICOES.items():
        ddl = con.execute("SELECT sql FROM sqlite_master WHERE name = ?", (tabela,)).fetchone()[0]
        cols = con.execute(f"PRAGMA table_info({tabela})").fetchall()
        faltando = {c[1] for c in cols} - set(desc_cols)
        if faltando:
            sys.exit(f"Coluna sem descrição em {tabela}: {faltando}")
        linhas += [f"## {tabela}", "", desc_tab, "",
                   "| Coluna | Tipo | Nulo? | Restrições | Descrição |", "|---|---|---|---|---|"]
        for _cid, nome, tipo, notnull, _dflt, pk in cols:
            nulo = "Não" if (notnull or pk) else "Sim"
            linhas.append(f"| `{nome}` | {tipo} | {nulo} | {restricoes_da_coluna(ddl, nome)} | {desc_cols[nome]} |")
        checks = [c.strip().rstrip(",") for c in ddl.splitlines() if c.strip().startswith(("CHECK", "UNIQUE ("))]
        if checks:
            linhas += ["", "Restrições de tabela: " + "; ".join(f"`{c}`" for c in checks)]
        idx = con.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name=? AND sql IS NOT NULL",
                          (tabela,)).fetchall()
        if idx:
            linhas += ["", "Índices: " + "; ".join(f"`{n}`" for n, _ in idx)]
        linhas.append("")
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text("\n".join(linhas), encoding="utf-8")
    print(f"Gerado: {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
