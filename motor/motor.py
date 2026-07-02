"""Núcleo del motor de microsimulación actuarial (walking skeleton, §4).

Loop de acumulación en tiempo discreto anual:

    S_{t+1} = (S_t + A_t - C_t) * (1 + r_t)

con identidad contable verificada en CADA periodo (aborta si falla):

    ΔS = A + R - C          (por agente, en el paso de acumulación)
    ΔS_total = A + R - C - salidas   (conciliación global de flujos)

Diseño skeleton (cada bloque en su versión más cruda defendible):
- Trayectorias laborales: Markov homogéneo de 4 estados, calibrado a las
  participaciones ENOE 2025T1.       ⚠️ PROVISIONAL (Prioridad 1)
- Salarios: lognormal persistente + perfil determinístico de edad.
                                     ⚠️ PROVISIONAL (Prioridad 2)
- Rendimientos: r real constante.    ⚠️ PROVISIONAL (Prioridad 3)
- Mortalidad: tabla CNSF EMSSA-09 estática.  ⚠️ PROVISIONAL (Prioridad 4)
- Reglas SAR: exactas desde el inicio (reglas_sar.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from motor import reglas_sar
from motor.reglas_sar import factor_anualidad

ESTADOS = ["formal", "informal", "desempleado", "fuera"]
FORMAL, INFORMAL, DESEMPLEADO, FUERA = 0, 1, 2, 3

# ⚠️ SUPUESTO PROVISIONAL: PIB real 2025 y crecimiento real 2% — solo para
# expresar el costo FPB como % del PIB; reemplazar con senda de Sección 8.
PIB_2025_MM = 34_900_000.0  # millones de pesos de 2025
CRECIMIENTO_PIB_REAL = 0.02


class ContabilidadError(RuntimeError):
    """La identidad ΔS = A + R - C no cuadró: hay una fuga en la tubería."""


def matriz_markov(part: dict[str, float], cfg: dict, delta_densidad_pp: float = 0.0) -> np.ndarray:
    """Matriz de transición homogénea 4x4 calibrada a participaciones ENOE.

    ⚠️ SUPUESTO PROVISIONAL: diagonal hand-coded (persistencias de config);
    masa fuera de la diagonal repartida proporcional a las participaciones
    objetivo de los demás estados. Sustituir por estimación del panel ENOE
    (Emiliano, Prioridad 1).
    """
    shares = np.array(
        [part["formal"], part["informal"], part["desempleado"], part["fuera"]]
    )
    diag = np.array(
        [
            cfg["mercado_laboral"]["persistencia_formal"],
            cfg["mercado_laboral"]["persistencia_informal"],
            cfg["mercado_laboral"]["persistencia_desempleo"],
            cfg["mercado_laboral"]["persistencia_fuera"],
        ]
    )
    M = np.zeros((4, 4))
    for i in range(4):
        M[i, i] = diag[i]
        otros = [j for j in range(4) if j != i]
        w = shares[otros] / shares[otros].sum()
        M[i, otros] = (1 - diag[i]) * w
    # Escenario: +/- delta pp de probabilidad de transitar a formal (§6)
    if delta_densidad_pp != 0.0:
        d = delta_densidad_pp / 100.0
        for i in range(4):
            objetivo = min(max(M[i, FORMAL] + d, 0.001), 0.999)
            ajuste = objetivo - M[i, FORMAL]
            otros = [j for j in range(4) if j != FORMAL]
            M[i, FORMAL] = objetivo
            M[i, otros] -= ajuste * M[i, otros] / M[i, otros].sum()
        M = np.clip(M, 0.0, 1.0)
        M /= M.sum(axis=1, keepdims=True)
    return M


def estacionaria(M: np.ndarray) -> np.ndarray:
    vals, vecs = np.linalg.eig(M.T)
    v = np.real(vecs[:, np.argmax(np.real(vals))])
    return v / v.sum()


@dataclass
class ResultadoSimulacion:
    agentes: pd.DataFrame
    anual: pd.DataFrame
    validacion: dict
    ledger: pd.DataFrame = field(default_factory=pd.DataFrame)


def _perfil_edad(edades: np.ndarray, cfg: dict) -> np.ndarray:
    g = cfg["economia"]["crecimiento_salarial_edad"]
    c = cfg["economia"]["curvatura_perfil_edad"]
    e = edades - 25.0
    return g * e - c * e**2


def simular(
    cfg: dict,
    conapo: pd.DataFrame,
    qx: dict[str, np.ndarray],
    participaciones: dict[str, float],
    escenario: str = "base",
    semilla: int | None = None,
) -> ResultadoSimulacion:
    """Corre el motor end-to-end: backcast 1997-2025 + proyección 2026-2070."""
    rng = np.random.default_rng(semilla if semilla is not None else cfg["semilla"])
    sim = cfg["simulacion"]
    n0 = sim["n_agentes"]
    anio_ini, anio_val, anio_fin = (
        sim["anio_backcast"],
        sim["anio_validacion"],
        sim["anio_fin"],
    )
    uma_mensual = cfg["economia"]["uma_diaria_2025"] * 30.4
    r_real = cfg["economia"]["rendimiento_real_anual"]
    delta_pp = cfg["escenarios"][escenario]["delta_densidad_pp"]

    M_hist = matriz_markov(participaciones, cfg, 0.0)
    M_fut = matriz_markov(participaciones, cfg, delta_pp)
    pi0 = estacionaria(M_hist)

    # ------------------------------------------------------------------
    # Población inicial: muestra de CONAPO 2025, edades 15-64.
    # ⚠️ SUPUESTO PROVISIONAL: se excluye el stock de pensionados pre-2026;
    # el costo FPB reportado es SOLO de cohortes que se retiran 2026+.
    # ------------------------------------------------------------------
    c25 = conapo[(conapo["anio"] == 2025) & conapo["edad"].between(15, 64)]
    pesos_pob = c25["poblacion"].to_numpy().astype(float)
    W = pesos_pob.sum() / n0  # personas representadas por agente
    idx = rng.choice(len(c25), size=n0, p=pesos_pob / pesos_pob.sum())
    edad_2025 = c25["edad"].to_numpy()[idx]
    sexo = np.where(c25["sexo"].to_numpy()[idx] == "H", 0, 1)

    # Entrantes 2026-2070: cohortes de 15 años según CONAPO
    entrantes = {
        a: conapo[(conapo["anio"] == a) & (conapo["edad"] == 15)]
        for a in range(2026, anio_fin + 1)
    }

    # Arrays de estado (crecen con los entrantes)
    edad = (edad_2025 - (2025 - anio_ini)).astype(float)  # edad en 1997
    n = n0
    estado = rng.choice(4, size=n, p=pi0)
    mu = rng.normal(0.0, cfg["salarios"]["sigma_log"], size=n)
    saldo = np.zeros(n)
    semanas = np.zeros(n)
    anios_formal = np.zeros(n)
    anios_activo = np.zeros(n)  # años desde la entrada (denominador densidad)
    suma_sal_formal = np.zeros(n)
    vivo = np.ones(n, dtype=bool)
    retirado = np.zeros(n, dtype=bool)
    pension = np.zeros(n)
    piso_fpb_i = np.zeros(n)
    anio_retiro = np.full(n, -1)
    requiere_pg = np.zeros(n, dtype=bool)
    requiere_fpb = np.zeros(n, dtype=bool)
    tasa_reemplazo = np.full(n, np.nan)
    saldo_final = np.full(n, np.nan)

    base_log_w = np.log(cfg["salarios"]["mediana_uma_mensual"] * uma_mensual)

    # Factores de anualidad (renta vitalicia anual anticipada, EMSSA-09)
    i_tec = cfg["economia"]["tasa_tecnica_anualidad"]
    a65 = {
        0: factor_anualidad(qx["H"], reglas_sar.EDAD_RETIRO, i_tec),
        1: factor_anualidad(qx["M"], reglas_sar.EDAD_RETIRO, i_tec),
    }

    pg_mensual = cfg["pension_garantizada"]["pg_mensual_2025"]
    tope_fpb = cfg["fpb"]["tope_mensual_2025"]
    tope_salarial = reglas_sar.TOPE_SALARIAL_UMA * uma_mensual
    cs_anual = reglas_sar.CUOTA_SOCIAL_DIARIA_2025 * 365.0
    cs_tope = reglas_sar.CUOTA_SOCIAL_TOPE_UMA * uma_mensual

    ledger_rows = []
    anual_rows = []
    validacion: dict = {}

    for anio in range(anio_ini, anio_fin + 1):
        M = M_hist if anio <= anio_val else M_fut

        # -- entrantes (proyección): agentes que cumplen 15 este año --------
        if anio > anio_val:
            ent = entrantes[anio]
            pob15 = ent["poblacion"].sum()
            n_new = round(pob15 / W)
            if n_new > 0:
                p_h = ent[ent["sexo"] == "H"]["poblacion"].sum() / pob15
                edad = np.append(edad, np.full(n_new, 15.0))
                sexo = np.append(sexo, (rng.random(n_new) > p_h).astype(int))
                estado = np.append(estado, rng.choice(4, size=n_new, p=pi0))
                mu = np.append(mu, rng.normal(0.0, cfg["salarios"]["sigma_log"], n_new))
                saldo = np.append(saldo, np.zeros(n_new))
                semanas = np.append(semanas, np.zeros(n_new))
                anios_formal = np.append(anios_formal, np.zeros(n_new))
                anios_activo = np.append(anios_activo, np.zeros(n_new))
                suma_sal_formal = np.append(suma_sal_formal, np.zeros(n_new))
                vivo = np.append(vivo, np.ones(n_new, dtype=bool))
                retirado = np.append(retirado, np.zeros(n_new, dtype=bool))
                pension = np.append(pension, np.zeros(n_new))
                piso_fpb_i = np.append(piso_fpb_i, np.zeros(n_new))
                anio_retiro = np.append(anio_retiro, np.full(n_new, -1))
                requiere_pg = np.append(requiere_pg, np.zeros(n_new, dtype=bool))
                requiere_fpb = np.append(requiere_fpb, np.zeros(n_new, dtype=bool))
                tasa_reemplazo = np.append(tasa_reemplazo, np.full(n_new, np.nan))
                saldo_final = np.append(saldo_final, np.full(n_new, np.nan))
                n += n_new

        activo = vivo & ~retirado & (edad >= 15) & (edad < reglas_sar.EDAD_RETIRO)

        # -- transición laboral (solo activos en el mercado) -----------------
        if activo.any():
            u = rng.random(n)
            cum = np.cumsum(M[estado], axis=1)
            nuevo = np.clip((u[:, None] > cum).sum(axis=1), 0, 3)
            estado = np.where(activo, nuevo, estado)

        # -- salarios (pesos reales 2025) ------------------------------------
        log_w = base_log_w + mu + _perfil_edad(edad, cfg)
        w = np.exp(log_w)
        w_cot = np.minimum(w, tope_salarial)  # tope 25 UMA

        formal = activo & (estado == FORMAL)

        # -- acumulación: S' = (S + A - C)(1 + r) ----------------------------
        tasa_a = reglas_sar.tasa_aportacion(anio)
        tasa_c = reglas_sar.tasa_comision(anio)
        A = np.where(formal, tasa_a * w_cot * 12.0, 0.0)
        A = A + np.where(formal & (w_cot <= cs_tope), cs_anual, 0.0)  # cuota social
        cuenta = vivo & ~retirado
        C = np.where(cuenta, tasa_c * saldo, 0.0)
        base = np.where(cuenta, saldo + A - C, saldo)
        R = np.where(cuenta, base * r_real, 0.0)
        saldo_nuevo = np.where(cuenta, base + R, saldo)

        # ============ CHECK CONTABLE ΔS = A + R - C (por agente) ============
        delta = saldo_nuevo[cuenta] - saldo[cuenta]
        flujo = A[cuenta] + R[cuenta] - C[cuenta]
        if not np.allclose(delta, flujo, rtol=1e-9, atol=1e-6):
            peor = np.abs(delta - flujo).max()
            raise ContabilidadError(
                f"ΔS != A + R - C en {anio} (desvío máximo {peor:.6e} pesos)"
            )
        saldo_total_pre = saldo[vivo].sum()
        saldo = saldo_nuevo

        semanas = semanas + np.where(formal, 52.0, 0.0)
        anios_formal = anios_formal + formal
        anios_activo = anios_activo + activo
        suma_sal_formal = suma_sal_formal + np.where(formal, w_cot, 0.0)

        # -- retiro a los 65 --------------------------------------------------
        cumple_edad = vivo & ~retirado & (edad >= reglas_sar.EDAD_RETIRO) & (anio > anio_val)
        salida_retiro = 0.0
        if cumple_edad.any():
            ids = np.where(cumple_edad)[0]
            sem_req = reglas_sar.semanas_requeridas(anio)
            for j in ids:
                sal_prom = (
                    suma_sal_formal[j] / anios_formal[j]
                    if anios_formal[j] > 0
                    else np.nan
                )
                if semanas[j] >= sem_req:
                    p = saldo[j] / (12.0 * a65[sexo[j]])
                    if p < pg_mensual:
                        # ⚠️ PROVISIONAL: PG como piso plano (el vigente es
                        # tabulador edad x semanas x salario) pagada por el
                        # Estado al agotarse el saldo — aquí piso directo.
                        p = pg_mensual
                        requiere_pg[j] = True
                    piso = min(sal_prom, tope_fpb) if not np.isnan(sal_prom) else 0.0
                    # ⚠️ PROVISIONAL: elegibilidad FPB = cumplir semanas y
                    # edad 65 (ley 97); piso = salario promedio de cotización
                    # con tope — confirmar reglas exactas con Fabiola/Yáñez.
                    if p < piso:
                        requiere_fpb[j] = True
                        piso_fpb_i[j] = piso
                    pension[j] = p
                    # pensión efectiva percibida = piso FPB si aplica el complemento
                    efectiva = piso if requiere_fpb[j] else p
                    tasa_reemplazo[j] = (
                        efectiva / sal_prom
                        if not np.isnan(sal_prom) and sal_prom > 0
                        else np.nan
                    )
                else:
                    # negativa de pensión: entrega del saldo en una exhibición
                    pension[j] = 0.0
                    tasa_reemplazo[j] = 0.0 if anios_formal[j] > 0 else np.nan
                saldo_final[j] = saldo[j]
                anio_retiro[j] = anio
                salida_retiro += saldo[j]
                saldo[j] = 0.0
            retirado[cumple_edad] = True

        # -- mortalidad (solo en proyección; el backcast condiciona a estar
        #    vivo en 2025 por construcción de la muestra CONAPO) -------------
        salida_muerte = 0.0
        if anio > anio_val:
            edades_i = np.clip(edad.astype(int), 0, 109)
            q = np.where(sexo == 0, qx["H"][edades_i], qx["M"][edades_i])
            muere = vivo & (rng.random(n) < q)
            # ⚠️ PROVISIONAL: el saldo de activos fallecidos sale del sistema
            # (herencia a beneficiarios); sin pensión de sobrevivencia.
            salida_muerte = saldo[muere & ~retirado].sum()
            saldo[muere & ~retirado] = 0.0
            vivo = vivo & ~muere

        # ===== CONCILIACIÓN GLOBAL: ΔS_total = A + R - C - salidas ==========
        saldo_total_post = saldo[vivo].sum()
        flujo_neto = A[cuenta].sum() + R[cuenta].sum() - C[cuenta].sum()
        delta_total = saldo_total_post - saldo_total_pre
        esperado = flujo_neto - salida_retiro - salida_muerte
        if not np.isclose(delta_total, esperado, rtol=1e-9, atol=1e-3):
            raise ContabilidadError(
                f"Conciliación global falla en {anio}: ΔS={delta_total:.2f} "
                f"vs A+R-C-salidas={esperado:.2f}"
            )

        ledger_rows.append(
            {
                "anio": anio,
                "aportaciones_mm": A[cuenta].sum() * W / 1e6,
                "rendimientos_mm": R[cuenta].sum() * W / 1e6,
                "comisiones_mm": C[cuenta].sum() * W / 1e6,
                "salidas_retiro_mm": salida_retiro * W / 1e6,
                "salidas_muerte_mm": salida_muerte * W / 1e6,
                "saldo_total_mm": saldo_total_post * W / 1e6,
                "check_contable": "OK",
            }
        )

        # -- snapshot de validación 2025 --------------------------------------
        if anio == anio_val:
            validacion = {
                "saldo_rcv_simulado_mm": saldo[vivo & ~retirado].sum() * W / 1e6,
                "cotizantes_simulados": int(formal.sum() * W),
                "cuentas_simuladas": int((vivo & (saldo > 0)).sum() * W),
                "peso_agente": W,
            }

        # -- costo FPB del año (jubilados vivos con complemento) --------------
        jub = vivo & retirado & (pension > 0)
        compl = np.where(
            jub & requiere_fpb, np.maximum(piso_fpb_i - pension, 0.0), 0.0
        )
        costo_fpb = compl.sum() * 12.0 * W
        pib_t = PIB_2025_MM * (1 + CRECIMIENTO_PIB_REAL) ** (anio - 2025) * 1e6
        anual_rows.append(
            {
                "anio": anio,
                "escenario": escenario,
                "n_jubilados": int(jub.sum() * W),
                "n_bajo_piso": int((jub & requiere_fpb).sum() * W),
                "costo_FPB_total_mm": costo_fpb / 1e6,
                "costo_como_pct_PIB": 100.0 * costo_fpb / pib_t,
            }
        )

        edad = edad + 1.0

    df_ag = pd.DataFrame(
        {
            "agente_id": np.arange(n),
            "escenario": escenario,
            "cohorte_retiro": anio_retiro,
            "genero": np.where(sexo == 0, "H", "M"),
            "densidad_cotizacion": np.divide(
                anios_formal,
                anios_activo,
                out=np.zeros(n),
                where=anios_activo > 0,
            ),
            "saldo_final": saldo_final,
            "pension_mensual": pension,
            "tasa_reemplazo": tasa_reemplazo,
            "requiere_PG": requiere_pg,
            "requiere_FPB": requiere_fpb,
            "complemento_FPB_anual": np.where(
                requiere_fpb, 12.0 * np.maximum(piso_fpb_i - pension, 0.0), 0.0
            ),
            "edad_retiro": np.where(anio_retiro > 0, reglas_sar.EDAD_RETIRO, -1),
            "semilla": semilla if semilla is not None else cfg["semilla"],
        }
    )
    return ResultadoSimulacion(
        agentes=df_ag,
        anual=pd.DataFrame(anual_rows),
        validacion=validacion,
        ledger=pd.DataFrame(ledger_rows),
    )
