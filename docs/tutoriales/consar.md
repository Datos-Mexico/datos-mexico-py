# Tutorial — SAR (CONSAR)

El namespace `client.consar` cubre el Sistema de Ahorro para el Retiro mexicano: 11 AFOREs activas, recursos administrados, composición por componente (RCV, vivienda, voluntarias), comisiones, traspasos, rendimientos por SIEFORE.

Este tutorial recorre los flujos típicos. La cobertura del dataset son 34 endpoints — aquí se documentan los principales y se enlazan los demás en el [reference](../reference/consar.md).

## AFOREs activas

```python
from datos_mexico import DatosMexico

with DatosMexico() as client:
    resp = client.consar.afores()
    for a in resp.afores:
        print(f"{a.codigo:<6} {a.nombre}")
```

El SAR mexicano tiene 11 AFOREs activas a 2025. La lista cambia ocasionalmente por fusiones / salidas; el endpoint refleja el estado actual.

## Recursos totales — serie histórica

```python
with DatosMexico() as client:
    resp = client.consar.recursos_totales()
    for punto in resp.series[-5:]:
        print(f"{punto.fecha} ${punto.recursos:,.0f}")
```

La serie comienza en mayo de 1998 (inicio del SAR). El campo `fecha_max` te dice hasta qué fecha está actualizado el corte. A 2025 la fecha más reciente es **2025-06-01**.

**Caveat clave**: las cifras están en **pesos corrientes**, no deflactadas. Comparar 1998 vs 2024 directamente sobre-estima el crecimiento real porque mezcla expansión nominal con inflación. Para análisis temporal serio, deflacta usando el INPC del INEGI.

## Composición del SAR — recursos por componente

Aquí está uno de los caveats más importantes del SDK, documentado explícitamente en el docstring del método:

```python
with DatosMexico() as client:
    resp = client.consar.recursos_por_componente(fecha="2025-06-01")
    for fila in resp.componentes:
        print(f"{fila.categoria:<12} {fila.componente:<30} ${fila.recursos:,.0f}")
```

El array `componentes` es **jerárquico**, no plano. Cada fila trae un campo `categoria` con valores en `{'total', 'aggregate', 'component', 'operativo'}`:

- `total` — el total general del SAR para esa fecha.
- `aggregate` — sumas intermedias (ej. RCV total = RCV-IMSS + RCV-ISSSTE).
- `component` — los componentes "hojas" (RCV-IMSS, RCV-ISSSTE, vivienda, voluntarias).
- `operativo` — algunas filas de detalle adicional.

Si sumas todas las filas sin filtrar, **sobre-cuentas el SAR aproximadamente 3×**. Para sumar correctamente:

```python
componentes_validos = [
    c for c in resp.componentes
    if c.categoria in ("component", "operativo")
]
suma = sum(c.recursos for c in componentes_validos)
print(f"Suma componentes: ${suma:,.0f}")
```

Esto está validado por la suite integral del SDK ([`test_data_integrity.py`](https://github.com/datos-mexico/datos-mexico-py/blob/main/tests/integration/test_data_integrity.py)) — si el cuadre se rompe, el test falla.

## IMSS vs ISSSTE

El SAR mexicano tiene dos universos de afiliados. El endpoint `recursos_imss_vs_issste()` los compara:

```python
with DatosMexico() as client:
    cmp = client.consar.recursos_imss_vs_issste()
    print(f"IMSS:    ${cmp.imss.recursos_totales:,.0f}  ({cmp.imss.cuentas:,} cuentas)")
    print(f"ISSSTE:  ${cmp.issste.recursos_totales:,.0f}  ({cmp.issste.cuentas:,} cuentas)")
```

ISSSTE es notablemente más pequeño en cuentas pero el ratio recursos/cuenta es distinto por la composición demográfica (sector público con más antigüedad típica).

## Recursos por AFORE — snapshot

```python
with DatosMexico() as client:
    resp = client.consar.recursos_por_afore(fecha="2025-06-01")
    afores_ord = sorted(resp.afores, key=lambda a: a.recursos, reverse=True)
    for a in afores_ord:
        share = a.recursos / sum(x.recursos for x in resp.afores) * 100
        print(f"{a.codigo:<8} ${a.recursos:>15,.0f}  ({share:5.1f} %)")
```

La distribución típica está concentrada: las 3 AFOREs más grandes suelen sumar más del 60 % del SAR.

**Caveat para snapshots**: la API requiere que `fecha` sea día 01 de un mes (formato `YYYY-MM-01`). El helper `_format_fecha` del SDK enforza esto con un `ValueError` temprano si pasas un día distinto.

## PEA y cotizantes

```python
with DatosMexico() as client:
    resp = client.consar.pea_cotizantes_serie()
    for p in resp.series[-3:]:
        print(f"{p.fecha} PEA: {p.pea:,.0f}  Cotizantes: {p.cotizantes:,.0f}")
```

Útil para calcular tasa de cobertura del SAR sobre la población económicamente activa.

## Comisiones, traspasos, rendimientos

Estos son endpoints más especializados — útiles para análisis comparativo entre AFOREs:

```python
with DatosMexico() as client:
    com = client.consar.comisiones_snapshot(fecha="2025-06-01")
    rend = client.consar.rendimientos_snapshot(fecha="2025-06-01")
    trasp = client.consar.traspasos_snapshot(fecha="2025-06-01")
```

Para los detalles de cada modelo, consulta el [reference de CONSAR](../reference/consar.md).

## Caveats globales del dataset

- **Pesos corrientes** en toda la serie histórica. Deflactar para comparar épocas distintas.
- **Universo SAR ≠ universo ISSSTE-pre-2008**. Los afiliados al esquema previo de ISSSTE no están en este sistema (siguen en el régimen de reparto).
- **Cuentas no son personas**. Una persona puede tener varias cuentas (ej. cuenta SAR-IMSS por trabajo formal + cuenta voluntaria). Sumar cuentas no equivale a sumar personas afiliadas.
- **Voluntarias y vivienda son componentes distintos del retiro**. Para análisis de "ahorro para pensión" el componente RCV es el que importa; vivienda es asignación temporal y voluntarias son aportes discrecionales.

## Próximos pasos

- [Tutorial cross-dataset](comparativo.md) — cobertura SAR vs PEA, aportes vs jubilaciones.
- [Reference completo CONSAR](../reference/consar.md) — los 34 métodos del namespace.
- [Notebook ejemplo](https://github.com/datos-mexico/datos-mexico-py/blob/main/examples/03_sar_composicion.ipynb) — composición histórica con gráficas.
