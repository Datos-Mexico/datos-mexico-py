# BITÁCORA DE DECISIONES — Motor de microsimulación (Sección 6)

> Walking skeleton, primera iteración (2026-07-01). Todo supuesto marcado
> `# ⚠️ SUPUESTO PROVISIONAL` en el código se acumula aquí, con el
> responsable de validarlo. Convención del brief §3.2.

## Arquitectura y unidades

| # | Decisión / supuesto | Dónde vive | Valida |
|---|--------------------|------------|--------|
| 1 | **Paso anual** (no trimestral). Semanas de cotización ≈ años formales × 52. Migrar a trimestral solo si el calendario lo permite. | `config.yaml`, `motor.py` | Esponda |
| 2 | **Todos los montos en pesos reales de 2025.** La UMA está indexada a INPC por ley ⇒ UMA real constante es exacta post-2016 y aproximación antes. | `config.yaml` | Yáñez |
| 3 | ~~Salarios reales de 2025 constantes en el backcast~~ **RESUELTO 2026-07-02 (ver #24):** el backcast usa la trayectoria de nivel del SBC real IMSS observado por año. Era, en efecto, la causa dominante de la Brecha 1 (1.64→1.38). | `motor.py`, `data/imss_sbc_promedio.csv` | — |
| 4 | **Población inicial = muestra CONAPO 2025, edades 15–64**, sin mortalidad en el backcast (la muestra condiciona a estar vivo en 2025). El stock de pensionados pre-2026 queda **excluido**: el costo FPB reportado es solo de cohortes que se retiran 2026+ (subestima el costo total de Sección 8). | `motor.py` | Fabiola / Ian |
| 5 | **Solo trabajadores tipo IMSS** (sin ISSSTE, sin independientes). La validación compara contra RCV-IMSS. | `validacion.py` | Equipo |

## Los cinco bloques (versión skeleton)

| # | Decisión / supuesto | Dónde vive | Valida |
|---|--------------------|------------|--------|
| 6 | **Markov homogéneo 4 estados** {formal, informal, desempleado, fuera}; persistencias hand-coded (0.88/0.82/0.30/0.90) y masa restante repartida proporcional a las participaciones ENOE 2025T1 (formal 26.4%, informal 31.6%, desemp. 1.5%, fuera 40.5% — `client.enoe.snapshot_nacional`). **Efecto conocido:** subdispersión de la densidad de cotización ⇒ la mediana de la cohorte 2050 no alcanza las 1,000 semanas y la tasa de reemplazo p50 es 0. La heterogeneidad persistente (panel ENOE) es la Prioridad 1 de refinamiento. | `motor.py::matriz_markov` | Emiliano (Prioridad 1) |
| 7 | **Salarios:** lognormal persistente, mediana 3.5 UMA mensuales, σ_log 0.65, perfil de edad determinístico (pico ~50 años). Sin AR(1) todavía (§4.3 es Fase 2–3). | `config.yaml`, `motor.py` | Emiliano (Prioridad 2) |
| 8 | **Rendimientos:** backcast 1997–2025 con la **serie observada de rendimiento bruto real del sistema** (ver #23); proyección 2026+ con 4% real constante. Sin glide path por edad (TODO Fase 2, ver #23). | `config.yaml`, `data/consar_rendimiento_bruto_anual.csv` | Yáñez / Esponda (Prioridad 3) |
| 9 | **Mortalidad EMSSA-09 estática** (sin factores de mejora de la circular; sin Lee-Carter). Tabla parseada del DOF 2009-11-27 (ANEXO 4); sanity check: esperanza de vida al nacer H 75.5 / M 84.5. **Nota técnica:** la tabla cruza (qx mujeres > hombres) en edades 88+ — verificado contra la fuente, pero señalarlo a Yáñez. | `data/cnsf_emssa09_mortalidad.csv` | Yáñez (Prioridad 4) |
| 10 | **Reglas SAR exactas** (bloque no aproximado): vector de aportación año→tasa, tope 25 UMA, semanas 750→1000, retiro a 65, comisiones serie CONSAR observada. Salvedades abajo (11–15). | `reglas_sar.py` | Yáñez |

## Reglas SAR — salvedades por verificar contra DOF/CONSAR

| # | Decisión / supuesto | Dónde vive | Valida |
|---|--------------------|------------|--------|
| 11 | **Vector de aportación RCV promedio** (rampa lineal 6.5% 2022 → 15% 2030; 2024 ≈ 8.6%). El calendario real de la patronal de cesantía/vejez es **por banda de UMA**; falta construir la tabla por banda del DOF. | `reglas_sar.py::_TASA_RCV` | Yáñez / Andre |
| 12 | **Cuota social plana:** 8.0 pesos (reales 2025) por día cotizado si salario ≤ 4 UMA. La vigente es una tabla por banda actualizada por INPC. | `reglas_sar.py` | Andre |
| 13 | **Comisiones pre-2008:** 1.9% sobre saldo como equivalente (la estructura real era sobre flujo y opaca). 2008–2025: promedios anuales observados vía `client.consar.comisiones_serie`. Futuro: 0.55% constante. | `reglas_sar.py::_COMISIONES` | Esponda |
| 14 | **Pensión Garantizada como piso plano** de $7,750/mes (reales 2025), aproximación del promedio del tabulador post-2020 (edad × semanas × salario). El Estado paga el piso directo (en la ley, el saldo se agota primero). | `config.yaml`, `motor.py` | Fabiola / Yáñez |
| 15 | **FPB:** piso = min(salario promedio de cotización de la carrera, tope del año de retiro — regla en #22); elegibilidad = edad 65 + semanas cumplidas (ley 97). **Consecuencia visible:** la tasa de reemplazo de quien recibe complemento FPB es ≈ 1.0 por construcción ⇒ distribución bimodal {0, 1} en la Figura 2. No es un bug: es el diseño de la política; discutir cómo narrarlo en Sección 7. | `motor.py` | Fabiola / Yáñez |

## Anualización

| # | Decisión / supuesto | Dónde vive | Valida |
|---|--------------------|------------|--------|
| 16 | **Renta vitalicia anual anticipada**, ä_x = Σ v^k·ₖpₓ, con tasa técnica real 3% y EMSSA-09 por sexo. Pensión mensual = S/(12·ä₆₅). La convención exacta (mensual/anual, anticipada/vencida, tasa técnica, recargos) **es el punto donde un actuario mira primero**. | `reglas_sar.py::factor_anualidad` | **Yáñez (primera agenda)** |
| 17 | **Negativa de pensión** (semanas insuficientes): saldo en una exhibición, pensión 0, tasa de reemplazo 0. Sin pensión de sobrevivencia; el saldo de activos fallecidos sale del sistema (herencia no modelada) — por eso las cuentas simuladas (63M) < observadas (78M, que incluyen inactivas y de fallecidos). | `motor.py` | Yáñez |

## Otros

| # | Decisión / supuesto | Dónde vive | Valida |
|---|--------------------|------------|--------|
| 18 | **PIB:** 34.9 billones MXN (2025), crecimiento real 2% anual — solo para expresar costo FPB como % del PIB; reemplazar con la senda de Sección 8. *(2026-07-02: movido de `motor.py` a `config.yaml` sección `macro` — es supuesto de modelado y eje de sensibilidad, no ley; verificado byte-idéntico con misma semilla.)* | `config.yaml::macro` | Ian |
| 19 | **Escenarios** (§6): ±2 pp sobre la probabilidad de transitar a formal, a partir de 2026. Intervalos con 5 semillas por escenario. | `config.yaml`, `run_skeleton.py` | Equipo |
| 20 | **Cohorte 2050 de la Figura 2** = retiros 2048–2052 (ventana ±2 años) para tener n≈420 con 5,000 agentes; se etiqueta explícito en la figura. Escalar a 50–100k agentes cuando el motor valide (§10). | `figuras.py` | Equipo |
| 21 | **Reformas como overrides de ley (2026-07-02):** `reglas_sar.PoliticaSAR` acepta overrides opcionales (aportación, semanas, edad de retiro, cuota social, topes, comisión) con año de entrada en vigor `desde`; los defaults DOF/CONSAR quedan intactos con su cita. `PoliticaSAR()` vacía reproduce byte-idéntico la corrida vigente (verificado con misma semilla); el backcast 1997–2025 nunca se ve afectado por un override. Reformas se declaran en `config.yaml::reformas` (ejemplo ejecutable: `semanas_1250`, smoke test: % sin pensión 68%→80%, costo FPB 2050 0.39→0.18 billones). Piso PG y tope FPB se reforman directo en config (secciones `pension_garantizada`/`fpb`). | `reglas_sar.py::PoliticaSAR`, `config.yaml::reformas` | Equipo (Sección 9) |
| 22 | **Tope FPB anclado a fuentes (2026-07-02):** (a) el valor anterior $17,532 (16,777.68 + inflación ~4.5%) **no rastreaba a fuente oficial → descartado**; también se detectó y descartó $17,885.85 (solo prensa secundaria, sin fuente oficial). (b) Anclas verificadas: **$16,777.68/mes (2024)** — ley, Decreto de creación del FPB, DOF 01/05/2024 (<https://www.dof.gob.mx/nota_detalle.php?codigo=5725285&fecha=01/05/2024>, "salario mensual promedio registrado en el año 2023 en el IMSS actualizado"); **$17,364.00/mes (2026)** — CONSAR (<https://www.gob.mx/consar/es/articulos/fondo-de-pensiones-para-el-bienestar-394538>, "salario mensual promedio registrado en el año 2025 por el IMSS"). (c) **Regla de indexación (supuesto):** tope_t = salario medio de cotización IMSS_{t-1}; NO se indexa a INPC — las anclas implican ~1.7% anual vs inflación observada 2024-2025 de ~4-5%. Tramo 2024–2026: interpolación geométrica entre anclas (la serie IMSS no está en el SDK, ver ASKS); reproduce el oficial 2026 con error 0.00%; 2025 implícito = $17,068.32. Proyección 2027+: crece con `economia.crecimiento_salarial_secular_real` — el MISMO parámetro que mueve los salarios de los agentes (coherencia piso/salarios; 0 en el skeleton ⇒ tope real constante en 17,364). Efecto del cambio (misma semilla): costo FPB 2050 0.4022→0.3975 billones (−1.2%), % sin pensión y validación 2025 sin cambio. (d) **PENDIENTE DE VALIDACIÓN POSTERIOR:** confirmar el valor 2025 del tope contra fuente oficial, y leer el artículo del decreto que define el mecanismo exacto de actualización (el texto dice "actualizado" sin especificar fórmula). | `reglas_sar.py::tope_fpb_mensual`, `config.yaml::fpb` | Fabiola / Andre |

| 23 | **Calibración de rendimientos del backcast (2026-07-02).** **Fuente:** `client.consar.precios_gestion_serie` (precio de gestión interna, diario, 1997-07→2025-12, por AFORE×SIEFORE) — es el rendimiento **BRUTO**: verificación empírica CAGR gestión ~11.2% vs NAV ~10.1%, brecha ≈ serie de comisiones CONSAR; la comisión sigue explícita en C (no se netea dos veces). **Se descartó `rendimientos_*`**: solo cubre 2019-12+ y es IRN anualizado por plazo (12/24/36m), no retorno de periodo. **Agregación:** retorno dic-a-dic (último día hábil del año) por par; promedio simple entre SIEFOREs dentro de cada AFORE (los activos por SIEFORE no existen históricamente en el SDK) ponderado **por activos entre AFOREs** (`recursos_por_afore`, dic del año previo; 1997–1998 sin dato → pesos iguales). El **glide path por edad** (cada agente ve su SIEFORE generacional) es **TODO Fase 2**. **INPC:** general (serie SP1, Banxico SIE, mensual 1969-01→2026-05, base 2018) como estático `data/inpc_mensual.csv`; r_real=(1+r_nom)/(1+π)−1 con π dic-dic (ventana igual al retorno); sanity: 2017=6.77% ✓, 2024=4.21% ✓ (primer intento con SP74625 descartado: era el subyacente). **Tramo 1997-ene→jun:** la serie arranca 1997-07 (igual que el SAR); el retorno 1997 es jul→dic **sin anualizar** (equivale a asumir 0% en H1; los saldos de 1997 son ínfimos, efecto trivial). Serie reproducible con `data/build_rendimientos_brutos.py`; media real 1997–2025 = **5.02%** (2008: −5.1%, 2022: −9.3%). **Resultado: el ratio de saldo apenas se movió (1.6462→1.6405)** — la media observada (5.02%) es MAYOR que el 4% plano pero la secuencia (altos al inicio con saldos chicos, bajos 2013–2022 con saldos grandes) compensa. Los rendimientos NO eran la causa dominante de la Brecha 1; el sospechoso principal pasa a ser la **trayectoria salarial anclada a 2025** (supuesto #3). | `data/build_rendimientos_brutos.py`, `motor.py` | Emiliano / Esponda |

| 24 | **Backcast salarial con SBC IMSS observado (2026-07-02).** **Fuente:** microdatos de Datos Abiertos IMSS (<http://datos.imss.gob.mx>, datasets `asg-1997`…`asg-2026`, patrón `/sites/default/files/asg-AAAA-MM-DD.csv`) — el portal NO publica la serie agregada; se derivó de 30 archivos (~8 GB): SBC promedio = Σ`masa_sal_ta`/Σ`ta_sal`, diciembre de cada año 1997–2025 + may-2026, guardada en `data/imss_sbc_promedio.csv`. El esquema del CSV cambió dos veces (2017 inserta `rango_uma`; 2026 inserta `ptpd`): parseo por nombre de columna, no por posición. Cobertura real desde 1997 ⇒ la regla de extrapolación 1997–2004 prevista resultó innecesaria. **Sanity checks:** may-2026 $671.25 diarios vs punto público ~$671.3 (error 0.007%) ✓; crecimiento real dic-2012→may-2026 +37.2% vs ~37% validado externamente ✓. **Sustitución:** índice de nivel real (2025=1.0; 1997=0.608, 2005=0.751, 2015=0.785), multiplicativo sobre el salario de todos los agentes en el año calendario correspondiente, solo backcast (proyección sigue con `crecimiento_salarial_secular_real`). **Decisiones de modelado:** (1) el SBC agregado corrige el NIVEL transversal del backcast, NO el perfil individual edad-salario — eso es transversal vs longitudinal (confunde efectos cohorte/edad/periodo); el perfil longitudinal es **TODO Fase 2**. (2) **[I]** el índice mezcla crecimiento salarial puro con **recomposición del universo cotizante** (10.3M cotizantes en 1997 → 22.5M en 2025: formalización, entrada de jóvenes y sectores nuevos); explícitamente NO debe leerse como "crecimiento del salario individual". (3) **Hallazgo:** el perfil real es muy no-lineal — +23.6% (1997–2005), **+4.4% (2005–2015, estancamiento)**, +27.4% (2015–2025, auge del salario mínimo) — la Brecha 1 se explicaba principalmente por el estancamiento 2005–2015 que el ancla-2025 no capturaba. **Resultado:** saldo sim/obs **1.6405 → 1.3829**; cotizantes (0.96) y cuentas (0.81) sin cambio. **Residual 1.38 — atribución (sin forzar):** sospechoso marcado: backcast sin mortalidad (#4); candidato cuantificado adicional: la participación "formal" de ENOE incluye trabajadores del Estado (ISSSTE) cuyos fondos viven en RCV-ISSSTE, no en el target RCV-IMSS — contra RCV-IMSS+ISSSTE ($7.71 bn) el ratio sería **1.24**; también faltan retiros parciales por desempleo. Diagnóstico pendiente con el equipo. | `data/imss_sbc_promedio.csv`, `datos.py::cargar_indice_salarial_real`, `motor.py` | Emiliano / Yáñez |

## Estado de la validación 2025 (corrida 2026-07-02, vía API en vivo)

| Métrica | Simulado | Observado (CONSAR) | sim/obs |
|---|---|---|---|
| Saldo RCV-IMSS | 9.5 billones | 6.9 billones | **1.38** |
| Cotizantes | 27.9 M | 29.1 M | 0.96 |
| Cuentas con saldo | 63.2 M | 77.8 M | 0.81 |

Trayectoria de la Brecha 1: 1.65 (skeleton) → 1.64 (rendimientos
observados, #23) → **1.38 (backcast salarial SBC, #24)**. Residual:
candidatos en #24 — mezcla IMSS/ISSSTE en la participación formal
(contra RCV-IMSS+ISSSTE el ratio sería 1.24), backcast sin mortalidad
(#4), retiros parciales no modelados.
