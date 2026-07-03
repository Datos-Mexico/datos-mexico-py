# ASKS PARA LA JUNTA — Motor Sección 6 (walking skeleton, 2026-07-01)

> El motor **ya corre de punta a punta, valida contra 2025 y produce
> distribuciones** (`python -m motor.run_skeleton`). Estos son los bloqueos
> y decisiones que el equipo debe resolver para pasar a Fase 2.

## 1. Auditoría de datos — checklist de insumos (brief §2)

| # | Insumo | Estado | Detalle |
|---|--------|--------|---------|
| 1 | Matrices de transición ENOE | 🟡 **Crudo** | No hay matrices estimadas. El SDK expone agregados ENOE (participaciones 2025T1, usadas para el Markov homogéneo) y ~101.5M microdatos con paginación (`client.enoe.microdatos_iter`, tabla `sdem`) de los que **sí** puede estimarse el panel. No bloqueante para el skeleton. |
| 2 | Tablas de mortalidad CNSF | 🟢 **Resuelto hoy** | EMSSA-09 (qx 0–109, H/M) parseada del DOF y guardada en `motor/data/cnsf_emssa09_mortalidad.csv`. Deuda: factores de mejora de la circular no aplicados. |
| 3 | Proyecciones CONAPO 2025–2070 | 🟢 **Resuelto hoy** | Descarga oficial CONAPO (conciliación 2023) filtrada a nacional: `motor/data/conapo_proyecciones_nacional_2025_2070.csv`. |
| 4 | Rendimientos SIEFOREs | 🟡 **Parcial** | SDK: `client.consar.rendimientos_*` cubre **2019–2025** (36 meses, por SIEFORE generacional). El brief pide 2010–2025: falta el tramo 2010–2018 (¿entra al observatorio o archivo estático?). |
| 5 | Distribuciones salariales IMSS/ENOE | 🟡 **Crudo** | ENIGH y microdatos ENOE accesibles vía SDK, sin calibrar. El repo `proyecto-final-bd-itam-2026` solo aporta salarios del sector público CDMX (no representativo). Bloquea la calibración de Sección 4, no el skeleton. |
| 6 | Agregados observados 2025 | 🟢 **Presente y validado** | `client.consar` en vivo: RCV-IMSS $6.89 billones (dic 2025), 29.1M cotizantes (2024), 77.8M cuentas (dic 2025), comisiones 0.547%. El check de composición del SAR cierra al peso. |

**SDK/API:** `datos-mexico` instalado (editable, `.venv/`), `api.datos-itam.org`
responde; todas las llamadas de validación corren en vivo con fallback estático.

## 2. Decisiones actuariales — agenda con la Dra. Yáñez (prioridad máxima)

1. **Convención de anualización** (§4.6): hoy renta vitalicia anual
   anticipada, tasa técnica real 3%, EMSSA-09 por sexo. ¿Mensual vencida?
   ¿Qué tasa técnica? ¿Recargos de seguridad?
2. **PG como tabulador** (edad × semanas × salario) vs piso plano actual
   de $7,750. ¿Nos comparte o construimos el tabulador vigente?
3. **Reglas exactas del FPB**: elegibilidad, definición del "salario
   promedio de cotización" (¿nominal histórico actualizado?, ¿toda la
   carrera o últimos años?) y mecánica del complemento. Con las reglas
   actuales la tasa de reemplazo de beneficiarios FPB es ≈100% por
   construcción (bimodal {0,1} en la Figura 2) — ¿es la lectura correcta
   de la política?
4. **EMSSA-09**: ¿aplicar factores de mejora de la circular? Señalar el
   cruce qx M>H en edades 88+ (verificado contra la fuente DOF).

## 3. Contratos de interfaz (brief §7)

- **Emiliano (Sección 4):** ¿en qué formato y fecha entrega (a) matrices de
  transición del panel ENOE (¿por edad/género/escolaridad?), (b) proceso de
  salarios calibrado (μ, φ, σ)? El motor hoy consume una matriz 4×4 y
  parámetros lognormales de `config.yaml` — cualquier formato tabular sirve.
- **Ian / Fabiola (Secciones 7–8):** confirmar columnas de
  `motor/outputs/agentes.csv` y `agregados_anuales.csv` (schema propuesto
  del brief §7 ya implementado) para no rehacer el output.

## 4. Decisiones de modelado que el equipo debe tomar

1. **Stock de pensionados pre-2026:** hoy excluido ⇒ el costo FPB reportado
   (0.40 billones reales / 0.70% del PIB en 2050, escenario base) es solo de
   cohortes nuevas. Sección 8 necesita el costo total: ¿se modela el stock o
   se suma exógeno (CONSAR reporta ~2.3M cuentas resguardadas en FPB)?
2. **Plan para cerrar la brecha de validación** (saldo sim/obs = 1.65):
   (a) índice de salario real IMSS para el backcast, (b) rendimiento real
   histórico observado en lugar de 4% plano, (c) comisiones pre-2008.
   ¿Quién toma cada pieza?
3. **Base real vs nominal:** el motor corre en pesos reales 2025. ¿Sección 8
   quiere salidas nominales (necesita senda de inflación explícita)?
4. **Rendimientos 2010–2018:** ¿se suben al observatorio (SDK) o archivo
   estático como CNSF/CONAPO?
5. **Escala:** skeleton corre con 5,000 agentes (1.2s las 15 corridas).
   ¿Subimos a 50–100k ya o después de calibrar?
6. **Serie de salario medio de cotización IMSS — LOCALIZADA, absorber al
   SDK:** no existe agregada en ningún lado; la derivamos de los microdatos
   de Datos Abiertos IMSS (datos.imss.gob.mx, `asg-1997`…`asg-2026`,
   ~390 MB/mes; SBC = masa_sal_ta/ta_sal). Validada al 0.007% contra el
   punto público de may-2026 (bitácora #24). Hoy es estático anual
   (diciembres) en `motor/data/imss_sbc_promedio.csv`. **Triple uso:**
   (a) tope FPB (= salario medio IMSS del año previo, #22), (b) calibración
   del nivel salarial (#7), (c) backcast salarial del motor (#24, ya en
   producción). El microdato trae sexo/edad/entidad/sector — absorber al
   observatorio daría además el perfil por sexo/edad para Fase 2.
7. **Serie INPC al SDK:** el motor ya la necesita permanentemente (deflactar
   rendimientos, bitácora #23; futuro: salidas nominales para Sección 8).
   Hoy es estático `motor/data/inpc_mensual.csv` (Banxico SIE, serie SP1).
   ¿Se absorbe al observatorio como dataset de precios?

## 5. Qué NO prometemos aún (brief §9)

Validación completa 2025, matrices ENOE reales, salarios AR(1),
rendimientos estocásticos y Lee-Carter son **Fase 2–3**. Lo entregado hoy:
motor end-to-end con check contable ΔS=A+R−C pasando en cada periodo,
validación cruda contra CONSAR en vivo, dos figuras y esta bitácora.
