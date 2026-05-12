# Tutorial — análisis cross-dataset

El namespace `client.comparativo` es el más distintivo del observatorio: combina indicadores de los tres datasets principales (CDMX × CONSAR × ENIGH) en endpoints donde **el equipo del observatorio ya armó el cruce metodológico**. Es decir, no es responsabilidad del usuario construir denominadores compatibles; eso lo hizo el equipo y lo documenta en los caveats editoriales del propio endpoint.

Este tutorial muestra los siete endpoints comparativos, con énfasis en cómo leer los textos editoriales que los acompañan.

## Por qué los endpoints comparativos son distintos

Cuando comparas dos datasets directamente, la persona que arma el cruce tiene que tomar decisiones metodológicas: qué denominador usar, qué fecha de corte alinear, cómo manejar definiciones que difieren entre fuentes. El equipo del observatorio toma esas decisiones, las **documenta explícitamente** en campos como `narrative`, `caveats`, `nota_hipotesis`, e `interpretacion`, y publica el resultado.

Esto significa que si vas a citar un comparativo, **debes leer el `narrative` del endpoint** y reproducir el cruce con sus mismas decisiones, o explicar dónde te apartas.

→ Ver [Caveats editoriales](../conceptos/caveats-editoriales.md).

## Aportes vs jubilaciones actuales

Este es uno de los endpoints centrales para el paper Amafore-ITAM 2026:

```python
from datos_mexico import DatosMexico

with DatosMexico() as client:
    resp = client.comparativo.aportes_vs_jubilaciones_actuales()
    cdmx = resp.cdmx_aportes_actuales
    enigh = resp.enigh_jubilaciones_actuales
    print("CDMX (servidor activo):")
    print(f"  Servidores:                  {cdmx.n_servidores:,}")
    print(f"  Sueldo bruto medio mensual: ${cdmx.mean_sueldo_bruto:,.2f}")
    print(f"  Deducción media mensual:    ${cdmx.mean_deduccion_total:,.2f}")
    print(f"  % deducción / bruto:         {cdmx.pct_deduccion_sobre_bruto}%")
    print()
    print("ENIGH (hogares con jubilación):")
    print(f"  Hogares con jubilación:      {enigh.n_hogares_con_jubilacion_expandido:,}")
    print(f"  % hogares con jubilación:    {enigh.pct_hogares_con_jubilacion}%")
    print(f"  Jubilación media mensual:   ${enigh.mean_jubilacion_solo_jubilados_mensual:,.2f}")
    print()
    print("=== INTERPRETACIÓN ===")
    print(resp.interpretacion)
    print()
    print("=== CAVEATS ===")
    for c in resp.caveats:
        print(f"- {c}")
```

El endpoint cruza dos realidades coexistentes del sistema de pensiones — las deducciones actuales del servidor CDMX activo y las jubilaciones que reciben hoy los hogares ENIGH — sin pretender que sea una comparación actuarial. El campo `interpretacion` (texto pre-redactado por el equipo) aclara explícitamente qué se puede y qué NO se puede concluir.

## Ingresos CDMX vs nacional

```python
with DatosMexico() as client:
    resp = client.comparativo.ingreso_cdmx_vs_nacional()
    print(f"Servidor CDMX:    sueldo medio mensual ${resp.cdmx_servidor.mean_sueldo_bruto_mensual:,.2f}")
    print(f"Hogar nacional:   ingreso medio mensual ${resp.enigh_hogar_nacional.mean_ing_cor_mensual:,.2f}")
    print(f"Hogar CDMX:       ingreso medio mensual ${resp.enigh_hogar_cdmx.mean_ing_cor_mensual:,.2f}")
    print(f"Ratio hogar nacional / servidor:  {resp.ratio_hogar_nacional_sobre_servidor}")
    print(f"Ratio hogar CDMX / servidor:      {resp.ratio_hogar_cdmx_sobre_servidor}")
    print()
    print(resp.note)
```

