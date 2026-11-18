"""Model: Zona de entrega."""
from ..db import get_db
from ..services.frete import Zona


def listar_zonas() -> list[Zona]:
    rows = get_db().execute(
        "SELECT id, nome, cep_inicio, cep_fim, valor_centavos, prazo_minutos FROM zona_entrega ORDER BY cep_inicio"
    ).fetchall()
    return [Zona(**dict(r)) for r in rows]
