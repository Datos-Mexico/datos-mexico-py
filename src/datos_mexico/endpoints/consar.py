"""Namespace CONSAR/SAR: dataset del Sistema de Ahorro para el Retiro."""

from __future__ import annotations

from datetime import date
from typing import Any

from datos_mexico._helpers import _format_fecha
from datos_mexico._namespace import BaseNamespace
from datos_mexico.models.consar import (
    ActivoNetoAggregadoResponse,
    ActivoNetoSerieResponse,
    ActivoNetoSnapshotResponse,
    AforesResponse,
    ComisionSerieResponse,
    ComisionSnapshotResponse,
    ComposicionResponse,
    CuentaSerieResponse,
    CuentaSistemaResponse,
    CuentaSnapshotResponse,
    FlujoSerieResponse,
    FlujoSnapshotResponse,
    ImssVsIsssteeResponse,
    MedidaSerieResponse,
    MedidaSnapshotResponse,
    MetricasCuentaResponse,
    MetricasSensibilidadResponse,
    PeaCotizantesResponse,
    PorAforeResponse,
    PorComponenteResponse,
    PrecioComparativoResponse,
    PrecioSerieResponse,
    PrecioSnapshotResponse,
    RendimientoSerieResponse,
    RendimientoSistemaResponse,
    RendimientoSnapshotResponse,
    SerieResponse,
    TiposRecursoResponse,
    TotalesSarResponse,
    TraspasoSerieResponse,
    TraspasoSnapshotResponse,
)


