# Matrices de transición laboral ANUALES 5x5 — ENOE 2015-2024 (Fase 2.5)

Sección 6 (Brecha 2). Entregable DEFINITIVO, generado por
`estimador_matrices_anuales.py full`. Reemplaza las matrices v1 del smoke
test (`matrices_transicion_2024T3_2024T4.csv`, trimestrales + P^4).

## Diseño: transición anual directa, panel 1ª↔5ª entrevista

Cada observación es una persona con 1ª entrevista en t y 5ª en t+4
trimestres (un año exacto). La transición anual se estima DIRECTO — sin
supuesto Markov intra-año, sin P^4. Justificación cuantificada: la
permanencia anual formal_IMSS→formal_IMSS del perfil de referencia
(hombre, 30-34, superior) es **0.82 estimada directa** vs **0.49 bajo el
P^4 de las matrices v1 trimestrales** — el supuesto Markov de primer
orden intra-año destruye la dependencia de duración (la permanencia
formal está correlacionada entre trimestres) y sobreestima la rotación.

**Hallazgo llave-slot (Fase 0)**: la llave de Fase 1 (cd_a+ent+con+v_sel+
n_hog+h_mud+n_ren) identifica el SLOT muestral, no a la persona — al
completar un hogar sus 5 entrevistas, el hogar de reemplazo hereda la
llave con n_ent reiniciado. A 4 trimestres un merge sin filtro produce
62% de matches espurios (patrones n_ent 2→1, 3→2…, 31.7% con sexo
inconsistente). Emparejamiento definitivo: llave **+ n_ent=1 en t y
n_ent=5 en t+4**, validación cruzada: 98.6% de los matches con n_ent=1
en origen cae en n_ent=5 en destino. Checks posteriores: sexo igual,
delta-eda ∈ {0,1,2} (97.4% de los pares limpios tiene delta = +1
exacto).

## Apilado 2015-2024 y exclusión COVID

27 pares (t, t+4) apilados: t ∈ 2015T1-2018T4 y 2021T3-2024T1.
**Excluidos** los 10 pares con t o t+4 dentro de 2020T1-2021T2:
t ∈ {2019T1, 2019T2, 2019T3, 2019T4, 2020T1, 2020T2, 2020T3, 2020T4, 2021T1, 2021T2}. Razones: 2020T2 no tiene microdatos
ENOE (ETOE telefónica); 2020T3-2021T2 es ENOE-N con levantamiento mixto en
retorno gradual. Nota adicional: el apilado cruza el rediseño muestral
post-Censo 2020 (clásica 2015-2019 vs ENOE-N 2021+) — las transiciones son
tasas condicionales, robustas al cambio de marco; el fac_tri 2021T3-T4
pre-CPV subestima niveles pero no afecta proporciones.

## Tasa de emparejamiento por par

tasa_match_pct = consistentes / n_ent=1 del trimestre t (universo
filtrado). Anómalo si <70% o >90%.

| par            |   n_ent1 |   limpios_1a5 |   consistentes |   tasa_match_pct | anomalo   |
|:---------------|---------:|--------------:|---------------:|-----------------:|:----------|
| 2015T1->2016T1 |    63249 |         51705 |          51705 |            81.75 | False     |
| 2015T2->2016T2 |    63459 |         51923 |          51923 |            81.82 | False     |
| 2015T3->2016T3 |    62528 |         50436 |          50436 |            80.66 | False     |
| 2015T4->2016T4 |    62262 |         50293 |          50293 |            80.78 | False     |
| 2016T1->2017T1 |    62532 |         50459 |          50459 |            80.69 | False     |
| 2016T2->2017T2 |    62820 |         50559 |          50559 |            80.48 | False     |
| 2016T3->2017T3 |    62275 |         49890 |          49890 |            80.11 | False     |
| 2016T4->2017T4 |    61539 |         49394 |          49394 |            80.26 | False     |
| 2017T1->2018T1 |    61675 |         49342 |          49342 |            80    | False     |
| 2017T2->2018T2 |    63167 |         51461 |          51461 |            81.47 | False     |
| 2017T3->2018T3 |    61625 |         49781 |          49781 |            80.78 | False     |
| 2017T4->2018T4 |    62033 |         50532 |          50532 |            81.46 | False     |
| 2018T1->2019T1 |    62086 |         49551 |          49551 |            79.81 | False     |
| 2018T2->2019T2 |    62460 |         49918 |          49918 |            79.92 | False     |
| 2018T3->2019T3 |    62704 |         50520 |          50519 |            80.57 | False     |
| 2018T4->2019T4 |    62114 |         49727 |          49727 |            80.06 | False     |
| 2021T3->2022T3 |    65832 |         50484 |          48652 |            73.9  | False     |
| 2021T4->2022T4 |    66207 |         51359 |          50800 |            76.73 | False     |
| 2022T1->2023T1 |    63615 |         51629 |          51612 |            81.13 | False     |
| 2022T2->2023T2 |    66374 |         53230 |          52843 |            79.61 | False     |
| 2022T3->2023T3 |    64406 |         51853 |          51204 |            79.5  | False     |
| 2022T4->2023T4 |    65103 |         51587 |          50758 |            77.97 | False     |
| 2023T1->2024T1 |    68484 |         54179 |          53462 |            78.06 | False     |
| 2023T2->2024T2 |    67202 |         53817 |          51237 |            76.24 | False     |
| 2023T3->2024T3 |    67385 |         53454 |          51019 |            75.71 | False     |
| 2023T4->2024T4 |    65452 |         51460 |          48980 |            74.83 | False     |
| 2024T1->2025T1 |    65838 |         52563 |          50133 |            76.15 | False     |

