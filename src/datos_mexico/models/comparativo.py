"""Modelos Pydantic para el namespace ``comparativo``.

Endpoints cross-dataset que cruzan información de Servidores Públicos
CDMX, CONSAR/SAR y ENIGH en un solo payload, con campos editoriales
pre-escritos por el equipo del observatorio (``note``, ``narrative``,
``interpretacion``, ``caveats``, ...). Los nombres de los campos
editoriales son heterogéneos entre endpoints: cada uno usa la nomenclatura
acordada por el equipo y se preservan tal cual del API.

Convenciones específicas de este módulo:

- Campos monetarios y métricas derivadas (``ratio_*``, ``pct_*``,
  ``delta_*``, ``brecha_*``) se exponen como ``Decimal`` vía
  ``BeforeValidator(_to_decimal)`` para preservar precisión aritmética.
- Campos de texto editorial (``note``, ``nota_hipotesis``, ``narrative``,
  ``interpretacion``, ``definicion_operativa``) son ``str`` requeridos
  según el spec; el SDK no los altera.
- ``caveats`` siempre es ``list[str]`` (puede estar vacía).
- Algunos endpoints exponen objetos schema-libre (``cdmx_servidor`` en
  ``decil-servidores-cdmx``, ``top_bracket``/``bottom_bracket`` en
  ``top-vs-bottom``). Se tipan como ``dict[str, Any]`` y se documenta
  que el shape evoluciona server-side.
"""

from __future__ import annotations

from typing import Any

from datos_mexico._helpers import Money
from datos_mexico.models.base import DatosMexicoModel

# ============================================================================
# Sub-modelos compartidos
# ============================================================================


class IngresoCdmxServidor(DatosMexicoModel):
    """Bloque del servidor CDMX en ``ingreso/cdmx-vs-nacional``."""

    unit: str
    n_servidores: int
    mean_sueldo_bruto_mensual: Money
    median_sueldo_bruto_mensual: Money


class IngresoEnighHogar(DatosMexicoModel):
    """Bloque de hogar ENIGH (nacional o CDMX) en ``ingreso/cdmx-vs-nacional``."""

    unit: str
    scope: str
    n_hogares_expandido: int
    mean_ing_cor_mensual: Money


class GastoRubroComparativo(DatosMexicoModel):
    """Fila por rubro en ``gastos/cdmx-vs-nacional``."""

    slug: str
    nombre: str
    mean_cdmx_mensual: Money
    mean_nacional_mensual: Money
    delta_absoluto: Money
    delta_pct: Money
    pct_del_monetario_cdmx: Money
    pct_del_monetario_nacional: Money


class DecilBound(DatosMexicoModel):
    """Frontera de decil ENIGH (lower/upper) en ``decil-servidores-cdmx``."""

    decil: int
    lower_mensual: Money
    upper_mensual: Money


class EscenarioMapeoRow(DatosMexicoModel):
    """Mapeo percentil servidor → decil hogar ENIGH bajo un escenario."""

    percentil: str
    ingreso_hogar_supuesto_mensual: Money
    decil_hogar_enigh: int | None = None


class EscenarioResponse(DatosMexicoModel):
    """Escenario de mapeo CDMX servidor → decil ENIGH hogar."""

    nombre: str
    supuesto: str
    ingreso_adicional_mensual: Money
    mapeo: list[EscenarioMapeoRow]


class CaveatsInterpretativos(DatosMexicoModel):
    """Texto editorial estructurado del decil servidores CDMX.

    El equipo del observatorio precomputa cuatro lecturas narrativas para
    evitar que un consumidor downstream simplifique la interpretación.
    """

    frontera_p50: str
    narrativa_correcta: str
    insight_principal: str
    implicacion_narrativa: str


class ActividadComparativa(DatosMexicoModel):
    """Bloque agro o no-agro en ``actividad-cdmx-vs-nacional``."""

    tipo: str
    hogares_expandido_nacional: int
    hogares_expandido_cdmx: int
    pct_nacional: Money
    pct_cdmx: Money
    ratio_cdmx_sobre_nacional: Money


class CdmxAportesActuales(DatosMexicoModel):
    """Bloque CDMX en ``aportes-vs-jubilaciones-actuales``."""

    unit: str
    n_servidores: int
    mean_sueldo_bruto: Money
    mean_sueldo_neto: Money
    mean_deduccion_total: Money
    pct_deduccion_sobre_bruto: Money


