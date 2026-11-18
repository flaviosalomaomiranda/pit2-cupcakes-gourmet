"""Model: Cupcake e Categoria."""
from ..db import get_db


def listar_categorias() -> list[dict]:
    rows = get_db().execute("SELECT id, nome, slug FROM categoria ORDER BY id").fetchall()
    return [dict(r) for r in rows]


def listar_cupcakes(categoria_slug: str | None = None, busca: str | None = None) -> list[dict]:
    sql = (
        "SELECT c.id, c.nome, c.descricao, c.preco_centavos, c.cor_cobertura, "
        "       cat.nome AS categoria, cat.slug AS categoria_slug "
        "FROM cupcake c JOIN categoria cat ON cat.id = c.categoria_id "
        "WHERE c.ativo = 1"
    )
    params: list = []
    if categoria_slug:
        sql += " AND cat.slug = ?"
        params.append(categoria_slug)
    if busca:
        sql += " AND (c.nome LIKE ? OR c.descricao LIKE ? OR c.ingredientes LIKE ?)"
        termo = f"%{busca.strip()[:40]}%"
        params += [termo, termo, termo]
    sql += " ORDER BY cat.id, c.nome"
    return [dict(r) for r in get_db().execute(sql, params).fetchall()]


def buscar_cupcake(cupcake_id: int) -> dict | None:
    row = get_db().execute(
        "SELECT c.*, cat.nome AS categoria, cat.slug AS categoria_slug "
        "FROM cupcake c JOIN categoria cat ON cat.id = c.categoria_id "
        "WHERE c.id = ? AND c.ativo = 1",
        (cupcake_id,),
    ).fetchone()
    return dict(row) if row else None


def mapa_cupcakes_ativos(ids: list[int]) -> dict[int, dict]:
    if not ids:
        return {}
    marcadores = ",".join("?" * len(ids))
    rows = get_db().execute(
        f"SELECT id, nome, preco_centavos, cor_cobertura FROM cupcake WHERE ativo = 1 AND id IN ({marcadores})",
        ids,
    ).fetchall()
    return {r["id"]: dict(r) for r in rows}
