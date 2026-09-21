"""Namespace INEGI: capa de cubos del observatorio, tabulados explorables, Censos Económicos y
bancos de indicadores.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from urllib.parse import quote

from datos_mexico._namespace import BaseNamespace
from datos_mexico.models.inegi import (
    CatalogoCubos,
    FichaCubo,
    MiembrosCubo,
    Observaciones,
    ResultadoCubo,
    SaicDatos,
    SaicResumen,
    TabuladoCuadro,
    TabuladosCuadros,
    TabuladosFamilias,
)


class InegiNamespace(BaseNamespace):
    """Datos del INEGI publicados por api.datosmexico.org.

    - **Cubos** (``cubos``, ``cubo``, ``cubo_miembros``, ``cubo_datos``, ``cubo_csv``): la capa que
      consume el explorador de datosmexico.org/observatorio; cada tabla del explorador tiene la
      consulta equivalente aquí.
    - **Tabulados explorables** (``tabulados``, ``tabulados_cuadros``, ``tabulado``,
    ``tabulado_celdas``):
      los cuadros publicados en Excel (censos de población 2005-2020, cuentas por sectores
      institucionales), celda por celda, tal cual.
    - **Censos Económicos 2004-2024** (``saic``, ``saic_datos``): por entidad, municipio, actividad
      del SCIAN y estrato de personal ocupado.
    - **Bancos de indicadores** (``indicador_observaciones``, ``bie_observaciones``).

    Examples:
        >>> from datos_mexico import DatosMexico
        >>> with DatosMexico() as client:
        ...     r = client.inegi.cubo_datos("saic-censos", medidas=["ue"], columnas=["entidad"],
        ...                                 filtros={"anio": ["2023"], "ambito": ["entidad"],
        ...                                          "nivel": ["0"], "estrato": ["0"]})
        ...     sum(f["ue"] for f in r.filas)
        5468180
    """

    # ----- cubos -----
    def cubos(self) -> CatalogoCubos:
        """Catálogo de cubos por tema. Endpoint: ``GET /api/v1/cubos``."""
        return self._get_validated("/api/v1/cubos", CatalogoCubos)

    def cubo(self, clave: str) -> FichaCubo:
        """Ficha de un cubo: medidas, dimensiones, filas, corte y notas. Endpoint: ``GET
        /api/v1/cubos/{cubo}``.
        """
        return self._get_validated(f"/api/v1/cubos/{quote(clave, safe='')}", FichaCubo)

    def cubo_miembros(
        self,
        clave: str,
        dimension: str,
        *,
        q: str | None = None,
        limite: int | None = None,
        filtros: dict[str, list[str]] | None = None,
    ) -> MiembrosCubo:
        """Miembros de una dimensión (con búsqueda ``q`` y filtros ``f.<dimensión>``). Endpoint:
        ``GET /api/v1/cubos/{cubo}/miembros``.
        """
        params: dict[str, Any] = {"dimension": dimension}
        if q:
            params["q"] = q
        if limite is not None:
            params["limite"] = limite
        params.update(self._filtros(filtros))
        return self._get_validated(
            f"/api/v1/cubos/{quote(clave, safe='')}/miembros", MiembrosCubo, params
        )

    def cubo_datos(
        self,
        clave: str,
        *,
        medidas: list[str],
        columnas: list[str],
        filtros: dict[str, list[str]] | None = None,
        padres: bool = False,
        orden: str | None = None,
        sentido: str | None = None,
        limite: int | None = None,
    ) -> ResultadoCubo:
        """Consulta un cubo: medidas agregadas por las columnas pedidas, con filtros ``{dimensión:
        [miembros]}``.

        Endpoint: ``GET /api/v1/cubos/{cubo}/datos``. Las dimensiones de partición (ámbito, nivel,
        estrato…) deben
        filtrarse o ir en columnas; la API responde 422 explicando qué falta.
        """
        params = self._params_datos(medidas, columnas, filtros, padres, orden, sentido, limite)
        return self._get_validated(
            f"/api/v1/cubos/{quote(clave, safe='')}/datos", ResultadoCubo, params
        )

    def cubo_csv(
        self,
        clave: str,
        *,
        medidas: list[str],
        columnas: list[str],
        filtros: dict[str, list[str]] | None = None,
        padres: bool = False,
        orden: str | None = None,
        sentido: str | None = None,
        limite: int | None = None,
    ) -> str:
        """La misma consulta que ``cubo_datos`` en CSV (con BOM, como lo descarga el explorador)."""
        params = self._params_datos(medidas, columnas, filtros, padres, orden, sentido, limite)
        params["formato"] = "csv"
        return self._http.get_text(f"/api/v1/cubos/{quote(clave, safe='')}/datos", params=params)

    @staticmethod
    def _filtros(filtros: dict[str, list[str]] | None) -> dict[str, str]:
        return {
            f"f.{dim}": "|".join(str(m) for m in miembros)
            for dim, miembros in (filtros or {}).items()
        }

    def _params_datos(
        self,
        medidas: list[str],
        columnas: list[str],
        filtros: dict[str, list[str]] | None,
        padres: bool,
        orden: str | None,
        sentido: str | None,
        limite: int | None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"medidas": ",".join(medidas), "columnas": ",".join(columnas)}
        params.update(self._filtros(filtros))
        if padres:
            params["padres"] = 1
        if orden:
            params["orden"] = orden
        if sentido:
            params["sentido"] = sentido
        if limite is not None:
            params["limite"] = limite
        return params

    # ----- tabulados explorables -----
    def tabulados(self) -> TabuladosFamilias:
        """Familias de tabulados explorables. Endpoint: ``GET /api/v1/inegi/tabulados``."""
        return self._get_validated("/api/v1/inegi/tabulados", TabuladosFamilias)

    def tabulados_cuadros(self, familia: str) -> TabuladosCuadros:
        """Cuadros de una familia con título, dimensiones de fila y columnas. Endpoint: ``GET
        /api/v1/inegi/tabulados/{familia}``.
        """
        return self._get_validated(
            f"/api/v1/inegi/tabulados/{quote(familia, safe='')}", TabuladosCuadros
        )

    def tabulado(
        self,
        familia: str,
        cuadro: str,
        *,
        d1: str | None = None,
        d2: str | None = None,
        d3: str | None = None,
        d4: str | None = None,
        d5: str | None = None,
        columna: str | None = None,
        limit: int = 500,
        offset: int = 0,
    ) -> TabuladoCuadro:
        """Un cuadro y sus celdas, filtrables por dimensión de fila (valor exacto) y columna.

        Endpoint: ``GET /api/v1/inegi/tabulados/{familia}/{cuadro}``. ``limit`` ≤ 5000; para todo el
        cuadro use ``tabulado_celdas``.
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        for k, v in (
            ("d1", d1),
            ("d2", d2),
            ("d3", d3),
            ("d4", d4),
            ("d5", d5),
            ("columna", columna),
        ):
            if v is not None:
                params[k] = v
        return self._get_validated(
            f"/api/v1/inegi/tabulados/{quote(familia, safe='')}/{quote(cuadro, safe='')}",
            TabuladoCuadro,
            params,
        )

    def tabulado_celdas(self, familia: str, cuadro: str, **filtros: str) -> Iterator[Any]:
        """Todas las celdas de un cuadro (pagina internamente de 5,000 en 5,000), en el orden
        publicado.
        """
        offset = 0
        while True:
            r = self.tabulado(familia, cuadro, limit=5000, offset=offset, **filtros)
            yield from r.items
            offset += len(r.items)
            if not r.items or offset >= r.total:
                return

    # ----- Censos Económicos -----
    def saic(self) -> SaicResumen:
        """Censos Económicos 2004-2024: años cargados, fuente y totales verificados. Endpoint:
        ``GET /api/v1/inegi/saic``.
        """
        return self._get_validated("/api/v1/inegi/saic", SaicResumen)

    def saic_datos(
        self,
        anio: str,
        nivel_act: int,
        *,
        cve_ent: str | None = None,
        cve_mun: str | None = None,
        clave_act: str | None = None,
        estrato: int | None = None,
        variables: list[str] | None = None,
        limit: int = 500,
        offset: int = 0,
    ) -> SaicDatos:
        """Filas de un censo por geografía, nivel de actividad y estrato con las variables pedidas.

        Endpoint: ``GET /api/v1/inegi/saic/datos``. ``cve_mun="todos"`` = todos los municipios de la
        entidad; para filas
        municipales solo las nueve variables principales (las 98 están en el Parquet de
        ``/api/v1/inegi/saic/descarga/{año}``).
        """
        params: dict[str, Any] = {
            "anio": anio,
            "nivel_act": nivel_act,
            "limit": limit,
            "offset": offset,
        }
        if cve_ent is not None:
            params["cve_ent"] = cve_ent
        if cve_mun is not None:
            params["cve_mun"] = cve_mun
        if clave_act is not None:
            params["clave_act"] = clave_act
        if estrato is not None:
            params["estrato"] = estrato
        if variables:
            params["variables"] = ",".join(variables)
        return self._get_validated("/api/v1/inegi/saic/datos", SaicDatos, params)

    # ----- bancos de indicadores -----
    def indicador_observaciones(
        self,
        indicador: str,
        *,
        geografia: str | None = None,
        desde: str | None = None,
        hasta: str | None = None,
        limit: int | None = None,
    ) -> Observaciones:
        """Observaciones de un indicador del Banco de Indicadores. Endpoint: ``GET
        /api/v1/inegi/indicadores/{id}/observaciones``.
        """
        params: dict[str, Any] = {}
        for k, v in (
            ("geografia", geografia),
            ("desde", desde),
            ("hasta", hasta),
            ("limit", limit),
        ):
            if v is not None:
                params[k] = v
        return self._get_validated(
            f"/api/v1/inegi/indicadores/{quote(indicador, safe='')}/observaciones",
            Observaciones,
            params,
        )

    def bie_observaciones(
        self,
        serie: str,
        *,
        area: str | None = None,
        desde: str | None = None,
        hasta: str | None = None,
    ) -> Observaciones:
        """Observaciones de una serie del Banco de Información Económica. Endpoint: ``GET
        /api/v1/bie/series/{serie}/observaciones``.
        """
        params: dict[str, Any] = {}
        for k, v in (("area", area), ("desde", desde), ("hasta", hasta)):
            if v is not None:
                params[k] = v
        return self._get_validated(
            f"/api/v1/bie/series/{quote(serie, safe='')}/observaciones", Observaciones, params
        )
