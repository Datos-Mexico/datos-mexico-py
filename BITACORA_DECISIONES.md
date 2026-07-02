# BITÁCORA DE DECISIONES — Motor de microsimulación (Sección 6)

> Walking skeleton, primera iteración (2026-07-01). Todo supuesto marcado
> `# ⚠️ SUPUESTO PROVISIONAL` en el código se acumula aquí, con el
> responsable de validarlo. Convención del brief §3.2.

## Arquitectura y unidades

| # | Decisión / supuesto | Dónde vive | Valida |
|---|--------------------|------------|--------|
| 1 | **Paso anual** (no trimestral). Semanas de cotización ≈ años formales × 52. Migrar a trimestral solo si el calendario lo permite. | `config.yaml`, `motor.py` | Esponda |
| 2 | **Todos los montos en pesos reales de 2025.** La UMA está indexada a INPC por ley ⇒ UMA real constante es exacta post-2016 y aproximación antes. | `config.yaml` | Yáñez |
| 3 | **Salarios reales de 2025 constantes en el backcast 1997–2024.** Los salarios reales fueron menores en 2000–2015 ⇒ sobreestima aportaciones históricas. Es la causa principal del sobretiro en la validación de saldo (sim/obs = 1.65). Corregir en Fase 2 con índice de salario real IMSS. | `motor.py` | Emiliano |
| 4 | **Población inicial = muestra CONAPO 2025, edades 15–64**, sin mortalidad en el backcast (la muestra condiciona a estar vivo en 2025). El stock de pensionados pre-2026 queda **excluido**: el costo FPB reportado es solo de cohortes que se retiran 2026+ (subestima el costo total de Sección 8). | `motor.py` | Fabiola / Ian |
| 5 | **Solo trabajadores tipo IMSS** (sin ISSSTE, sin independientes). La validación compara contra RCV-IMSS. | `validacion.py` | Equipo |

## Los cinco bloques (versión skeleton)

| # | Decisión / supuesto | Dónde vive | Valida |
|---|--------------------|------------|--------|
| 6 | **Markov homogéneo 4 estados** {formal, informal, desempleado, fuera}; persistencias hand-coded (0.88/0.82/0.30/0.90) y masa restante repartida proporcional a las participaciones ENOE 2025T1 (formal 26.4%, informal 31.6%, desemp. 1.5%, fuera 40.5% — `client.enoe.snapshot_nacional`). **Efecto conocido:** subdispersión de la densidad de cotización ⇒ la mediana de la cohorte 2050 no alcanza las 1,000 semanas y la tasa de reemplazo p50 es 0. La heterogeneidad persistente (panel ENOE) es la Prioridad 1 de refinamiento. | `motor.py::matriz_markov` | Emiliano (Prioridad 1) |
| 7 | **Salarios:** lognormal persistente, mediana 3.5 UMA mensuales, σ_log 0.65, perfil de edad determinístico (pico ~50 años). Sin AR(1) todavía (§4.3 es Fase 2–3). | `config.yaml`, `motor.py` | Emiliano (Prioridad 2) |
| 8 | **Rendimiento real constante 4% anual.** Referencia: serie SIEFOREs del SDK (36 meses nominal 6.5–9.4%, 2019–2025). Sin glide path por edad. | `config.yaml` | Yáñez / Esponda (Prioridad 3) |
| 9 | **Mortalidad EMSSA-09 estática** (sin factores de mejora de la circular; sin Lee-Carter). Tabla parseada del DOF 2009-11-27 (ANEXO 4); sanity check: esperanza de vida al nacer H 75.5 / M 84.5. **Nota técnica:** la tabla cruza (qx mujeres > hombres) en edades 88+ — verificado contra la fuente, pero señalarlo a Yáñez. | `data/cnsf_emssa09_mortalidad.csv` | Yáñez (Prioridad 4) |
| 10 | **Reglas SAR exactas** (bloque no aproximado): vector de aportación año→tasa, tope 25 UMA, semanas 750→1000, retiro a 65, comisiones serie CONSAR observada. Salvedades abajo (11–15). | `reglas_sar.py` | Yáñez |

## Reglas SAR — salvedades por verificar contra DOF/CONSAR

