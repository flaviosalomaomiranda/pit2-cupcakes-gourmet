"""Model: Pedido, ItemPedido, Pagamento, HistoricoStatus e Cliente.

A criação do pedido é TRANSACIONAL: cliente + pedido + itens + pagamento + histórico
são gravados juntos; se qualquer passo falhar, nada fica pela metade (rollback).
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from ..db import get_db
from ..services import RegraNegocioErro
from ..services.status import validar_transicao
from . import agora_iso, parse_iso

_ALFABETO_CODIGO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sem 0/O e 1/I para não confundir


def gerar_codigo() -> str:
    return "".join(secrets.choice(_ALFABETO_CODIGO) for _ in range(8))


def criar_pedido(cliente: dict, endereco: dict, cep: int, zona, linhas, totais: dict,
                 embalagem_presente: bool, mensagem_presente: str, pagamento: dict) -> str:
    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO cliente (nome, telefone, email) VALUES (?, ?, ?)",
            (cliente["nome"], cliente["telefone"], cliente["email"]),
        )
        cliente_id = cur.lastrowid

        for _ in range(5):  # colisão de código é improvável, mas tratada
            codigo = gerar_codigo()
            if not db.execute("SELECT 1 FROM pedido WHERE codigo = ?", (codigo,)).fetchone():
                break
        else:
            raise RegraNegocioErro("Não foi possível gerar o código do pedido. Tente novamente.")

        cur = db.execute(
            """INSERT INTO pedido (codigo, cliente_id, zona_entrega_id, embalagem_presente, mensagem_presente,
                                   cep, logradouro, numero, bairro, complemento,
                                   subtotal_centavos, embalagem_centavos, frete_centavos, total_centavos)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (codigo, cliente_id, zona.id, int(embalagem_presente), mensagem_presente,
             cep, endereco["logradouro"], endereco["numero"], endereco["bairro"], endereco["complemento"],
             totais["subtotal"], totais["embalagem"], totais["frete"], totais["total"]),
        )
        pedido_id = cur.lastrowid

        db.executemany(
            """INSERT INTO item_pedido (pedido_id, cupcake_id, quantidade, preco_unitario_centavos, subtotal_centavos)
               VALUES (?, ?, ?, ?, ?)""",
            [(pedido_id, l.cupcake_id, l.quantidade, l.preco_centavos, l.subtotal_centavos) for l in linhas],
        )

        db.execute(
            """INSERT INTO pagamento (pedido_id, metodo, status, codigo_pix, cartao_final, motivo_recusa, expira_em)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (pedido_id, pagamento["metodo"], pagamento["status"], pagamento.get("codigo_pix"),
             pagamento.get("cartao_final"), pagamento.get("motivo_recusa", ""), pagamento.get("expira_em")),
        )
        db.execute("INSERT INTO historico_status (pedido_id, status) VALUES (?, 'AGUARDANDO_PAGAMENTO')", (pedido_id,))
        if pagamento["status"] == "APROVADO":
            _mudar_status(db, pedido_id, "AGUARDANDO_PAGAMENTO", "RECEBIDO")
        db.commit()
        return codigo
    except Exception:
        db.rollback()
        raise


def expira_em(minutos: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutos)).strftime("%Y-%m-%dT%H:%M:%SZ")


def buscar_por_codigo(codigo: str) -> dict | None:
    db = get_db()
    row = db.execute(
        """SELECT p.*, c.nome AS cliente_nome, c.telefone AS cliente_telefone, c.email AS cliente_email,
                  z.nome AS zona_nome, z.prazo_minutos,
                  pg.metodo AS pg_metodo, pg.status AS pg_status, pg.codigo_pix, pg.cartao_final,
                  pg.motivo_recusa, pg.expira_em
           FROM pedido p
           JOIN cliente c ON c.id = p.cliente_id
           JOIN zona_entrega z ON z.id = p.zona_entrega_id
           JOIN pagamento pg ON pg.pedido_id = p.id
           WHERE p.codigo = ?""",
        ((codigo or "").strip().upper()[:8],),
    ).fetchone()
    if not row:
        return None
    pedido = dict(row)
    pedido["itens"] = [dict(r) for r in db.execute(
        """SELECT i.quantidade, i.preco_unitario_centavos, i.subtotal_centavos, cp.id AS cupcake_id, cp.nome, cp.cor_cobertura
           FROM item_pedido i JOIN cupcake cp ON cp.id = i.cupcake_id
           WHERE i.pedido_id = ? ORDER BY cp.nome""", (pedido["id"],)).fetchall()]
    pedido["historico"] = [dict(r) for r in db.execute(
        "SELECT status, data_hora FROM historico_status WHERE pedido_id = ? ORDER BY id", (pedido["id"],)).fetchall()]
    return pedido


def _mudar_status(db, pedido_id: int, atual: str, novo: str) -> None:
    validar_transicao(atual, novo)
    cur = db.execute(
        "UPDATE pedido SET status = ?, atualizado_em = ? WHERE id = ? AND status = ?",
        (novo, agora_iso(), pedido_id, atual),
    )
    if cur.rowcount != 1:  # outro usuário mudou antes (controle de concorrência otimista)
        raise RegraNegocioErro("O pedido foi alterado por outra pessoa. Atualize a página.")
    db.execute("INSERT INTO historico_status (pedido_id, status) VALUES (?, ?)", (pedido_id, novo))


def atualizar_status(codigo: str, novo: str) -> None:
    db = get_db()
    pedido = db.execute("SELECT id, status FROM pedido WHERE codigo = ?", (codigo,)).fetchone()
    if not pedido:
        raise RegraNegocioErro("Pedido não encontrado.")
    try:
        _mudar_status(db, pedido["id"], pedido["status"], novo)
        db.commit()
    except Exception:
        db.rollback()
        raise


def confirmar_pix(codigo: str) -> None:
    """Papel do webhook do gateway: confirma o PIX se ainda estiver dentro do prazo."""
    db = get_db()
    row = db.execute(
        """SELECT p.id, p.status, pg.status AS pg_status, pg.metodo, pg.expira_em
           FROM pedido p JOIN pagamento pg ON pg.pedido_id = p.id WHERE p.codigo = ?""", (codigo,)).fetchone()
    if not row:
        raise RegraNegocioErro("Pedido não encontrado.")
    if row["metodo"] != "PIX":
        raise RegraNegocioErro("Este pedido não foi pago com PIX.")
    if row["pg_status"] == "APROVADO":
        return  # idempotente: o banco pode avisar duas vezes
    if row["pg_status"] != "PENDENTE":
        raise RegraNegocioErro("Este PIX não está mais pendente.")
    try:
        db.execute("UPDATE pagamento SET status = 'APROVADO', atualizado_em = ? WHERE pedido_id = ?",
                   (agora_iso(), row["id"]))
        _mudar_status(db, row["id"], row["status"], "RECEBIDO")
        db.commit()
    except Exception:
        db.rollback()
        raise


def expirar_pix_vencidos(agora: datetime | None = None) -> int:
    """Cancela pedidos com PIX pendente além do prazo de 15 minutos. Retorna quantos expirou."""
    agora = agora or datetime.now(timezone.utc)
    db = get_db()
    pendentes = db.execute(
        """SELECT p.id, p.status, pg.expira_em FROM pedido p JOIN pagamento pg ON pg.pedido_id = p.id
           WHERE pg.metodo = 'PIX' AND pg.status = 'PENDENTE'""").fetchall()
    n = 0
    for r in pendentes:
        if r["expira_em"] and parse_iso(r["expira_em"]) < agora:
            db.execute("UPDATE pagamento SET status = 'EXPIRADO', atualizado_em = ? WHERE pedido_id = ?",
                       (agora_iso(), r["id"]))
            _mudar_status(db, r["id"], r["status"], "CANCELADO")
            n += 1
    db.commit()
    return n


def listar_para_painel(status: str | None = None) -> list[dict]:
    sql = """SELECT p.codigo, p.status, p.total_centavos, p.criado_em, p.embalagem_presente,
                    p.mensagem_presente, p.logradouro, p.numero, p.bairro, p.complemento, p.cep,
                    c.nome AS cliente_nome, c.telefone AS cliente_telefone, pg.metodo AS pg_metodo
             FROM pedido p JOIN cliente c ON c.id = p.cliente_id JOIN pagamento pg ON pg.pedido_id = p.id"""
    params = []
    if status:
        sql += " WHERE p.status = ?"
        params.append(status)
    else:
        sql += " WHERE p.status NOT IN ('ENTREGUE', 'CANCELADO', 'AGUARDANDO_PAGAMENTO')"
    sql += " ORDER BY p.criado_em DESC, p.id DESC LIMIT 200"
    db = get_db()
    pedidos = [dict(r) for r in db.execute(sql, params).fetchall()]
    for p in pedidos:
        p["itens"] = [dict(r) for r in db.execute(
            """SELECT i.quantidade, cp.nome FROM item_pedido i
               JOIN pedido pe ON pe.id = i.pedido_id JOIN cupcake cp ON cp.id = i.cupcake_id
               WHERE pe.codigo = ? ORDER BY cp.nome""", (p["codigo"],)).fetchall()]
    return pedidos


def contagem_por_status() -> dict[str, int]:
    rows = get_db().execute("SELECT status, COUNT(*) AS n FROM pedido GROUP BY status").fetchall()
    return {r["status"]: r["n"] for r in rows}


def total_pedidos_pagos() -> int:
    return get_db().execute(
        "SELECT COUNT(*) FROM pedido WHERE status NOT IN ('AGUARDANDO_PAGAMENTO','CANCELADO')").fetchone()[0]
