"""Namespace ``comparativo``: endpoints cross-dataset CDMX x CONSAR x ENIGH."""

from __future__ import annotations

from datos_mexico._namespace import BaseNamespace
from datos_mexico.models.comparativo import (
    ComparativoActividad,
    ComparativoAportesVsJubilaciones,
    ComparativoBancarizacion,
    ComparativoDecilServidores,
    ComparativoGastos,
    ComparativoIngreso,
    ComparativoTopVsBottom,
)


class ComparativoNamespace(BaseNamespace):
    """Endpoints comparativos cross-dataset.

    Estos endpoints son el diferenciador editorial del Observatorio Datos
    México: cruzan información de los tres datasets principales (Servidores
    Públicos CDMX, CONSAR/SAR, ENIGH 2024 NS) y devuelven, además de
    métricas precomputadas, **texto editorial pre-escrito por el equipo**
    (``note``, ``narrative``, ``interpretacion``, ``caveats``,
    ``caveats_interpretativos``). Estos campos son contenido humano y el
    SDK no los altera.

    Examples:
        >>> from datos_mexico import DatosMexico
        >>> with DatosMexico() as client:
        ...     ing = client.comparativo.ingreso_cdmx_vs_nacional()
        ...     print(f"Ratio nacional/servidor: "
        ...           f"{ing.ratio_hogar_nacional_sobre_servidor}")
    """

    def ingreso_cdmx_vs_nacional(self) -> ComparativoIngreso:
        """Compara sueldo medio/mediano del servidor CDMX vs ingreso medio del hogar.

        Cruza el sueldo del servidor público de la CDMX con el ingreso
        corriente medio del hogar nacional y del hogar CDMX (ENIGH 2024 NS).
        Incluye brechas absolutas y razones (``ratio_*``) precomputadas y
        notas metodológicas del observatorio en ``note`` y ``caveats``.

        Endpoint: ``GET /api/v1/comparativo/ingreso/cdmx-vs-nacional``
        """
        return self._get_validated(
            "/api/v1/comparativo/ingreso/cdmx-vs-nacional",
            ComparativoIngreso,
        )

    def gastos_cdmx_vs_nacional(self) -> ComparativoGastos:
        """Compara gasto monetario medio CDMX vs nacional, desagregado por rubro.

        Devuelve el gasto monetario medio mensual de los hogares (nacional
        y CDMX) y un array ``rubros`` con el detalle por rubro (delta
        absoluto, delta %, peso del rubro dentro del gasto monetario total).

        Endpoint: ``GET /api/v1/comparativo/gastos/cdmx-vs-nacional``
        """
        return self._get_validated(
            "/api/v1/comparativo/gastos/cdmx-vs-nacional",
            ComparativoGastos,
        )

    def decil_servidores_cdmx(self) -> ComparativoDecilServidores:
        """Posición del servidor CDMX en deciles ENIGH bajo distintos escenarios.

        Cruza percentiles de sueldo del servidor CDMX (p25/p50/p75/p90)
        con los deciles de ingreso del hogar nacional ENIGH bajo varios
        supuestos (perceptor único, dos perceptores, etc.). El payload
        incluye ``narrative`` y ``caveats_interpretativos`` con narrativa
        estructurada del observatorio para evitar simplificaciones.

        Endpoint: ``GET /api/v1/comparativo/decil-servidores-cdmx``
        """
        return self._get_validated(
            "/api/v1/comparativo/decil-servidores-cdmx",
            ComparativoDecilServidores,
        )

    def top_vs_bottom(self) -> ComparativoTopVsBottom:
        """Comparación bracket alto (top percentiles) vs bracket bajo.

        Cruza el extremo alto de la distribución de sueldos CDMX con el
        decil 10 ENIGH y el extremo bajo con el decil 1, incluyendo
        ``narrative`` e ``insights`` editoriales.

        Endpoint: ``GET /api/v1/comparativo/top-vs-bottom``
        """
        return self._get_validated(
            "/api/v1/comparativo/top-vs-bottom",
            ComparativoTopVsBottom,
        )

    def bancarizacion(self) -> ComparativoBancarizacion:
        """Hogares con uso de tarjeta débito/crédito CDMX vs nacional.

        Devuelve porcentajes y razón (CDMX/nacional) bajo la
        ``definicion_operativa`` que documenta el endpoint. Útil como
        proxy de bancarización financiera.

        Endpoint: ``GET /api/v1/comparativo/bancarizacion``
        """
        return self._get_validated(
            "/api/v1/comparativo/bancarizacion",
            ComparativoBancarizacion,
        )

    def actividad_cdmx_vs_nacional(self) -> ComparativoActividad:
        """Hogares con actividad agropecuaria/no-agropecuaria CDMX vs nacional.

        Compara el porcentaje y conteo expandido de hogares con actividad
        agropecuaria vs no-agropecuaria entre CDMX y nacional. Incluye
        ``note`` y ``nota_hipotesis`` editoriales.

        Endpoint: ``GET /api/v1/comparativo/actividad-cdmx-vs-nacional``
        """
        return self._get_validated(
            "/api/v1/comparativo/actividad-cdmx-vs-nacional",
            ComparativoActividad,
        )

    def aportes_vs_jubilaciones_actuales(
        self,
    ) -> ComparativoAportesVsJubilaciones:
        """Aportes (deducciones) actuales del servidor CDMX vs jubilaciones ENIGH.

        Endpoint cross-dataset que contrasta deducciones del servidor CDMX
        activo con jubilaciones actualmente recibidas por hogares ENIGH.
        El campo ``interpretacion`` aclara que **no** es una comparación
        actuarial: son dos realidades coexistentes del sistema de pensiones,
        no una proyección.

        Endpoint: ``GET /api/v1/comparativo/aportes-vs-jubilaciones-actuales``
        """
        return self._get_validated(
            "/api/v1/comparativo/aportes-vs-jubilaciones-actuales",
            ComparativoAportesVsJubilaciones,
        )