class ConsarNamespace(BaseNamespace):
    """Endpoints del dataset CONSAR/SAR (Sistema de Ahorro para el Retiro).

    Cobertura completa de las 11 AFOREs activas, 327 puntos mensuales
    (1998-05 a 2025-06), 15 tipos de recurso y 11 SIEFOREs. Organizada en
    12 grupos lógicos:

    - **Catálogos** (4): AFOREs, tipos de recurso, métricas de cuentas y
      sensibilidad.
    - **Recursos administrados** (6): totales, snapshot por AFORE, por
      componente, composición contable, IMSS vs ISSSTE, serie filtrable.
    - **PEA cotizantes** (1): cobertura del SAR vs población económicamente
      activa.
    - **Comisiones** (2): serie filtrable y snapshot.
    - **Flujos** (2): entradas, salidas y flujo neto.
    - **Traspasos** (2): cuentas cedidas/recibidas con identidad contable.
    - **Rendimientos** (3): por AFORE, snapshot y promedio del sistema.
    - **Precios (NAV)** (3): serie, snapshot, comparativo entre AFOREs.
    - **Precios de gestión** (3): mismas tres formas con base de gestión.
    - **Cuentas** (3): número de cuentas y montos por métrica.
    - **Medidas regulatorias** (2): sensibilidad, VaR, duración, etc.
    - **Activo neto** (3): por SIEFORE, snapshot, agregado por categoría.

    Examples:
        >>> from datos_mexico import DatosMexico
        >>> with DatosMexico() as client:
        ...     totales = client.consar.recursos_totales()
        ...     print(f"Última fecha: {totales.fecha_max}")
        ...     por_afore = client.consar.recursos_por_afore(fecha="2025-06-01")
        ...     print(f"Total: ${por_afore.total_sistema_mm:,.0f} mdp")
    """

    # ------------------------------------------------------------------
    # GRUPO 1 — Catálogos
    # ------------------------------------------------------------------

    def afores(self) -> AforesResponse:
        """Catálogo de las AFOREs registradas históricamente.

        Endpoint: ``GET /api/v1/consar/afores``
        """
        return self._get_validated(
            "/api/v1/consar/afores", AforesResponse
        )

    def tipos_recurso(self) -> TiposRecursoResponse:
        """Catálogo de tipos de recurso (RCV, vivienda, voluntario, etc.).

        Endpoint: ``GET /api/v1/consar/tipos-recurso``
        """
        return self._get_validated(
            "/api/v1/consar/tipos-recurso", TiposRecursoResponse
        )

    def metricas_cuenta(self) -> MetricasCuentaResponse:
        """Catálogo de métricas de cuentas disponibles.

        Endpoint: ``GET /api/v1/consar/metricas-cuenta``
        """
        return self._get_validated(
            "/api/v1/consar/metricas-cuenta", MetricasCuentaResponse
        )

    def metricas_sensibilidad(self) -> MetricasSensibilidadResponse:
        """Catálogo de métricas de sensibilidad/regulatorias.

        Endpoint: ``GET /api/v1/consar/metricas-sensibilidad``
        """
        return self._get_validated(
            "/api/v1/consar/metricas-sensibilidad",
            MetricasSensibilidadResponse,
        )

    # ------------------------------------------------------------------
    # GRUPO 2 — Recursos administrados
    # ------------------------------------------------------------------

    def recursos_totales(self) -> TotalesSarResponse:
        """Serie histórica del SAR total en mil millones de MXN corrientes.

        Endpoint: ``GET /api/v1/consar/recursos/totales``
        """
        return self._get_validated(
            "/api/v1/consar/recursos/totales", TotalesSarResponse
        )

    def recursos_por_afore(self, fecha: date | str) -> PorAforeResponse:
        """Snapshot de recursos administrados por AFORE para una fecha.

        Endpoint: ``GET /api/v1/consar/recursos/por-afore``

        Args:
            fecha: Fecha del snapshot (día = 01).

        Raises:
            ValueError: Si ``fecha`` no es válida o el día no es 01.
            NotFoundError: Si no hay datos para esa fecha.
        """
        return self._get_validated(
            "/api/v1/consar/recursos/por-afore",
            PorAforeResponse,
            params={"fecha": _format_fecha(fecha)},
        )

    def recursos_por_componente(
        self, fecha: date | str
    ) -> PorComponenteResponse:
        """Snapshot de recursos por componente (tipo de recurso) para una fecha.

        Endpoint: ``GET /api/v1/consar/recursos/por-componente``
        """
        return self._get_validated(
            "/api/v1/consar/recursos/por-componente",
            PorComponenteResponse,
            params={"fecha": _format_fecha(fecha)},
        )

    def recursos_composicion(self, fecha: date | str) -> ComposicionResponse:
        """Composición contable: verifica que la suma cuadra al peso.

        Endpoint: ``GET /api/v1/consar/recursos/composicion``
        """
        return self._get_validated(
            "/api/v1/consar/recursos/composicion",
            ComposicionResponse,
            params={"fecha": _format_fecha(fecha)},
        )

    def recursos_imss_vs_issste(self) -> ImssVsIsssteeResponse:
        """Serie histórica del split RCV IMSS vs ISSSTE.

        Endpoint: ``GET /api/v1/consar/recursos/imss-vs-issste``
        """
        return self._get_validated(
            "/api/v1/consar/recursos/imss-vs-issste", ImssVsIsssteeResponse
        )

    def recursos_serie(
        self,
        *,
        codigo: str,
        afore_codigo: str | None = None,
        desde: date | str | None = None,
        hasta: date | str | None = None,
    ) -> SerieResponse:
        """Serie de un tipo de recurso específico, opcionalmente filtrada.

        Endpoint: ``GET /api/v1/consar/recursos/serie``

        Args:
            codigo: Código del tipo de recurso (ej. ``"rcv"``, ``"vivienda"``).
            afore_codigo: Si se especifica, filtra a una sola AFORE.
            desde: Fecha inicial del rango (día = 01).
            hasta: Fecha final del rango (día = 01).
        """
        params: dict[str, Any] = {"codigo": codigo}
        if afore_codigo is not None:
            params["afore_codigo"] = afore_codigo
        if desde is not None:
            params["desde"] = _format_fecha(desde)
        if hasta is not None:
            params["hasta"] = _format_fecha(hasta)
        return self._get_validated(
            "/api/v1/consar/recursos/serie", SerieResponse, params=params
        )

    # ------------------------------------------------------------------
    # GRUPO 3 — PEA cotizantes
    # ------------------------------------------------------------------

    def pea_cotizantes_serie(self) -> PeaCotizantesResponse:
        """Serie anual de cotizantes vs PEA: cobertura del SAR.

        Endpoint: ``GET /api/v1/consar/pea-cotizantes/serie``
        """
        return self._get_validated(
            "/api/v1/consar/pea-cotizantes/serie", PeaCotizantesResponse
        )

    # ------------------------------------------------------------------
    # GRUPO 4 — Comisiones
    # ------------------------------------------------------------------

    def comisiones_serie(
        self,
        *,
        afore_codigo: str | None = None,
        desde: date | str | None = None,
        hasta: date | str | None = None,
    ) -> ComisionSerieResponse:
        """Serie de comisiones (porcentaje cobrado mensualmente).

        Endpoint: ``GET /api/v1/consar/comisiones/serie``

        Args:
            afore_codigo: Si se especifica, filtra a una AFORE.
            desde: Fecha inicial del rango.
            hasta: Fecha final del rango.
        """
        params = self._build_optional_params(
            afore_codigo=afore_codigo, desde=desde, hasta=hasta
        )
        return self._get_validated(
            "/api/v1/consar/comisiones/serie",
            ComisionSerieResponse,
            params=params,
        )

    def comisiones_snapshot(
        self, fecha: date | str
    ) -> ComisionSnapshotResponse:
        """Snapshot de comisiones por AFORE para una fecha.

        Endpoint: ``GET /api/v1/consar/comisiones/snapshot``
        """
        return self._get_validated(
            "/api/v1/consar/comisiones/snapshot",
            ComisionSnapshotResponse,
            params={"fecha": _format_fecha(fecha)},
        )

    # ------------------------------------------------------------------
    # GRUPO 5 — Flujos
    # ------------------------------------------------------------------

    def flujos_serie(
        self,
        *,
        afore_codigo: str | None = None,
        desde: date | str | None = None,
        hasta: date | str | None = None,
    ) -> FlujoSerieResponse:
        """Serie de flujos (entradas, salidas, flujo neto).

        Endpoint: ``GET /api/v1/consar/flujos/serie``
        """
        params = self._build_optional_params(
            afore_codigo=afore_codigo, desde=desde, hasta=hasta
        )
        return self._get_validated(
            "/api/v1/consar/flujos/serie", FlujoSerieResponse, params=params
        )

    def flujos_snapshot(self, fecha: date | str) -> FlujoSnapshotResponse:
        """Snapshot de flujos por AFORE para una fecha.

        Endpoint: ``GET /api/v1/consar/flujos/snapshot``
        """
        return self._get_validated(
            "/api/v1/consar/flujos/snapshot",
            FlujoSnapshotResponse,
            params={"fecha": _format_fecha(fecha)},
        )

    # ------------------------------------------------------------------
    # GRUPO 6 — Traspasos
    # ------------------------------------------------------------------

    def traspasos_serie(
        self,
        *,
        afore_codigo: str | None = None,
        desde: date | str | None = None,
        hasta: date | str | None = None,
    ) -> TraspasoSerieResponse:
        """Serie de traspasos (cuentas cedidas/recibidas/neto).

        Endpoint: ``GET /api/v1/consar/traspasos/serie``
        """
        params = self._build_optional_params(
            afore_codigo=afore_codigo, desde=desde, hasta=hasta
        )
        return self._get_validated(
            "/api/v1/consar/traspasos/serie",
            TraspasoSerieResponse,
            params=params,
        )

    def traspasos_snapshot(
        self, fecha: date | str
    ) -> TraspasoSnapshotResponse:
        """Snapshot de traspasos con verificación de identidad.

        Endpoint: ``GET /api/v1/consar/traspasos/snapshot``
        """
        return self._get_validated(
            "/api/v1/consar/traspasos/snapshot",
            TraspasoSnapshotResponse,
            params={"fecha": _format_fecha(fecha)},
        )

    # ------------------------------------------------------------------
    # GRUPO 7 — Rendimientos
    # ------------------------------------------------------------------

    def rendimientos_serie(
        self,
        *,
        afore_codigo: str,
        siefore_slug: str,
        plazo: str,
    ) -> RendimientoSerieResponse:
        """Serie de rendimientos para un par AFORE x SIEFORE x plazo.

        Endpoint: ``GET /api/v1/consar/rendimientos/serie``

        Args:
            afore_codigo: Código de la AFORE (requerido).
            siefore_slug: Slug de la SIEFORE (requerido).
            plazo: Plazo del rendimiento (ej. ``"36meses"``).
        """
        return self._get_validated(
            "/api/v1/consar/rendimientos/serie",
            RendimientoSerieResponse,
            params={
                "afore_codigo": afore_codigo,
                "siefore_slug": siefore_slug,
                "plazo": plazo,
            },
        )

    def rendimientos_snapshot(
        self,
        *,
        fecha: date | str,
        plazo: str,
    ) -> RendimientoSnapshotResponse:
        """Snapshot de rendimientos para un plazo en una fecha (cubre todas las SIEFORES).

        Endpoint: ``GET /api/v1/consar/rendimientos/snapshot``
        """
        return self._get_validated(
            "/api/v1/consar/rendimientos/snapshot",
            RendimientoSnapshotResponse,
            params={"fecha": _format_fecha(fecha), "plazo": plazo},
        )

    def rendimientos_sistema(
        self,
        *,
        siefore_slug: str,
        plazo: str,
    ) -> RendimientoSistemaResponse:
        """Serie de rendimiento promedio del sistema para una SIEFORE.

        Endpoint: ``GET /api/v1/consar/rendimientos/sistema``
        """
        return self._get_validated(
            "/api/v1/consar/rendimientos/sistema",
            RendimientoSistemaResponse,
            params={"siefore_slug": siefore_slug, "plazo": plazo},
        )

    # ------------------------------------------------------------------
    # GRUPO 8 — Precios (NAV)
    # ------------------------------------------------------------------

    def precios_serie(
        self,
        *,
        afore_codigo: str,
        siefore_slug: str,
        desde: date | str | None = None,
        hasta: date | str | None = None,
    ) -> PrecioSerieResponse:
        """Serie de precios (NAV) para un par AFORE x SIEFORE.

        Endpoint: ``GET /api/v1/consar/precios/serie``
        """
        params: dict[str, Any] = {
            "afore_codigo": afore_codigo,
            "siefore_slug": siefore_slug,
        }
        if desde is not None:
            params["desde"] = _format_fecha(desde)
        if hasta is not None:
            params["hasta"] = _format_fecha(hasta)
        return self._get_validated(
            "/api/v1/consar/precios/serie",
            PrecioSerieResponse,
            params=params,
        )

    def precios_snapshot(self, fecha: date | str) -> PrecioSnapshotResponse:
        """Snapshot de precios para una fecha (cubre todas las SIEFORES).

        Endpoint: ``GET /api/v1/consar/precios/snapshot``
        """
        return self._get_validated(
            "/api/v1/consar/precios/snapshot",
            PrecioSnapshotResponse,
            params={"fecha": _format_fecha(fecha)},
        )

    def precios_comparativo(
        self,
        *,
        siefore_slug: str,
        desde: date | str,
        hasta: date | str,
    ) -> PrecioComparativoResponse:
        """Comparación de precios de una SIEFORE entre AFOREs en un rango.

        Endpoint: ``GET /api/v1/consar/precios/comparativo``
        """
        return self._get_validated(
            "/api/v1/consar/precios/comparativo",
            PrecioComparativoResponse,
            params={
                "siefore_slug": siefore_slug,
                "desde": _format_fecha(desde),
                "hasta": _format_fecha(hasta),
            },
        )

    # ------------------------------------------------------------------
    # GRUPO 9 — Precios de gestión
    # ------------------------------------------------------------------

    def precios_gestion_serie(
        self,
        *,
        afore_codigo: str,
        siefore_slug: str,
        desde: date | str | None = None,
        hasta: date | str | None = None,
    ) -> PrecioSerieResponse:
        """Serie de precios de gestión (con base de gestión) para AFORE x SIEFORE.

        Endpoint: ``GET /api/v1/consar/precios-gestion/serie``
        """
        params: dict[str, Any] = {
            "afore_codigo": afore_codigo,
            "siefore_slug": siefore_slug,
        }
        if desde is not None:
            params["desde"] = _format_fecha(desde)
        if hasta is not None:
            params["hasta"] = _format_fecha(hasta)
        return self._get_validated(
            "/api/v1/consar/precios-gestion/serie",
            PrecioSerieResponse,
            params=params,
        )

    def precios_gestion_snapshot(
        self, fecha: date | str
    ) -> PrecioSnapshotResponse:
        """Snapshot de precios de gestión para una fecha.

        Endpoint: ``GET /api/v1/consar/precios-gestion/snapshot``
        """
        return self._get_validated(
            "/api/v1/consar/precios-gestion/snapshot",
            PrecioSnapshotResponse,
            params={"fecha": _format_fecha(fecha)},
        )

    def precios_gestion_comparativo(
        self,
        *,
        siefore_slug: str,
        desde: date | str,
        hasta: date | str,
    ) -> PrecioComparativoResponse:
        """Comparación de precios de gestión entre AFOREs en un rango.

        Endpoint: ``GET /api/v1/consar/precios-gestion/comparativo``
        """
        return self._get_validated(
            "/api/v1/consar/precios-gestion/comparativo",
            PrecioComparativoResponse,
            params={
                "siefore_slug": siefore_slug,
                "desde": _format_fecha(desde),
                "hasta": _format_fecha(hasta),
            },
        )

    # ------------------------------------------------------------------
    # GRUPO 10 — Cuentas
    # ------------------------------------------------------------------

    def cuentas_serie(
        self,
        *,
        afore_codigo: str,
        metrica: str,
    ) -> CuentaSerieResponse:
        """Serie de una métrica de cuentas para una AFORE.

        Endpoint: ``GET /api/v1/consar/cuentas/serie``
        """
        return self._get_validated(
            "/api/v1/consar/cuentas/serie",
            CuentaSerieResponse,
            params={"afore_codigo": afore_codigo, "metrica": metrica},
        )

    def cuentas_snapshot(self, fecha: date | str) -> CuentaSnapshotResponse:
        """Snapshot de cuentas para una fecha (cubre todas las métricas).

        Endpoint: ``GET /api/v1/consar/cuentas/snapshot``
        """
        return self._get_validated(
            "/api/v1/consar/cuentas/snapshot",
            CuentaSnapshotResponse,
            params={"fecha": _format_fecha(fecha)},
        )

    def cuentas_sistema(self, *, metrica: str) -> CuentaSistemaResponse:
        """Serie del sistema completo, etiquetada por categoría.

        Endpoint: ``GET /api/v1/consar/cuentas/sistema``
        """
        return self._get_validated(
            "/api/v1/consar/cuentas/sistema",
            CuentaSistemaResponse,
            params={"metrica": metrica},
        )

    # ------------------------------------------------------------------
    # GRUPO 11 — Medidas regulatorias
    # ------------------------------------------------------------------

    def medidas_serie(
        self,
        *,
        afore_codigo: str,
        siefore_slug: str,
        metrica: str,
    ) -> MedidaSerieResponse:
        """Serie de una medida regulatoria para AFORE x SIEFORE x métrica.

        Endpoint: ``GET /api/v1/consar/medidas/serie``
        """
        return self._get_validated(
            "/api/v1/consar/medidas/serie",
            MedidaSerieResponse,
            params={
                "afore_codigo": afore_codigo,
                "siefore_slug": siefore_slug,
                "metrica": metrica,
            },
        )

    def medidas_snapshot(
        self,
        *,
        fecha: date | str,
        metrica: str,
    ) -> MedidaSnapshotResponse:
        """Snapshot de una métrica regulatoria para una fecha.

        Endpoint: ``GET /api/v1/consar/medidas/snapshot``
        """
        return self._get_validated(
            "/api/v1/consar/medidas/snapshot",
            MedidaSnapshotResponse,
            params={"fecha": _format_fecha(fecha), "metrica": metrica},
        )

    # ------------------------------------------------------------------
    # GRUPO 12 — Activo neto
    # ------------------------------------------------------------------

    def activo_neto_serie(
        self,
        *,
        afore_codigo: str,
        siefore_slug: str,
    ) -> ActivoNetoSerieResponse:
        """Serie de activo neto para un par AFORE x SIEFORE.

        Endpoint: ``GET /api/v1/consar/activo-neto/serie``
        """
        return self._get_validated(
            "/api/v1/consar/activo-neto/serie",
            ActivoNetoSerieResponse,
            params={
                "afore_codigo": afore_codigo,
                "siefore_slug": siefore_slug,
            },
        )

    def activo_neto_snapshot(
        self, fecha: date | str
    ) -> ActivoNetoSnapshotResponse:
        """Snapshot de activo neto para una fecha (todas AFOREs x SIEFORES).

        Endpoint: ``GET /api/v1/consar/activo-neto/snapshot``
        """
        return self._get_validated(
            "/api/v1/consar/activo-neto/snapshot",
            ActivoNetoSnapshotResponse,
            params={"fecha": _format_fecha(fecha)},
        )

    def activo_neto_agregado(
        self,
        *,
        afore_codigo: str,
        categoria: str,
    ) -> ActivoNetoAggregadoResponse:
        """Activo neto agregado a través de SIEFORES de una categoría para una AFORE.

        Endpoint: ``GET /api/v1/consar/activo-neto/agregado``

        Args:
            afore_codigo: Código de la AFORE.
            categoria: Categoría de SIEFORES a sumar (ej. ``"basicas"``).
        """
        return self._get_validated(
            "/api/v1/consar/activo-neto/agregado",
            ActivoNetoAggregadoResponse,
            params={"afore_codigo": afore_codigo, "categoria": categoria},
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_optional_params(
        *,
        afore_codigo: str | None = None,
        desde: date | str | None = None,
        hasta: date | str | None = None,
    ) -> dict[str, Any]:
        """Construye query params para series con filtros opcionales comunes."""
        params: dict[str, Any] = {}
        if afore_codigo is not None:
            params["afore_codigo"] = afore_codigo
        if desde is not None:
            params["desde"] = _format_fecha(desde)
        if hasta is not None:
            params["hasta"] = _format_fecha(hasta)
        return params
