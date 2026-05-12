# Por qué Decimal

El SDK usa `decimal.Decimal` para todos los campos monetarios y porcentuales. No usa `float`. Esta página explica por qué.

## El problema con `float`

Python (como casi cualquier lenguaje) representa `float` con punto flotante binario IEEE 754. Eso es perfecto para cálculos científicos donde la precisión relativa importa más que la representación decimal exacta — y un desastre cuando lo que estás manejando son **pesos y centavos**.

```python
>>> 0.1 + 0.2
0.30000000000000004
>>> 1234.56 + 0.01
1234.5700000000002
```

Si una nómina suma 246,831 sueldos brutos en `float`, el error acumulado puede alcanzar el orden de los pesos. Si después esa cifra se publica en una nota o un paper, se está reportando un dato técnicamente falso por motivos puramente numéricos. Para el observatorio eso es inaceptable: el dato bruto del padrón está expresado en decimal exacto y debemos preservarlo.

## La solución del SDK

Cada campo monetario o porcentual de cada modelo Pydantic está tipado con un `BeforeValidator` que aplica `Decimal(str(value))`. Esto garantiza dos cosas:

1. La conversión nunca pasa por `float` intermedio. Si el JSON trae `"1234.56"` como string, llega exacto. Si trae `1234.56` como número, se serializa primero a string vía `str()` y luego a `Decimal` — la representación decimal del literal se respeta.
2. Las operaciones aritméticas son exactas hasta donde la precisión permita configurar el contexto de `decimal`.

```python
from datos_mexico import DatosMexico

with DatosMexico() as client:
    rows = client.cdmx.servidores_lista(limit=100)
    total = sum(r.sueldo_bruto for r in rows.rows if r.sueldo_bruto)
    # total es Decimal exacto, no float
    print(total)
```

Dado que el campo `sueldo_bruto` es `Decimal | None`, los tipos se mantienen consistentes en el cálculo y el resultado de `sum(...)` también es `Decimal`.

## Cuándo importa

- **Análisis financiero**: cualquier suma sobre cifras monetarias (sueldos, recursos administrados del SAR, gastos por hogar) requiere precisión decimal.
- **Validaciones contables**: el observatorio publica varios endpoints comparativos cuyas identidades dependen de sumas exactas (componentes ≈ totales del SAR, deciles particionan el universo ENIGH, rubros suman 100 %). Con `float` esos cuadres dan diferencias espurias.
- **Reproducibilidad académica**: si un investigador corre el mismo notebook dos veces y obtiene cifras ligeramente distintas por error de redondeo, no hay forma de defender la metodología.
- **Tablas en reportes**: `Decimal` se imprime con la representación que esperas (`Decimal("1234.56")`) sin sorpresas tipo `1234.5600000000001`.

## Cuándo no importa

- Cálculos donde explícitamente quieres `float` (gráficas matplotlib, `numpy`, modelos estadísticos): convierte tú al borde con `float(valor)`. El SDK no convierte por ti porque la decisión es del usuario, no de la librería.

## Lectura adicional

- [PEP 327 — Decimal Data Type](https://peps.python.org/pep-0327/) explica la motivación para incluir `Decimal` en la stdlib de Python.
- El docstring de [`datos_mexico._helpers`](https://github.com/Datos-Mexico/datos-mexico-py/blob/main/src/datos_mexico/_helpers.py) documenta la implementación de `_to_decimal` y los validators que usan los modelos.
