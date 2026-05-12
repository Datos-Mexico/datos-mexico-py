# Tutorial — ENOE (mercado laboral mexicano)

El namespace `client.enoe` cubre la **Encuesta Nacional de Ocupación y Empleo** del INEGI, fuente oficial trimestral del mercado laboral en México. Es el dataset más amplio del observatorio: ~101.5 millones de microdatos en cinco tablas (`viv`, `hog`, `sdem`, `coe1`, `coe2`), 76 mil indicadores agregados nacionales y por entidad, y cobertura continua entre 2005T1 y 2025T1 (80 trimestres, con gap documental en 2020T2 por la suspensión COVID).

Los 19 métodos del namespace se agrupan en cuatro familias: **catálogos** y metadata, **indicadores agregados** (serie / snapshot / ranking), **distribuciones** (por sector económico y por posición en la ocupación), y **microdatos** (schema / count / paginación / iter / pandas). El observatorio expone cada respuesta acompañada de sus caveats metodológicos tipados.

## Catálogos y metadata

Empieza por los catálogos para descubrir qué hay disponible: los 13 indicadores, las 32 entidades federativas y las 3 etapas metodológicas.

```python
from datos_mexico import DatosMexico

with DatosMexico() as client:
    cat = client.enoe.indicadores()
    print(f"Indicadores disponibles: {cat.count}")
    for ind in cat.indicadores[:5]:
        print(f"  {ind.slug:<35} ({ind.unidad}) — {ind.nombre}")

    etapas = client.enoe.etapas()
    for e in etapas.etapas:
        print(f"  {e.slug:<18} {e.periodo_inicio} → {e.periodo_fin}  dominio={e.dominio_edad}")
```

Las tres etapas (`clasica` pre-2020T1, `etoe_telefonica` 2020T2, `enoe_n` post-2020T3) marcan cambios de marco muestral. El observatorio reconstruyó la etapa clásica sobre el dominio 15+ uniforme para que toda la serie sea comparable.

## Serie histórica nacional

`serie_nacional()` devuelve una serie temporal completa para cualquiera de los 13 indicadores. El más demandado es `tasa_desocupacion`:

```python
with DatosMexico() as client:
    serie = client.enoe.serie_nacional(indicador="tasa_desocupacion")
    print(f"Cobertura: {serie.cobertura.desde} → {serie.cobertura.hasta} ({serie.cobertura.n_observaciones} trimestres)")
    for p in serie.datos[-8:]:
        print(f"  {p.periodo}  {p.valor:>5.2f}%  ({p.etapa})")
```

El campo `etapa` viene poblado en cada punto de la serie: útil para filtrar antes de comparar cifras pre y post cambio de marco muestral 2020T3.

## Serie por entidad federativa

Para una entidad específica usa la clave INEGI de dos dígitos (CDMX = `"09"`):

```python
with DatosMexico() as client:
    cdmx = client.enoe.serie_entidad(indicador="tasa_desocupacion", entidad_clave="09")
    print(f"{cdmx.entidad_nombre}: {cdmx.cobertura.n_observaciones} trimestres")
    for p in cdmx.datos[-4:]:
        print(f"  {p.periodo}  {p.valor:>5.2f}%")
```

Cruzar la serie de empleo público (`client.cdmx.dashboard_stats()`) con la serie de desempleo ENOE para CDMX es el patrón de combinación cross-dataset más común — ver el [Tutorial CDMX](cdmx.md) y el [Tutorial cross-dataset](comparativo.md).

## Snapshots por periodo

Para una foto de un trimestre — o todos los indicadores nacionales, o todas las entidades para un indicador — usa los métodos `snapshot_*`:

```python
with DatosMexico() as client:
    snap = client.enoe.snapshot_nacional(periodo="2025T1")
    print(f"{snap.periodo} ({snap.etapa}) — {snap.n_indicadores} indicadores:")
    for ind in snap.indicadores[:6]:
        v = f"{ind.valor:>8.2f}" if ind.valor is not None else "       —"
        print(f"  {ind.indicador:<35} {v} {ind.unidad}")

    por_entidad = client.enoe.snapshot_entidad(periodo="2025T1", indicador="tasa_desocupacion")
    top = sorted(por_entidad.datos, key=lambda r: r.valor or -1, reverse=True)[:3]
    for r in top:
        print(f"  {r.entidad_nombre:<28} {r.valor:>5.2f}%")
```

## Ranking — reproducir el boletín INEGI 265/25

`ranking()` ordena las 32 entidades por un indicador y un trimestre. El TOP 5 con `tasa_desocupacion` en 2025T1 reproduce el boletín INEGI 265/25 publicado en mayo 2025:

```python
with DatosMexico() as client:
    r = client.enoe.ranking(periodo="2025T1", indicador="tasa_desocupacion", limit=5)
    print(f"TOP 5 entidades por {r.nombre} — {r.periodo}:")
    for row in r.ranking:
        print(f"  {row.rank}. {row.entidad_nombre:<28} {row.valor:.2f}%")
```

Salida esperada:

```text
1. Tabasco                      4.97%
2. Coahuila de Zaragoza         3.56%
3. Durango                      3.46%
4. Ciudad de México             3.45%
5. Tamaulipas                   3.37%
```

**Caveat**: el ranking exacto reproduce el boletín 265/25 al momento de publicar este SDK (v0.2.0, 2026-05). Si la API recibe revisiones de INEGI en trimestres futuros, las cifras pueden ajustarse marginalmente; los rangos relativos suelen mantenerse estables.

## Distribución por sector económico

12 sectores SCIAN para un periodo nacional, ordenados por participación:

