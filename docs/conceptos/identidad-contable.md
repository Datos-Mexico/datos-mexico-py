# Identidad contable

Una **identidad contable** es una igualdad que tiene que cumplirse por construcción del dato. Si los componentes de algo suman al total publicado, ahí hay una identidad. Si los deciles particionan al universo, ahí hay otra. Cuando el SDK te entrega un endpoint que descompone una cifra en partes, esas partes deberían cuadrar contra la cifra global — y si no cuadran, es señal de bug, no de azar.

El observatorio expone explícitamente las descomposiciones de varios datasets para que cualquier persona pueda validar las identidades en su propio análisis. La suite de tests integrales del SDK valida estas identidades automáticamente contra el API en producción.

## SAR — componentes vs total

`consar.recursos_por_componente()` devuelve un array de filas con los componentes del Sistema de Ahorro para el Retiro. La suma de los componentes debe aproximar el total reportado por `consar.recursos_totales()` para la misma fecha.

**Caveat importante**: la respuesta es **jerárquica**, no plana. Cada fila trae un campo `categoria` con valores en `{'total', 'aggregate', 'component', 'operativo'}`. Para sumar componentes correctamente, filtra por `categoria in ('component', 'operativo')`. Sumar todas las filas sobre-cuenta el SAR aproximadamente 3× porque incluye agregados intermedios.

```python
from datos_mexico import DatosMexico

with DatosMexico() as client:
    resp = client.consar.recursos_por_componente(fecha="2025-06-01")
    componentes = [
        c for c in resp.componentes
        if c.categoria in ("component", "operativo")
    ]
    suma = sum(c.monto_mxn_mm for c in componentes)
    total = client.consar.recursos_totales().serie[-1].monto_mxn_mm
    diff_pct = abs(suma - total) / total * 100
    print(f"Suma componentes: {suma:,}")
    print(f"Total reportado:  {total:,}")
    print(f"Diferencia: {diff_pct:.4f} %")
```

El cuadre típico está dentro del 0.1 %.

## ENIGH — deciles particionan el universo

`enigh.hogares_by_decil()` devuelve diez filas, una por decil de ingreso. Las propiedades que deben cumplirse:

- La suma de hogares expandidos por decil ≈ total nacional reportado por `enigh.hogares_summary()`.
- Cada decil debe tener una décima parte aproximada del total (la diferencia respecto a 10 % es precisamente lo que hacen los factores de elevación de la encuesta).

```python
with DatosMexico() as client:
    deciles = client.enigh.hogares_by_decil()
    total_decil = sum(d.n_hogares_expandido for d in deciles)
    total_nacional = client.enigh.hogares_summary().n_hogares_expandido
    print(f"Suma deciles: {total_decil:,}")
    print(f"Total ENIGH:  {total_nacional:,}")
```

## ENIGH — gastos por rubro suman 100 %

`enigh.gastos_by_rubro()` devuelve la composición del gasto total por categoría (alimentos, transporte, vivienda, etc.). Cada fila trae un porcentaje. La suma debe ser 100 % ± redondeo.

```python
with DatosMexico() as client:
    rubros = client.enigh.gastos_by_rubro()
    suma_pct = sum(r.pct_del_monetario for r in rubros.rubros)
    print(f"Suma de pct: {suma_pct}")  # ≈ 100.0
```

Aquí es donde [usar `Decimal`](decimal.md) importa: si los porcentajes vienen en `float`, la suma puede dar `99.99999999998` o `100.00000000003` por error de representación. Con `Decimal` la suma da exacto hasta los dígitos publicados.

## CDMX — sectores no se solapan

Aunque el SDK no expone un test directo, la API garantiza que la suma de servidores por sector ≈ total del padrón. Si analizas distribuciones por sector, esta es la identidad que estás asumiendo.

## Validaciones INEGI

El namespace `enigh.validaciones()` devuelve un payload donde el observatorio ya pre-calculó cuadres contra cifras publicadas por INEGI (13 cifras de referencia). Cada fila trae un campo `passing` (`True/False`).

Si **alguna** validación da `passing=False`, eso es noticia: el dato ya no cuadra con la fuente oficial y el endpoint debe revisarse antes de publicar análisis. La suite integral del SDK falla si `passing` no es `True` en las 13.

## Por qué importa

Para reproducibilidad académica, no basta con publicar la cifra agregada — hay que demostrar que la descomposición es consistente. Si en una tabla los componentes no suman al total, la lectora razonable asume que hay un error de cálculo o una omisión metodológica.

El SDK te entrega los componentes para que puedas validar tú misma. El equipo del observatorio ya validó (la suite integral lo hace), pero la garantía de tu análisis depende de que tú también lo hagas si tu paper o reporte se va a defender en revisión por pares.

## Lectura adicional

- [Caveats editoriales](caveats-editoriales.md) — los campos `note`, `narrative`, `caveats` complementan las identidades contables explicando contexto cualitativo.
- [Tutorial ENIGH](../tutoriales/enigh.md) — workflow completo con validaciones INEGI.
- [`tests/integration/test_data_integrity.py`](https://github.com/Datos-Mexico/datos-mexico-py/blob/main/tests/integration/test_data_integrity.py) — implementación de las validaciones automáticas.