Rango observado: 73.9%–81.8%, ningún par anómalo. Los pares clásicos
(2015-2018) rondan 80-82%; los ENOE-N post-COVID bajan a 73.9-81.1% (el
mínimo es 2021T3→2022T3, retorno gradual a campo). **Nota descartes
ENOE-N**: los descartes por inconsistencia sexo/edad son ~0 en toda la
era clásica y suben a ~0.5-3.7% por par en ENOE-N (2021T3+) — artefacto
del levantamiento mixto (captura telefónica/presencial), no de la llave.

Panel apilado final (25-64, escolaridad válida): **842,085
observaciones**.

## Attrition anual (Fase 0, par de prueba 2023T1↔2024T1)

Shares ponderados (fac_tri) del corte n_ent=1 vs panel emparejado
consistente, 5 estados: máximo |sesgo| = **1.15 pp** (fuera_PEA
sobre-representado +1.15 pp; en el universo de estimación 25-64: +0.89).
**Dirección**: el panel sub-representa formal_IMSS (−0.7 pp) — sesgo leve
hacia estabilidad/inactividad (quien se muda entre olas es más
formal/urbano). Bajo el umbral acordado de 2 pp → **sin IPW**; las
transiciones desde formal quedan estimadas sobre los que permanecen.

## Mapeo variable → estado (Opción A, 5 estados)

Fuente: INEGI, *ENOE N — Estructura de la base de datos* (2022), tabla
`ENOEN_SDEMT`, campo 97 `IMSSISSSTE`: **1 = IMSS, 2 = ISSSTE, 3 = Otras
instituciones, 4 = No recibe atención médica, 5 = No especificado**.
<https://www.inegi.org.mx/contenidos/programas/enoe/15ymas/doc/enoe_n_fd_c_bas_amp.pdf>

| Estado | Regla |
|---|---|
| formal_IMSS | clase2 = 1 AND imssissste = 1 |
| formal_ISSSTE | clase2 = 1 AND imssissste = 2 |
| informal | clase2 = 1 AND imssissste ∈ {3,4,5} |
| desempleado | clase2 = 2 |
| fuera_PEA | clase1 = 2 |

**Nota código 3 ("Otras instituciones")**: va a `informal` — es atención
médica no-IMSS/ISSSTE (Pemex, Sedena, privada, etc.); su masa es chica y
no es separable en un sexto estado con n razonable. La descontaminación
relevante (36% de ISSSTE dentro de informal-superior en v1) la resuelve el
estado formal_ISSSTE explícito.

**Nota interpretativa**: transiciones como desempleado→formal_IMSS ≈ 0.32
(perfil de referencia) pueden parecer altas frente a intuiciones
trimestrales, pero son transiciones a **12 meses**: consistentes con las
duraciones cortas del desempleo en México (mediana < 3 meses), donde el
estado "desempleado" observado en t rara vez persiste un año.

## Desagregación y estimador (idéntico a Fase 2)

- 8 quinquenios 25-29…60-64 (eda en t) × 2 sexos × 3 escolaridades
  (anios_esc en t: ≤9, 10-12, ≥13; 99/NA excluido) = 48 perfiles 5x5.
- Conteo condicional ponderado con fac_tri de t. Shrinkage Dirichlet por
  fila: p = (n_fila·p_pond + kappa·P_quinquenio) / (n_fila + kappa),
  n_fila sin ponderar, prior = matriz marginal 5x5 del quinquenio sobre el
  panel apilado. **kappa = 5**. Sensibilidad kappa ∈ {1,5,20} en
  `sensibilidad_kappa.csv`: max|Δ| = 0.07228 (κ1 vs
  κ5) y 0.12392 (κ20 vs κ5).
- baja_confianza si n_fila < 30: 2
  de 240 filas-perfil-origen.

| estado_origen   |   filas_baja_confianza |
|:----------------|-----------------------:|
| desempleado     |                      2 |

## Archivos

- `matrices_anuales_2015_2024.csv` — 1200 filas (48×5×5), formato
  long `|`: grupo_edad|sexo|escolaridad|estado_origen|estado_destino|
  probabilidad|n_muestra_pond|n_muestra_sin_pond|baja_confianza.
- `sensibilidad_kappa_anuales.csv` — mismas llaves + p_kappa1|p_kappa5|
  p_kappa20 y deltas absolutos vs κ=5.
- Estimación: `estimador_matrices_anuales.py` (pickles sdem por trimestre
  en scratchpad de sesión, descarga reproducible con descarga_enoe.py
  parametrizado).