```python
with DatosMexico() as client:
    dist = client.enoe.distribucion_sectorial_snapshot(periodo="2025T1")
    print(f"Ocupados totales {dist.periodo}: {dist.total_ocupados_nivel:,}")
    top = sorted(dist.distribucion, key=lambda r: r.participacion_porcentaje, reverse=True)[:5]
    for r in top:
        print(f"  {r.sector_nombre[:40]:<40} {r.participacion_porcentaje:>5.2f}%  ({r.total_ocupados:>11,})")
```

Para una entidad específica, agregar `nivel="entidad"` y `entidad_clave`. Para serie temporal de un sector concreto, usar `distribucion_sectorial_serie(sector_clave=..., ...)`.

## Distribución por posición en la ocupación

Cuatro categorías (1=subordinados, 2=empleadores, 3=cuenta propia, 4=no remunerados):

```python
with DatosMexico() as client:
    pos = client.enoe.distribucion_posicion_snapshot(periodo="2025T1")
    for r in sorted(pos.distribucion, key=lambda x: x.participacion_porcentaje, reverse=True):
        print(f"  {r.pos_nombre:<22} {r.participacion_porcentaje:>5.2f}%  ({r.total_ocupados:>11,})")
```

La proporción de cuenta propia + no remunerados es un proxy directo de informalidad estructural. Para el indicador formal de informalidad, usa `serie_nacional(indicador="til1")`.

## Microdatos — schema, count, iteración

Para análisis sobre microdatos, primero entiende el schema de la tabla. Las cinco tablas son `viv` (vivienda), `hog` (hogar), `sdem` (sociodemográfica), `coe1` y `coe2` (cuestionario de ocupación):

```python
with DatosMexico() as client:
    schema = client.enoe.microdatos_schema("sdem")
    print(f"Tabla {schema.tabla}: {schema.total_filas:,} filas, {schema.total_columnas} columnas")
    for c in schema.columnas[:6]:
        print(f"  {c.nombre:<18} {c.tipo:<10} nullable={c.nullable}")

    n = client.enoe.microdatos_count("sdem", periodo="2025T1", entidad_clave="09")
    print(f"Microdatos sdem CDMX 2025T1: {n.total:,} filas")
```

Para iterar sin cargar todo a memoria — la paginación corre internamente:

```python
with DatosMexico() as client:
    muestra = list(client.enoe.microdatos_iter(
        "sdem", periodo="2025T1", entidad_clave="09",
        sex=2, eda_min=18,
        limit=500,
    ))
    print(f"Muestreadas {len(muestra)} filas (mujeres 18+ en CDMX 2025T1)")
```

**Caveat**: `include_extras=True` por default (convención Sub-fase 3.10b del observatorio) — el SDK no oculta el `extras_jsonb` con las variables ENOE no promovidas a columna. Si necesitas un payload más ligero, pasa `include_extras=False` explícitamente.

## Microdatos a pandas

Para volúmenes manejables (<100k filas) usa el helper que materializa el iterador en un `DataFrame`. Requiere el extra opcional `pandas`:

```python
# pip install datos-mexico[examples]   # incluye pandas, matplotlib, jupyter

with DatosMexico() as client:
    df = client.enoe.microdatos_to_pandas(
        "sdem", periodo="2025T1", entidad_clave="09", limit=1000,
    )
    print(f"DataFrame: {len(df):,} filas × {len(df.columns)} cols")
    print(f"Edad media (CDMX 2025T1, muestra 1000): {df['eda'].mean():.1f}")
```

Si pandas no está instalado, el helper levanta `ImportError` con el mensaje exacto de instalación. Para volúmenes >100k filas, preferir `microdatos_iter` y procesar por chunks.

## Caveats metodológicos

El observatorio inyecta caveats tipados en cada response que toque una zona delicada. Los cinco a tener en mente:

- **TIL1 (definición operativa)**: la tasa de informalidad laboral del observatorio sigue la definición operativa estándar INEGI; aparece como string en `IndicadorRef.caveat_metodologico` de cada indicador relevante.
- **TCCO redefinición 2020T1** (`redefinicion_tcco_2020T1`): la tasa de condiciones críticas de ocupación cambió su construcción en 2020T1. Series TCCO cross-etapa requieren cautela.
- **Cambio de marco muestral 2020T3 / CPV 2020** (`cambio_marco_2020T3`): la transición al marco del Censo de Población y Vivienda 2020 produjo sub-estimaciones de ~6-7 % en el periodo 2020T3 – 2021T4.
- **Dominio 15+ uniforme** (`dominio_15_plus`): el observatorio reconstruyó la etapa clásica sobre el dominio de 15 años y más para que toda la serie sea comparable; INEGI publicaba originalmente 14+ pre-2014T4.
- **Gap documental 2020T2** (`gap_documental_2020T2`): la ENOE presencial se suspendió por COVID; INEGI levantó una sustitución telefónica (ETOE, etapa `etoe_telefonica`) pero no expone microdatos brutos para ese trimestre.

Los cuatro caveats tipados aparecen como objetos `CaveatMetodologico` en `series`, `rankings` y `microdatos_page`. Imprimir `response.caveats` al inicio de cualquier análisis es buena práctica reproducible.

## Próximos pasos

- [Tutorial cross-dataset](comparativo.md) — combinar ENOE con CDMX y ENIGH.
- [Tutorial ENIGH](enigh.md) — encuesta INEGI análoga (hogares en lugar de personas/empleo).
- [Caveats editoriales](../conceptos/caveats-editoriales.md) — marco general de los caveats en el observatorio.
- [Reference completo ENOE](../reference/enoe.md) — todos los métodos y modelos del namespace.
- [Notebook ejemplo](https://github.com/datos-mexico/datos-mexico-py/blob/main/examples/06_enoe_mercado_laboral.ipynb) — análisis end-to-end con outputs persistidos.
