# Tutorial — ENIGH (hogares)

El namespace `client.enigh` cubre la **Encuesta Nacional de Ingresos y Gastos de los Hogares 2024 — Nueva Serie** del INEGI: 91,414 hogares en muestra que se expanden a 38.8M hogares mexicanos vía factores de elevación. Es el dataset canónico para estudiar desigualdad de ingreso, composición del gasto, y demografía.

## Resumen del universo

```python
from datos_mexico import DatosMexico

with DatosMexico() as client:
    resp = client.enigh.hogares_summary()
    print(f"Hogares en muestra:  {resp.n_hogares_muestra:,}")
    print(f"Hogares expandidos:  {resp.n_hogares_expandido:,}")
    print(f"Personas:            {resp.n_personas_expandido:,}")
```

La diferencia entre muestra y expandido es la lógica de la encuesta: cada hogar muestreado representa cientos o miles de hogares similares en la población según los factores de elevación.

## Distribución por decil de ingreso

```python
with DatosMexico() as client:
    deciles = client.enigh.hogares_by_decil()
    for d in deciles:
        print(f"D{d.decil:<2} ${d.ingreso_mediano:>10,.0f}  ({d.hogares_expandido:,} hogares)")
```

[Identidad contable](../conceptos/identidad-contable.md) — la suma de hogares expandidos por decil debe coincidir con `hogares_summary().n_hogares_expandido` ± redondeo.

```python
total = sum(d.hogares_expandido for d in deciles)
ref = client.enigh.hogares_summary().n_hogares_expandido
assert abs(total - ref) / ref < 0.001
```

## Composición de gasto por rubro

```python
with DatosMexico() as client:
    rubros = client.enigh.gastos_by_rubro()
    print(f"{'Rubro':<30} {'Pct':>7}")
    for r in rubros.rubros:
        print(f"{r.nombre:<30} {r.pct:>6.2f}%")
    print(f"{'TOTAL':<30} {sum(r.pct for r in rubros.rubros):>6.2f}%")
```

La suma debe ser 100 % ± 0.01. Si usas `Decimal` (que el SDK usa) la suma da exacta hasta los decimales publicados.

### Comparar gasto entre deciles

```python
with DatosMexico() as client:
    d1 = client.enigh.gastos_by_rubro(decil=1)
    d10 = client.enigh.gastos_by_rubro(decil=10)
    pares = {r.nombre: r.pct for r in d1.rubros}
    for r in d10.rubros:
        diff = r.pct - pares.get(r.nombre, 0)
        print(f"{r.nombre:<30} D1: {pares.get(r.nombre,0):>5.1f}% D10: {r.pct:>5.1f}% Δ: {diff:+5.1f}")
```

El patrón clásico: D1 gasta una proporción mucho mayor en alimentos y vivienda; D10 gasta mucho más en transporte, educación y servicios.

## Hogares por entidad federativa

```python
with DatosMexico() as client:
    resp = client.enigh.hogares_by_entidad()
    for e in sorted(resp.entidades, key=lambda x: x.hogares_expandido, reverse=True)[:10]:
        print(f"{e.nombre:<25} {e.hogares_expandido:>11,.0f}  (mediano ingreso: ${e.ingreso_mediano:>8,.0f})")
```

CDMX, EdoMex, Jalisco y Veracruz suelen estar arriba en valor absoluto.

## Validaciones INEGI — el sello de calidad

```python
with DatosMexico() as client:
    val = client.enigh.validaciones()
    pasa = sum(1 for v in val.cifras if v.passing)
    total = len(val.cifras)
    print(f"Validaciones: {pasa}/{total} passing")
    for v in val.cifras:
        flag = "✓" if v.passing else "✗"
        print(f"  {flag} {v.indicador:<40} obs: {v.valor_observado}  esp: {v.valor_esperado}")
```

El observatorio pre-calcula 13 cifras de referencia que cuadran cifras del API contra publicaciones oficiales del INEGI. Las 13 deben dar `passing=True`. La suite integral del SDK falla si alguna no pasa.

Este es el "sello de calidad" del dataset. Si `validaciones()` devuelve cifras con `passing=False`, ese endpoint específico tiene un problema y conviene esperar antes de usarlo en publicación.

## Demografía

```python
with DatosMexico() as client:
    demo = client.enigh.poblacion_demographics()
    # composición edad/sexo
    for fila in demo.distribucion[:5]:
        print(f"{fila.grupo_edad} {fila.sexo}: {fila.personas:,}")
```

Hay endpoints específicos para actividad económica:

- `enigh.actividad_agro()` — sector agrícola.
- `enigh.actividad_noagro()` — sector no agrícola.
- `enigh.actividad_jcf()` — jefas/jefes de familia (composición laboral).

## Caveats globales del dataset

- **Es una encuesta, no censo**. Las cifras a nivel agregado están construidas vía factores de elevación. Tienen intervalos de confianza implícitos que la API no publica explícitamente.
- **Corte transversal**, no panel. No puedes seguir hogares específicos a lo largo del tiempo con ENIGH.
- **ENIGH 2024 NS** (Nueva Serie) ≠ **ENIGH 2024 Tradicional**. El INEGI publica ambas con cambios metodológicos en captura de ingresos. El dataset del observatorio usa la NS por default. Para comparaciones temporales largas (pre-2022) hay que usar la Tradicional, no expuesta en este endpoint.
- **Ingreso vs gasto**. Los hogares mexicanos típicamente reportan más gasto que ingreso (por sub-reporte de fuentes informales). Cualquier análisis de "ahorro privado" basado solo en ENIGH va a estar sub-estimado.
- **Pesos corrientes 2024**. Para análisis longitudinal con cifras pre-2024 (vía otras fuentes), deflactar.

## Próximos pasos

- [Tutorial cross-dataset](comparativo.md) — combinar ENIGH con CDMX y SAR.
- [Reference completo ENIGH](../reference/enigh.md).
- [Notebook ejemplo](https://github.com/Datos-Mexico/datos-mexico-py/blob/main/examples/04_enigh_hogares_desigualdad.ipynb) — análisis de desigualdad por decil.