El endpoint expone tres bloques con shape uniforme: el servidor CDMX (sueldo bruto mensual medio y mediano) y dos bloques ENIGH (hogar nacional y hogar CDMX, con ingreso corriente medio mensual). Las razones `ratio_hogar_*_sobre_servidor` vienen precomputadas. El campo `note` aclara que la "brecha" no es equivalente a desigualdad entre personas — el hogar ENIGH promedio combina varios perceptores, transferencias y rentas, no un solo salario.

## Gastos CDMX vs nacional

```python
with DatosMexico() as client:
    resp = client.comparativo.gastos_cdmx_vs_nacional()
    print(f"Gasto mensual medio CDMX:     ${resp.mean_gasto_mon_mensual_cdmx:,.2f}")
    print(f"Gasto mensual medio nacional: ${resp.mean_gasto_mon_mensual_nacional:,.2f}")
    print("Por rubro (CDMX vs nacional, primeros 5):")
    for r in resp.rubros[:5]:
        print(f"  {r.nombre:<32} CDMX ${r.mean_cdmx_mensual:>8,.0f}  Nac ${r.mean_nacional_mensual:>8,.0f}  Δ {r.delta_pct:>+6.2f}%")
```

Similar al anterior pero del lado del gasto del hogar. Cada rubro trae también el peso porcentual sobre el gasto monetario total de cada universo (`pct_del_monetario_cdmx`, `pct_del_monetario_nacional`) para detectar diferencias estructurales — por ejemplo, qué tanto pesan "Educación y esparcimiento" o "Transporte" en el gasto típico de un hogar de CDMX vs el promedio nacional.

## Decil servidores CDMX en distribución nacional

```python
with DatosMexico() as client:
    resp = client.comparativo.decil_servidores_cdmx()
    print("Fronteras de decil ENIGH (lower → upper mensual):")
    for db in resp.enigh_deciles_mensuales:
        print(f"  D{db.decil:<2}  ${db.lower_mensual:>9,.0f}  →  ${db.upper_mensual:>9,.0f}")
    print()
    for esc in resp.escenarios:
        print(f"Escenario: {esc.nombre}")
        print(f"  Supuesto: {esc.supuesto}")
        for m in esc.mapeo:
            print(f"    {m.percentil}  ingreso supuesto ${m.ingreso_hogar_supuesto_mensual:,.0f} → decil {m.decil_hogar_enigh}")
    print()
    print(resp.narrative)
```

El endpoint expone tres piezas: las **fronteras** de los 10 deciles ENIGH (`enigh_deciles_mensuales`), uno o más **escenarios** de mapeo (perceptor único vs servidor + cónyuge mediano), y la **narrativa** del observatorio explicando cómo leer cada escenario. El campo `caveats_interpretativos` (estructurado en cuatro lecturas: `frontera_p50`, `narrativa_correcta`, `insight_principal`, `implicacion_narrativa`) precomputa la interpretación correcta para evitar simplificaciones tipo "servidor público CDMX = decil 2".

**Caveat clave**: el universo de servidores CDMX no es directamente comparable con el universo ENIGH (que es hogares mexicanos). El cruce es a nivel ingreso individual contra fronteras de decil de hogar, bajo supuestos explícitos sobre composición del hogar.

## Top vs bottom

```python
with DatosMexico() as client:
    resp = client.comparativo.top_vs_bottom()
    print(f"top_bracket    keys: {list(resp.top_bracket.keys())}")
    print(f"bottom_bracket keys: {list(resp.bottom_bracket.keys())}")
    print()
    print(resp.narrative)
    print()
    print("Insights:")
    for ins in resp.insights:
        print(f"  - {ins}")
```

Los campos `top_bracket` y `bottom_bracket` son **schema-libre** (dicts genéricos) — su shape lo decide el observatorio server-side y puede evolucionar entre versiones. La interfaz estable del endpoint es la `narrative` (texto editorial) y la lista de `insights`, que cruzan los percentiles altos del servidor CDMX (p95, p99) contra los deciles 1 y 10 de ENIGH para mostrar dónde cae el bracket de CDMX dentro de la distribución de hogares mexicanos.

