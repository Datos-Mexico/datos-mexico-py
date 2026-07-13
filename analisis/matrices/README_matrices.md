# Matrices de transición laboral heterogéneas — ENOE 2024T3→2024T4

Sección 6 (Brecha 2) del motor de microsimulación. Entregable de Fase 2,
generado por `estimador_matrices.py full`. **v1 — un solo par trimestral.**

## Rango temporal y limitación declarada

Un único par de trimestres emparejados: **2024T3 → 2024T4**. Esto implica:
(i) la **estacionalidad Q3→Q4 no está controlada** (fin de año concentra
contrataciones formales de temporada y salidas escolares hacia la PEA);
(ii) **n delgado** en las filas de origen `desempleado` y `fuera_PEA` de
varios perfiles. La matriz FINAL del paper requiere **apilar múltiples
pares trimestrales consecutivos (Fase 2.5, pendiente)**; esta v1 sirve para
validar el pipeline y la forma de la heterogeneidad.

## Mapeo variable → estado (contrato §4)

Fuente oficial: INEGI, *ENOE N — Estructura de la base de datos* (2022),
tabla `ENOEN_SDEMT`, campo 97 `IMSSISSSTE` "Instituciones de atención
médica": **1 = IMSS, 2 = ISSSTE, 3 = Otras instituciones, 4 = No recibe
atención médica, 5 = No especificado**.
<https://www.inegi.org.mx/contenidos/programas/enoe/15ymas/doc/enoe_n_fd_c_bas_amp.pdf>
(págs. 24–25).

| Estado | Regla |
|---|---|
| formal_IMSS | clase2 = 1 AND imssissste = 1 (solo IMSS) |
| informal | clase2 = 1 AND imssissste ∈ {2,3,4,5} |
| desempleado | clase2 = 2 |
| fuera_PEA | clase1 = 2 (incluye clase2 ∈ {3,4}) |

### Decisión ISSSTE (Opción B) y sesgo cuantificado

En v1 los ocupados con ISSSTE (imssissste=2) y otras instituciones (=3) se
colapsan en `informal`. Porcentaje ponderado (fac_tri) del estado informal
que en realidad tiene seguridad social institucional, por escolaridad:

| escolaridad   |   pct_informal_imssissste_2_3 |   pct_solo_issste_cod2 |   n_sin_pond_informal |
|:--------------|------------------------------:|-----------------------:|----------------------:|
| basica-       |                          1.94 |                   1.54 |                 32760 |
| media_sup     |                         11.02 |                   9.59 |                 14047 |
| superior      |                         36    |                  33.41 |                 16907 |

**Limitación v1 declarada:** sus transiciones sectoriales quedan
aproximadas; el motor los reinyecta vía `sector_issste`.

## Universo y emparejamiento

- Universo (ambos trimestres, antes del merge): clase1 ∈ {1,2} AND
  r_def = 0 AND c_res ≠ 3. T3: 332,178 filas; T4:
  333,753.
- Llave persona: cd_a+ent+con+v_sel+n_hog+h_mud+n_ren (única en ambos
  trimestres; `h_mud` extraída de `extras_jsonb`).
- Emparejadas: 240,213 (72.31% de T3).
- **Matches descartados por inconsistencia** (sexo distinto o Δeda ∉
  {0,1}): **4,173**.
- Escolaridad no especificada (anios_esc=99) excluida:
  236 filas.
- Panel final 25–64: 144,035 observaciones.

## Desagregación (SPEC §6)

- Edad: quinquenios 25-29 … 60-64 sobre `eda` en t (2024T3).
- Sexo: sex 1=hombre, 2=mujer.
- Escolaridad: **`anios_esc` en t** (NIV_INS descartada: su código 4
  colapsa "medio superior y superior"). Cortes: básica- ≤ 9 años,
  media_sup 10–12, superior ≥ 13.
- 48 perfiles × matriz 4×4, formato long, separador `|`.

## Estimador y suavizamiento (SPEC §5)

Conteo condicional ponderado con `fac_tri` de t. Shrinkage Dirichlet por
fila: alpha_ij = kappa · P_marginal_edad_ij, donde P_marginal_edad es la
matriz cruda del quinquenio (colapsando sexo y escolaridad). Posterior:
p_ij = (n_fila · p_pond_ij + kappa · P_edad_ij) / (n_fila + kappa), con
n_fila el conteo SIN ponderar (kappa = pseudo-observaciones del prior).

**N efectivo del update (auditoría):** los pseudo-conteos del update
Dirichlet NO son las sumas crudas de fac_tri (escala poblacional, millones
— harían inoperante cualquier kappa razonable), sino las proporciones
ponderadas por fac_tri re-escaladas al conteo SIN ponderar de la
fila-perfil: c_ij = n_fila · p_pond_ij. El denominador de cada fila es
n_fila + kappa y el prior pesa kappa/(n_fila + kappa).

- **kappa = 5** (elegido): imperceptible en filas robustas, estabiliza las
  delgadas sin dominarlas. Sensibilidad completa por celda bajo
  kappa ∈ {1,5,20} en `sensibilidad_kappa.csv`; máximo |Δp| global:
  0.18507 (κ=1 vs 5) y 0.19052
  (κ=20 vs 5).
- **Celdas suavizadas**: todas las filas con n_fila > 0 reciben el
  shrinkage; el efecto es material solo donde `baja_confianza=True`.
- Filas con denominador 0: probabilidad = NaN (marcadas, nunca cero
  silencioso) y baja_confianza=True.

## Baja confianza (n sin ponderar < 30 en la fila-perfil)

14 de 192
filas-perfil-origen. Por estado de origen:

| estado_origen   |   filas_baja_confianza |
|:----------------|-----------------------:|
| desempleado     |                     14 |

Las 14 son filas de origen `desempleado` (mujeres 45+ y perfiles de alta
escolaridad en edades mayores). `fuera_PEA` no cae bajo el umbral en
ningún perfil: aun siendo minoritario en flujos, su stock en 25–64 es
suficientemente grande. El piso muestral está en desempleadas de 60–64
(n=4).

## Archivos

- `matrices_transicion_2024T3_2024T4.csv` — 768 filas (48×4×4), columnas
  SPEC §7: grupo_edad|sexo|escolaridad|estado_origen|estado_destino|
  probabilidad|n_muestra_pond|n_muestra_sin_pond|baja_confianza.
- `sensibilidad_kappa.csv` — mismas llaves + p_kappa1|p_kappa5|p_kappa20 y
  deltas absolutos vs κ=5.
- Attrition del panel (Fase 1): sesgo ≤ 0.3 pp por estado; sin corrección
  en v1.
