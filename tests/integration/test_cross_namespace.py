"""End-to-end flows that exercise multiple namespaces in one session.

Covers:

- Full observatory overview: cdmx + consar + enigh + comparativo all in
  the same session, verifying each returns valid data without affecting
  the others.
- Namespace isolation: the namespace objects expose distinct method
  surfaces and do not share state beyond the shared HttpClient.
- Chained calls consistency: an id obtained from a list endpoint can be
  used to drive a follow-up detail/filter call.
"""

from __future__ import annotations

import pytest

from datos_mexico import DatosMexico

pytestmark = pytest.mark.integration


def test_full_observatory_overview(client: DatosMexico) -> None:
    """A single session calls one signature method per dataset.

    This is the smoke test of "the SDK works end-to-end for the four
    canonical datasets". If any one of these breaks we want to know.
    """
    cdmx = client.cdmx.dashboard_stats()
    consar = client.consar.recursos_totales()
    enigh = client.enigh.hogares_summary()
    ing = client.comparativo.ingreso_cdmx_vs_nacional()

    assert cdmx.total_servidores > 100_000
    assert consar.n_puntos > 100
    assert enigh.n_hogares_expandido > 30_000_000
    assert ing.ratio_hogar_nacional_sobre_servidor > 0


def test_namespace_isolation(client: DatosMexico) -> None:
    """Each namespace object is a distinct instance bound to the same
    HttpClient. Mutating one's attributes (we don't, but we check) cannot
    leak into another.
    """
    namespaces = [
        client.cdmx,
        client.consar,
        client.enigh,
        client.comparativo,
        client.personas,
        client.nombramientos,
        client.demo,
        client.export,
    ]
    # Each namespace is a unique object …
    assert len({id(ns) for ns in namespaces}) == len(namespaces)
    # … but they all share the same underlying HttpClient.
    http_clients = {id(ns._http) for ns in namespaces}
    assert len(http_clients) == 1


def test_chained_calls_sectores_to_servidores(client: DatosMexico) -> None:
    """An id from ``sectores()`` drives ``sector_stats()`` and
    ``servidores_lista(sector_id=...)``. Verifies referential integrity.
    """
    sectores = client.cdmx.sectores()
    real_sectores = [s for s in sectores if s.total_servidores > 0]
    assert real_sectores, "expected at least one sector with personnel"
    target = real_sectores[0]

    stats = client.cdmx.sector_stats(target.id)
    assert stats.id == target.id
    assert stats.total_servidores == target.total_servidores

    page = client.cdmx.servidores_lista(sector_id=target.id, per_page=5)
    assert len(page.data) > 0
    # Every returned servidor must belong to the target sector.
    assert all(s.sector == target.nombre for s in page.data)


def test_chained_calls_persona_to_nombramientos(client: DatosMexico) -> None:
    """Picking a persona from the listing must yield a valid
    nombramientos filter result.
    """
    page = client.personas.list(per_page=1)
    assert page.data, "personas listing returned empty page"
    persona = page.data[0]

    detail = client.personas.get(persona.id)
    assert detail.id == persona.id

    nombramientos = client.nombramientos.list(persona_id=persona.id, per_page=10)
    assert all(n.persona_id == persona.id for n in nombramientos.data)