## Bancarización

```python
with DatosMexico() as client:
    resp = client.comparativo.bancarizacion()
    print(f"Definición operativa: {resp.definicion_operativa}")
    print()
    print(f"Hogares nacionales con uso de tarjeta: {resp.pct_nacional}%  "
          f"({resp.hogares_con_uso_tarjeta_nacional:,} de {resp.n_hogares_expandido_nacional:,})")
    print(f"Hogares CDMX con uso de tarjeta:       {resp.pct_cdmx}%  "
          f"({resp.hogares_con_uso_tarjeta_cdmx:,} de {resp.n_hogares_expandido_cdmx:,})")
    print(f"Brecha:  {resp.delta_pp} pp   Ratio CDMX/Nac: {resp.ratio_cdmx_sobre_nacional}×")
```

El endpoint compara la proporción de **hogares** con uso de tarjeta de débito o crédito en CDMX vs el agregado nacional (no compara servidores públicos individuales). La definición operativa exacta del observatorio se expone en `definicion_operativa`. CDMX tiene una tasa significativamente mayor de bancarización por hogar que el promedio del país.

## Actividad CDMX vs nacional

```python
with DatosMexico() as client:
    resp = client.comparativo.actividad_cdmx_vs_nacional()
    print(f"Universo: {resp.n_hogares_total_cdmx:,} hogares CDMX / "
          f"{resp.n_hogares_total_nacional:,} nacional")
    for bloque in (resp.agro, resp.noagro):
        print(f"\n{bloque.tipo}:")
        print(f"  Nacional: {bloque.hogares_expandido_nacional:,} ({bloque.pct_nacional}%)")
        print(f"  CDMX:     {bloque.hogares_expandido_cdmx:,} ({bloque.pct_cdmx}%)")
        print(f"  Ratio CDMX/Nac: {bloque.ratio_cdmx_sobre_nacional}")
    print()
    print(resp.note)
    print()
    print("Hipótesis del equipo:")
    print(resp.nota_hipotesis)
```

Compara la proporción de hogares con **actividad agropecuaria** vs **no agropecuaria** entre CDMX y el promedio nacional. CDMX tiene presencia residual de actividad agro (apenas 0.24 % vs 9.64 % nacional) y una tasa de actividad no-agro algo menor a la nacional. Los campos `note` y `nota_hipotesis` documentan las hipótesis del observatorio sobre por qué — el dataset no resuelve por sí solo la pregunta de informalidad capitalina.

## Workflow para investigación de pensiones

El paper Amafore-ITAM 2026 (deadline 31 de julio 2026) es el caso de uso central que motivó el desarrollo del SDK. El [notebook 05_paper_amafore_workflow.ipynb](https://github.com/Datos-Mexico/datos-mexico-py/blob/main/examples/05_paper_amafore_workflow.ipynb) reproduce el flujo cross-dataset completo:

1. `consar.recursos_totales()` y `consar.pea_cotizantes_serie()` → cobertura del SAR.
2. `comparativo.aportes_vs_jubilaciones_actuales()` → presión actuarial contemporánea.
3. `enigh.hogares_by_decil()` → distribución del ingreso de hogares.
4. `cdmx.dashboard_stats()` → benchmark de sueldo formal capitalino.
5. Cruces ad-hoc usando los caveats de cada endpoint para no mezclar definiciones incompatibles.

## Próximos pasos

- [Reference completo comparativo](../reference/comparativo.md).
- [Caveats editoriales](../conceptos/caveats-editoriales.md) — guía para leer los textos del observatorio.
- [Notebook Amafore](https://github.com/Datos-Mexico/datos-mexico-py/blob/main/examples/05_paper_amafore_workflow.ipynb) — workflow narrado paso a paso.
