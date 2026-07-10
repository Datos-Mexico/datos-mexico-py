"""Reglas SAR — parámetros duros (§4.5 del brief).

El único bloque que NO se aproxima en el skeleton: son ley, son públicas.
Cada valor cita su fuente. Los marcados PROVISIONAL requieren verificación
contra fuente primaria (DOF/CONSAR) antes del envío.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# ---------------------------------------------------------------------------
# Aportación obligatoria RCV (trabajadores IMSS, % del salario base de
# cotización). Reforma DOF 16-dic-2020, calendario gradual 2023-2030
# (Artículos Transitorios Segundo y Vigésimo LSS).
#
# ⚠️ SUPUESTO PROVISIONAL: la aportación patronal de cesantía/vejez depende
# del nivel salarial en UMAs (el ramp real es por banda); aquí se usa un
# vector promedio año→tasa total, anclado en 6.5% (pre-2023) y 15% (2030),
# consistente con ~8.5% total en 2024 (brief §4.5) — verificar el desglose
# por banda contra DOF con la Dra. Yáñez / CONSAR.
# ---------------------------------------------------------------------------
_TASA_RCV = {a: 0.065 for a in range(1997, 2023)}
for _i, _a in enumerate(range(2023, 2031)):
    _TASA_RCV[_a] = 0.065 + (0.15 - 0.065) * (_i + 1) / 8  # 2023: 7.56% ... 2030: 15%


def tasa_aportacion(anio: int) -> float:
    """Tasa total de aportación RCV (patrón + trabajador + Estado) del año."""
    if anio < 1997:
        raise ValueError("El SAR (ley 97) inicia en 1997")
    return _TASA_RCV.get(anio, 0.15)  # 15% de 2030 en adelante


# ---------------------------------------------------------------------------
# Cuota social (aportación adicional del Estado): aplica hasta 4 UMA de
# salario (reforma 2020 la re-focalizó en salarios bajos).
# ⚠️ SUPUESTO PROVISIONAL: monto diario plano en pesos reales de 2025
# (el vigente es una tabla por banda salarial actualizada por INPC) —
# verificar tabla vigente en DOF.
# ---------------------------------------------------------------------------
CUOTA_SOCIAL_DIARIA_2025 = 8.0   # pesos reales 2025 por día cotizado
CUOTA_SOCIAL_TOPE_UMA = 4.0      # aplica si salario <= 4 UMA

# ---------------------------------------------------------------------------
# Tope salarial de cotización: 25 UMA (Art. 28 LSS).
# ---------------------------------------------------------------------------
TOPE_SALARIAL_UMA = 25.0

# ---------------------------------------------------------------------------
# Comisiones sobre saldo (% anual). Serie observada CONSAR 2008-2025
# (promedios anuales de client.consar.comisiones_serie, consultado
# 2026-07-01). Post-2020 el tope está ligado a promedios internacionales.
# ⚠️ SUPUESTO PROVISIONAL: 1997-2007 la estructura de comisiones era sobre
# flujo y opaca; se usa 1.9% sobre saldo como equivalente — revisar.
# Futuro: 0.55% constante (tope regulatorio vigente) — PROVISIONAL.
# ---------------------------------------------------------------------------
_COMISIONES = {
    2008: 0.0199, 2009: 0.01745, 2010: 0.01578, 2011: 0.01476,
    2012: 0.01365, 2013: 0.01269, 2014: 0.01182, 2015: 0.01105,
    2016: 0.01056, 2017: 0.01028, 2018: 0.01014, 2019: 0.00983,
    2020: 0.00922, 2021: 0.00808, 2022: 0.00566, 2023: 0.00566,
    2024: 0.00566, 2025: 0.00547,
}


def tasa_comision(anio: int) -> float:
    """Comisión anual sobre saldo administrado del año."""
    if anio < 2008:
        return 0.019  # ⚠️ SUPUESTO PROVISIONAL (ver arriba)
    return _COMISIONES.get(anio, 0.0055)


# ---------------------------------------------------------------------------
# Semanas de cotización requeridas: reforma 2020 las bajó a 750 (2021) con
# aumento gradual de 25/año hasta 1000 en 2031 (Art. Cuarto Transitorio).
# ---------------------------------------------------------------------------
def semanas_requeridas(anio: int) -> int:
    if anio <= 2020:
        return 1250
    return min(750 + 25 * (anio - 2021), 1000)


# ---------------------------------------------------------------------------
# Edad de retiro: 65 años (vejez, Art. 162 LSS). 60 con cesantía — el
# skeleton usa 65 uniforme. ⚠️ SUPUESTO PROVISIONAL: sin retiro anticipado.
# ---------------------------------------------------------------------------
EDAD_RETIRO = 65


def vector_tasas_aportacion() -> dict[int, float]:
    """Vector año→tasa explícito (para citarlo en el paper, brief §4.5)."""
    return {a: round(tasa_aportacion(a), 5) for a in range(1997, 2036)}


# ---------------------------------------------------------------------------
# Tope del complemento FPB.
#
# Mecánica legal: el tope equivale al salario mensual promedio de cotización
# registrado en el IMSS el año previo ("salario mensual promedio registrado
# en el año 2023 en el IMSS actualizado", Decreto FPB, DOF 01/05/2024).
# NO se indexa a INPC: de 16,777.68 (2024) a 17,364.00 (2026, CONSAR) el
# crecimiento implícito es ~1.7% anual, muy por debajo de la inflación
# observada 2024-2025 (~4-5%).
#
# ⚠️ SUPUESTO PROVISIONAL (bitácora #22): tope_t = salario medio IMSS_{t-1}.
# - Tramo observado 2024-2026: interpolación geométrica entre las dos anclas
#   oficiales (la serie de salario medio IMSS no está en el SDK — ver
#   ASKS_JUNTA.md). El valor 2025 implícito queda PENDIENTE DE VALIDACIÓN.
# - Proyección 2027+: crece con el MISMO crecimiento salarial real secular
#   de los agentes del motor (coherencia piso/salarios; 0 en el skeleton).
# ---------------------------------------------------------------------------
def tope_fpb_mensual(
    anio: int,
    tope_2024: float,
    tope_2026: float,
    crecimiento_salarial_real: float = 0.0,
) -> float:
    """Tope mensual del complemento FPB para el año dado.

    Args:
        anio: año calendario (el FPB existe desde 2024).
        tope_2024: ancla de ley (DOF 01/05/2024): 16,777.68.
        tope_2026: valor oficial CONSAR vigente: 17,364.00.
        crecimiento_salarial_real: crecimiento salarial real secular del
            motor (config ``economia.crecimiento_salarial_secular_real``).
    """
    factor_obs = (tope_2026 / tope_2024) ** 0.5  # ~1.0173 anual entre anclas
    if anio <= 2024:
        return tope_2024
    if anio <= 2026:
        return tope_2024 * factor_obs ** (anio - 2024)
    return tope_2026 * (1.0 + crecimiento_salarial_real) ** (anio - 2026)


# ---------------------------------------------------------------------------
# Política SAR con overrides opcionales (Sección 9: evaluación de reformas).
#
# Los defaults son SIEMPRE los valores DOF/CONSAR vigentes definidos arriba
# (con su cita). Una reforma declara solo lo que cambia y desde qué año entra
# en vigor; antes de `desde` aplican los valores vigentes sin excepción, de
# modo que el backcast 1997-2025 y la validación son idénticos con o sin
# reforma.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class PoliticaSAR:
    """Parámetros de ley del SAR, con overrides opcionales para reformas.

    ``PoliticaSAR()`` sin argumentos == ley vigente (equivalencia verificada
    contra las funciones de módulo con la misma semilla).
    """

    desde: int = 2026                              # año de entrada en vigor
    tasa_aportacion_total: float | None = None     # % plano del SBC
    semanas_requeridas_fijas: int | None = None    # p. ej. 1250
    edad_retiro: int | None = None                 # p. ej. 67
    cuota_social_diaria: float | None = None       # pesos reales 2025/día
    cuota_social_tope_uma: float | None = None     # banda de elegibilidad
    tope_salarial_uma: float | None = None         # tope de cotización
    comision_pct: float | None = None              # % anual sobre saldo

    def tasa_aportacion(self, anio: int) -> float:
        if self.tasa_aportacion_total is not None and anio >= self.desde:
            return self.tasa_aportacion_total
        return tasa_aportacion(anio)

    def tasa_comision(self, anio: int) -> float:
        if self.comision_pct is not None and anio >= self.desde:
            return self.comision_pct
        return tasa_comision(anio)

    def semanas_requeridas(self, anio: int) -> int:
        if self.semanas_requeridas_fijas is not None and anio >= self.desde:
            return self.semanas_requeridas_fijas
        return semanas_requeridas(anio)

    def edad_retiro_en(self, anio: int) -> int:
        if self.edad_retiro is not None and anio >= self.desde:
            return self.edad_retiro
        return EDAD_RETIRO

    def cuota_social_diaria_en(self, anio: int) -> float:
        if self.cuota_social_diaria is not None and anio >= self.desde:
            return self.cuota_social_diaria
        return CUOTA_SOCIAL_DIARIA_2025

    def cuota_social_tope_uma_en(self, anio: int) -> float:
        if self.cuota_social_tope_uma is not None and anio >= self.desde:
            return self.cuota_social_tope_uma
        return CUOTA_SOCIAL_TOPE_UMA

    def tope_salarial_uma_en(self, anio: int) -> float:
        if self.tope_salarial_uma is not None and anio >= self.desde:
            return self.tope_salarial_uma
        return TOPE_SALARIAL_UMA

    @classmethod
    def desde_config(cls, reforma: dict | None) -> PoliticaSAR:
        """Construye la política desde una entrada de ``reformas:`` en config.

        ``None`` o dict vacío devuelve la ley vigente.
        """
        if not reforma:
            return cls()
        overrides = reforma.get("overrides", {})
        return cls(desde=reforma.get("desde", 2026), **overrides)


def factor_anualidad(qx: np.ndarray, edad: int, tasa_tecnica: float) -> float:
    """Valor presente actuarial de una renta vitalicia anual anticipada.

    ä_x = Σ_{k>=0} v^k · k_p_x, con v = 1/(1+i) y supervivencia de la tabla
    EMSSA-09 (qx indexado por edad 0..109).

    ⚠️ SUPUESTO PROVISIONAL: convención anual anticipada, tasa técnica real
    constante — la convención exacta (mensual/anual, anticipada/vencida,
    tasa técnica) debe cerrarse con la Dra. Yáñez (brief §4.6).
    """
    v = 1.0 / (1.0 + tasa_tecnica)
    kpx = 1.0
    a = 0.0
    for k in range(0, len(qx) - edad):
        a += (v**k) * kpx
        kpx *= 1.0 - qx[edad + k]
        if kpx <= 0:
            break
    return a