| # | Decisión / supuesto | Dónde vive | Valida |
|---|--------------------|------------|--------|
| 11 | **Vector de aportación RCV promedio** (rampa lineal 6.5% 2022 → 15% 2030; 2024 ≈ 8.6%). El calendario real de la patronal de cesantía/vejez es **por banda de UMA**; falta construir la tabla por banda del DOF. | `reglas_sar.py::_TASA_RCV` | Yáñez / Andre |
| 12 | **Cuota social plana:** 8.0 pesos (reales 2025) por día cotizado si salario ≤ 4 UMA. La vigente es una tabla por banda actualizada por INPC. | `reglas_sar.py` | Andre |
| 13 | **Comisiones pre-2008:** 1.9% sobre saldo como equivalente (la estructura real era sobre flujo y opaca). 2008–2025: promedios anuales observados vía `client.consar.comisiones_serie`. Futuro: 0.55% constante. | `reglas_sar.py::_COMISIONES` | Esponda |
| 14 | **Pensión Garantizada como piso plano** de $7,750/mes (reales 2025), aproximación del promedio del tabulador post-2020 (edad × semanas × salario). El Estado paga el piso directo (en la ley, el saldo se agota primero). | `config.yaml`, `motor.py` | Fabiola / Yáñez |
| 15 | **FPB:** piso = min(salario promedio de cotización de la carrera, tope $17,532 reales 2025 = 16,777.68 de 2024 actualizado con inflación ~4.5%); elegibilidad = edad 65 + semanas cumplidas (ley 97). **Consecuencia visible:** la tasa de reemplazo de quien recibe complemento FPB es ≈ 1.0 por construcción ⇒ distribución bimodal {0, 1} en la Figura 2. No es un bug: es el diseño de la política; discutir cómo narrarlo en Sección 7. | `motor.py` | Fabiola / Yáñez |

## Anualización

| # | Decisión / supuesto | Dónde vive | Valida |
|---|--------------------|------------|--------|
| 16 | **Renta vitalicia anual anticipada**, ä_x = Σ v^k·ₖpₓ, con tasa técnica real 3% y EMSSA-09 por sexo. Pensión mensual = S/(12·ä₆₅). La convención exacta (mensual/anual, anticipada/vencida, tasa técnica, recargos) **es el punto donde un actuario mira primero**. | `reglas_sar.py::factor_anualidad` | **Yáñez (primera agenda)** |
| 17 | **Negativa de pensión** (semanas insuficientes): saldo en una exhibición, pensión 0, tasa de reemplazo 0. Sin pensión de sobrevivencia; el saldo de activos fallecidos sale del sistema (herencia no modelada) — por eso las cuentas simuladas (63M) < observadas (78M, que incluyen inactivas y de fallecidos). | `motor.py` | Yáñez |

## Otros

| # | Decisión / supuesto | Dónde vive | Valida |
|---|--------------------|------------|--------|
| 18 | **PIB:** 34.9 billones MXN (2025), crecimiento real 2% anual — solo para expresar costo FPB como % del PIB; reemplazar con la senda de Sección 8. | `motor.py` | Ian |
| 19 | **Escenarios** (§6): ±2 pp sobre la probabilidad de transitar a formal, a partir de 2026. Intervalos con 5 semillas por escenario. | `config.yaml`, `run_skeleton.py` | Equipo |
| 20 | **Cohorte 2050 de la Figura 2** = retiros 2048–2052 (ventana ±2 años) para tener n≈420 con 5,000 agentes; se etiqueta explícito en la figura. Escalar a 50–100k agentes cuando el motor valide (§10). | `figuras.py` | Equipo |

## Estado de la validación 2025 (corrida 2026-07-01, vía API en vivo)

| Métrica | Simulado | Observado (CONSAR) | sim/obs |
|---|---|---|---|
| Saldo RCV-IMSS | 11.3 billones | 6.9 billones | **1.65** |
| Cotizantes | 27.9 M | 29.1 M | 0.96 |
| Cuentas con saldo | 63.2 M | 77.8 M | 0.81 |

Diagnóstico del 1.65: supuestos 3 (salario real constante hacia atrás),
8 (r histórico 4%) y 13 (comisiones pre-2008). Plan de calibración en
`ASKS_JUNTA.md`.
