# Tutorial — CDMX servidores públicos

El namespace `client.cdmx` expone el padrón de personal del Poder Ejecutivo del Gobierno de la Ciudad de México. Es el dataset más rico de los que cubre el observatorio: 246,836 servidores con campos sobre puesto, sector, sueldo bruto y neto, edad, sexo, antigüedad, tipo de contratación.

Este tutorial recorre los flujos típicos de análisis con caveats explícitos en cada paso.

## Catálogo de sectores

El padrón está particionado por sectores del gobierno (Secretaría de Salud, Secretaría de Cultura, Sistema de Aguas, etc.). Empieza obteniendo el catálogo:

```python
from datos_mexico import DatosMexico

with DatosMexico() as client:
    sectores = client.cdmx.sectores()
    for s in sectores[:5]:
        print(f"{s.id:>3} · {s.nombre} ({s.total_servidores:,} servidores)")
```

**Caveat**: la API trae 2 sectores test residuales (id=74 "Sector Test 6A3C4AA8" e id=77 "Sector Test B90B5FBA") con `total_servidores=0`. El SDK los tolera sin error pero conviene filtrarlos en análisis estadísticos. Está documentado server-side y pendiente de cleanup en la API.

```python
sectores_reales = [s for s in sectores if s.total_servidores > 0]
```

## Stats globales

`dashboard_stats()` devuelve los KPIs principales del padrón:

```python
with DatosMexico() as client:
    stats = client.cdmx.dashboard_stats()
    print(f"Total: {stats.total_servidores:,}")
    print(f"Sueldo medio: ${stats.avg_salary:,.2f}")
    print(f"Sueldo mediano: ${stats.median_salary:,.2f}")
```

La diferencia entre media y mediana ya es informativa: en el padrón típico la media supera la mediana en aproximadamente 10–15 % por la cola de altos sueldos. Esto justifica usar mediana cuando reportas un "sueldo típico" y media cuando comparas masa salarial total.

## Distribución salarial

Puedes obtener la lista paginada con `servidores_lista()`:

```python
with DatosMexico() as client:
    pagina = client.cdmx.servidores_lista(per_page=10)
    for r in pagina.data:
        print(f"{r.puesto[:50]:<50} ${r.sueldo_bruto:>12,.2f}")
    print(f"Página {pagina.page} de {pagina.pages} (total: {pagina.total:,})")
```

Para análisis de distribución completa, considera bajarte el padrón en CSV vía `client.export.csv()` y trabajarlo con pandas. La API tiene rate limiting prudente, así que es mejor pegarse uno solo a `export` que iterar miles de páginas.

```python
from io import StringIO
import pandas as pd

with DatosMexico() as client:
    csv_text = client.export.csv()
    df = pd.read_csv(StringIO(csv_text))
    print(df["sueldo_bruto"].describe())
```

## Ranking de puestos y sectores

```python
with DatosMexico() as client:
    top_puestos = client.cdmx.puestos_ranking(limit=10)
    for p in top_puestos:
        print(f"{p.nombre[:50]:<50} n={p.count:>5}  avg sueldo ${p.avg_sueldo:>11,.2f}")

    sectores_rank = client.cdmx.sectores_ranking()
    for s in sectores_rank[:10]:
        print(f"{s.nombre[:50]:<50} n={s.count:>5}  avg sueldo ${s.avg_sueldo:>11,.2f}")
```

Ambos rankings vienen ordenados **por sueldo promedio descendente**, no por cantidad de servidores. Si lo que necesitas es la concentración de cabezas (qué secretarías emplean a más gente), usa `client.cdmx.sectores()` y ordena por `total_servidores`: la Secretaría de Seguridad Ciudadana sola concentra alrededor de 20 % del padrón.

## Brecha por edad

`brecha_edad()` devuelve un corte específico que usa el observatorio para análisis demográfico del padrón:

```python
with DatosMexico() as client:
    rows = client.cdmx.brecha_edad()
    for r in rows:
        print(
            f"{r.bucket_edad:<10} "
            f"M:${r.avg_male:>9,.0f} ({r.count_male:,})  "
            f"F:${r.avg_female:>9,.0f} ({r.count_female:,})  "
            f"Δ:{r.gap_pct:+5.2f}%"
        )
```

**Caveat metodológico**: el grupo de edad y el sueldo promedio están correlacionados con antigüedad (no observada directamente como feature en este corte). Una lectura simplista — "los jóvenes ganan menos que los mayores" — confunde edad con experiencia. El equipo del observatorio expone el corte tal cual; la interpretación es responsabilidad del analista.

## Detalle de un servidor específico

Si necesitas el registro completo de un servidor (ej. para análisis de caso o auditoría):

```python
from datos_mexico import DatosMexico, NotFoundError

with DatosMexico() as client:
    try:
        detalle = client.cdmx.servidor_detail(servidor_id=12345)
        print(detalle.nombre, detalle.puesto, detalle.sueldo_bruto)
    except NotFoundError:
        print("Servidor no existe")
```

## Comparar dos sectores

```python
with DatosMexico() as client:
    cmp = client.cdmx.sectores_compare(a=1, b=2)
    a, b = cmp.sector_a, cmp.sector_b
    print(f"Sector A: {a.nombre}")
    print(f"  Sueldo bruto medio: ${a.sueldo_bruto_avg:,.2f}  (n={a.total_servidores})")
    print(f"Sector B: {b.nombre}")
    print(f"  Sueldo bruto medio: ${b.sueldo_bruto_avg:,.2f}  (n={b.total_servidores})")
    if a.sueldo_bruto_avg and b.sueldo_bruto_avg:
        print(f"Diferencia A − B: ${a.sueldo_bruto_avg - b.sueldo_bruto_avg:+,.2f}")
```

## Caveats globales del dataset

- **Cobertura**: solo Poder Ejecutivo del Gobierno de la Ciudad de México. No incluye Gobierno Federal con sede en CDMX, organismos autónomos locales, ni empresas paraestatales. Si tu análisis necesita "todos los servidores públicos en CDMX", este dataset es un subconjunto.
- **Snapshot**: el padrón es vigente al momento de publicación. No es serie histórica; no puedes hacer "evolución salarial 2020-2024" con este dataset.
- **Nominales**: sueldos están en pesos corrientes mexicanos. Para comparaciones temporales con otros datasets (ej. SAR), considera deflactar.

## Próximos pasos

- [Tutorial CONSAR/SAR](consar.md) — análisis del sistema de pensiones.
- [Tutorial cross-dataset](comparativo.md) — combinar CDMX con SAR y ENIGH.
- [Reference completa CDMX](../reference/cdmx.md) — todos los métodos del namespace.
- [Notebook ejemplo](https://github.com/Datos-Mexico/datos-mexico-py/blob/main/examples/02_cdmx_servidores_publicos.ipynb) — workflow completo en Jupyter.
