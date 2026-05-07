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
    print("=== INDICADOR ===")
    print(f"Aportes mensuales: ${resp.aportes_mensuales:,.0f}")
    print(f"Jubilaciones:      ${resp.jubilaciones_mensuales:,.0f}")
    print(f"Ratio:             {resp.ratio:.3f}")
    print()
    print("=== NARRATIVE ===")
    print(resp.narrative)
    print()
    print("=== CAVEATS ===")
    print(resp.caveats)
```

El endpoint cruza el flujo agregado de aportes al SAR (CONSAR) contra el flujo de jubilaciones pagadas (estimado vía ENIGH + supuestos demográficos). El `narrative` explica cómo se construyó el ratio y por qué es informativo (o por qué no lo es para ciertas preguntas).

## Ingresos CDMX vs nacional

```python
with DatosMexico() as client:
    resp = client.comparativo.ingreso_cdmx_vs_nacional()
    print(f"Ingreso mediano CDMX:     ${resp.cdmx_mediano:,.0f}")
    print(f"Ingreso mediano nacional: ${resp.nacional_mediano:,.0f}")
    print(f"Ratio CDMX/Nacional:      {resp.ratio_mediano:.2f}")
    print()
    print(resp.narrative)
```

El endpoint usa CDMX servidores públicos como aproximación al ingreso "formal capitalino". Esto es explícitamente NO el ingreso del hogar promedio en CDMX (que vendría de ENIGH segmentado por entidad). El `narrative` aclara qué pregunta sí puede responder y cuál no.

## Gastos CDMX vs nacional

```python
with DatosMexico() as client:
    resp = client.comparativo.gastos_cdmx_vs_nacional()
    print(f"Gasto mediano CDMX:     ${resp.cdmx_gasto_mediano:,.0f}")
    print(f"Gasto mediano nacional: ${resp.nacional_gasto_mediano:,.0f}")
```

Similar al anterior pero del lado del gasto del hogar.

## Decil servidores CDMX en distribución nacional

```python
with DatosMexico() as client:
    resp = client.comparativo.decil_servidores_cdmx()
    for fila in resp.distribucion:
        print(f"D{fila.decil:<2} servidores: {fila.share_servidores * 100:>5.1f}%")
```

Donde caen los servidores públicos CDMX en la distribución nacional ENIGH. Útil para responder "¿son bien o mal pagados?" comparado con la población general.

**Caveat clave**: el universo de servidores CDMX no es comparable directamente con el universo ENIGH (que es hogares mexicanos). El cruce es a nivel ingreso individual contra deciles de hogar. El `narrative` explica esa decisión.

## Top vs bottom

```python
with DatosMexico() as client:
    resp = client.comparativo.top_vs_bottom()
    print(f"Top 10% mediano:      ${resp.top_mediano:,.0f}")
    print(f"Bottom 10% mediano:   ${resp.bottom_mediano:,.0f}")
    print(f"Ratio:                {resp.ratio:.1f}x")
```

Razón de Palma simplificada (top decil / bottom decil de ingreso). Para CDMX se usa el padrón directamente; para ENIGH se usa el cálculo nacional.

## Bancarización

```python
with DatosMexico() as client:
    resp = client.comparativo.bancarizacion()
    print(f"Hogares con cuenta:           {resp.con_cuenta_pct:.1f}%")
    print(f"Servidores CDMX bancarizados: {resp.servidores_pct:.1f}%")
```

Cobertura del sistema bancario en hogares (ENIGH) vs cobertura en sector público (CDMX). El gap entre ambos es noticia social, no técnica.

## Actividad CDMX vs nacional

```python
with DatosMexico() as client:
    resp = client.comparativo.actividad_cdmx_vs_nacional()
    print(resp.narrative)
```

Compara composición de actividad económica (formal/informal) entre CDMX y el promedio nacional.

## Workflow para investigación de pensiones

El paper Amafore-ITAM 2026 (deadline 31 de julio 2026) es el caso de uso central que motivó el desarrollo del SDK. El [notebook 05_paper_amafore_workflow.ipynb](https://github.com/datos-mexico/datos-mexico-py/blob/main/examples/05_paper_amafore_workflow.ipynb) reproduce el flujo cross-dataset completo:

1. `consar.recursos_totales()` y `consar.pea_cotizantes_serie()` → cobertura del SAR.
2. `comparativo.aportes_vs_jubilaciones_actuales()` → presión actuarial contemporánea.
3. `enigh.hogares_by_decil()` → distribución del ingreso de hogares.
4. `cdmx.dashboard_stats()` → benchmark de sueldo formal capitalino.
5. Cruces ad-hoc usando los caveats de cada endpoint para no mezclar definiciones incompatibles.

## Próximos pasos

- [Reference completo comparativo](../reference/comparativo.md).
- [Caveats editoriales](../conceptos/caveats-editoriales.md) — guía para leer los textos del observatorio.
- [Notebook Amafore](https://github.com/datos-mexico/datos-mexico-py/blob/main/examples/05_paper_amafore_workflow.ipynb) — workflow narrado paso a paso.