class EnighJubilacionesActuales(DatosMexicoModel):
    """Bloque ENIGH en ``aportes-vs-jubilaciones-actuales``."""

    unit_trim: str
    unit_mes: str
    pct_hogares_con_jubilacion: Money
    mean_jubilacion_sobre_todos_trim: Money
    mean_jubilacion_solo_jubilados_trim: Money
    mean_jubilacion_solo_jubilados_mensual: Money
    n_hogares_con_jubilacion_expandido: int


# ============================================================================
# Responses raíz (uno por endpoint del namespace)
# ============================================================================


class ComparativoIngreso(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/comparativo/ingreso/cdmx-vs-nacional``.

    Compara el sueldo medio/mediano del servidor público CDMX con el
    ingreso corriente medio del hogar nacional y del hogar CDMX (ENIGH).
    Incluye brechas absolutas y razones precomputadas.
    """

    cdmx_servidor: IngresoCdmxServidor
    enigh_hogar_nacional: IngresoEnighHogar
    enigh_hogar_cdmx: IngresoEnighHogar
    brecha_mean_servidor_vs_hogar_nacional: Money
    ratio_hogar_nacional_sobre_servidor: Money
    brecha_mean_servidor_vs_hogar_cdmx: Money
    ratio_hogar_cdmx_sobre_servidor: Money
    note: str
    caveats: list[str]


class ComparativoGastos(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/comparativo/gastos/cdmx-vs-nacional``.

    Gasto monetario medio mensual de hogares CDMX vs nacional, con
    desagregado por rubro (delta absoluto, delta %, peso del rubro
    sobre el gasto monetario).
    """

    mean_gasto_mon_mensual_nacional: Money
    mean_gasto_mon_mensual_cdmx: Money
    rubros: list[GastoRubroComparativo]
    note: str
    caveats: list[str]


class ComparativoDecilServidores(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/comparativo/decil-servidores-cdmx``.

    Posiciona los percentiles del sueldo del servidor CDMX dentro de los
    deciles de ingreso del hogar nacional ENIGH bajo varios escenarios
    (perceptor único, dos perceptores, etc.). Incluye narrativa editorial
    estructurada vía ``caveats_interpretativos``.

    El campo ``cdmx_servidor`` es schema-libre. Estructura schema-libre;
    ver https://api.datos-itam.org/docs para el shape actual del payload.
    """

    cdmx_servidor: dict[str, Any]
    enigh_deciles_mensuales: list[DecilBound]
    escenarios: list[EscenarioResponse]
    narrative: str
    caveats: list[str]
    caveats_interpretativos: CaveatsInterpretativos


class ComparativoTopVsBottom(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/comparativo/top-vs-bottom``.

    Compara el bracket alto vs el bracket bajo (servidor CDMX top
    percentiles vs hogar ENIGH decil 1/decil 10).

    Los campos ``top_bracket`` y ``bottom_bracket`` son schema-libre.
    Estructura schema-libre; ver https://api.datos-itam.org/docs para
    el shape actual del payload.
    """

    top_bracket: dict[str, Any]
    bottom_bracket: dict[str, Any]
    narrative: str
    insights: list[str]
    caveats: list[str]


class ComparativoBancarizacion(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/comparativo/bancarizacion``.

    Hogares con uso de tarjeta de débito/crédito en CDMX vs el agregado
    nacional, con porcentajes, delta en puntos porcentuales y razón.
    """

    definicion_operativa: str
    n_hogares_expandido_nacional: int
    n_hogares_expandido_cdmx: int
    hogares_con_uso_tarjeta_nacional: int
    hogares_con_uso_tarjeta_cdmx: int
    pct_nacional: Money
    pct_cdmx: Money
    delta_pp: Money
    ratio_cdmx_sobre_nacional: Money
    caveats: list[str]


class ComparativoActividad(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/comparativo/actividad-cdmx-vs-nacional``.

    Hogares con actividad agropecuaria vs no-agropecuaria, comparando
    CDMX con el agregado nacional.
    """

    agro: ActividadComparativa
    noagro: ActividadComparativa
    n_hogares_total_nacional: int
    n_hogares_total_cdmx: int
    note: str
    nota_hipotesis: str
    caveats: list[str]


class ComparativoAportesVsJubilaciones(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/comparativo/aportes-vs-jubilaciones-actuales``.

    Cruce CDMX x ENIGH (x CONSAR conceptualmente): contrasta deducciones
    actuales del servidor CDMX activo con jubilaciones actuales recibidas
    por hogares ENIGH. Incluye texto interpretativo del observatorio
    aclarando que NO es una comparación actuarial.
    """

    cdmx_aportes_actuales: CdmxAportesActuales
    enigh_jubilaciones_actuales: EnighJubilacionesActuales
    interpretacion: str
    caveats: list[str]
