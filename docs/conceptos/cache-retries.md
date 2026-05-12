# Cache y retries

El SDK trae un comportamiento HTTP por default que protege al usuario de fallos transitorios y al servidor de carga innecesaria. Esta página documenta cómo funciona y cuándo conviene desviarse del default.

## Cache TTL

El cliente mantiene un cache en memoria configurado por TTL (Time-To-Live). Por default cada respuesta exitosa se guarda 300 segundos (5 minutos). Llamadas repetidas dentro del TTL devuelven la respuesta cacheada sin pegar al servidor.

```python
from datos_mexico import DatosMexico

client = DatosMexico(cache_ttl=600)  # 10 minutos en lugar de 5

# Primera llamada — pega al servidor
afores1 = client.consar.afores()

# Segunda llamada dentro de 10 minutos — viene del cache
afores2 = client.consar.afores()

assert afores1 == afores2  # mismo objeto desde cache
```

### Por qué importa el cache

- Notebooks de análisis interactivo: una celda que llama al mismo endpoint cinco veces durante una iteración de exploración no sobrecarga el servidor.
- Suite integral de tests: el cache permite que tests independientes que tocan el mismo endpoint solo paguen el costo de red una vez.
- Workflows largos: si un script encadena 50 llamadas y muchas tocan endpoints comunes (catálogos, `health`), el cache reduce el tiempo total significativamente.

### Cuándo deshabilitarlo

Si tu análisis necesita la respuesta más reciente posible (ej. un workflow programado que corre cada minuto contra un endpoint que actualiza también cada minuto), pasa `use_cache=False` en la llamada o configura `cache_ttl=0` en el constructor.

```python
# Por llamada
afores = client.consar.afores(use_cache=False)

# O global
client = DatosMexico(cache_ttl=0)
```

Para limpiar todo el cache durante una sesión:

```python
client.clear_cache()
```

### Política

- El cache es **por instancia de cliente**. Dos clientes distintos no comparten cache.
- El cache es **thread-safe** dentro de una misma instancia.
- Las claves del cache distinguen entre `get()` (JSON) y `get_text()` (texto crudo) para evitar colisiones — una llamada CSV no sobrescribe el cache de un endpoint JSON paralelo.
- El cache usa solo memoria. No hay persistencia entre runs del proceso.

## Retries con exponential backoff

Toda request HTTP puede fallar transitoriamente: el servidor está saturado un instante, hay un timeout TCP, una respuesta 502/503/504 momentánea, o `429 Too Many Requests`. El SDK reintenta automáticamente con backoff exponencial — para no inundar al servidor cuando ya está bajo presión.

```python
client = DatosMexico(max_retries=3)  # default: 3 reintentos
```

### Lo que se reintenta

- Status codes "transitorios": **429**, **500**, **502**, **503**, **504**.
- Errores de red: timeout TCP, fallo de DNS, connection reset.

### Lo que NO se reintenta

- **400 Bad Request** — el problema es del request, reintentarlo no ayuda. Levanta `BadRequestError`.
- **401 / 403** — auth/permisos. Levanta `AuthenticationError` / `AuthorizationError`.
- **404 Not Found** — el recurso no existe. Levanta `NotFoundError`.
- **409 / 422** — conflicto / unprocessable entity.

Estas distinciones son explícitas para que un error real no se enmascare como retry hasta que se acabe el contador.

### Backoff

Los reintentos usan `tenacity` con `wait_exponential`. Cada intento espera más que el anterior. Después del último intento fallido, levanta la excepción correspondiente (`NetworkError`, `TimeoutError`, `RateLimitError`, `ServerError`).

### Cuándo subirlo

Si tu workflow corre en una red inestable (por ejemplo desde un servidor con conectividad esporádica), subir `max_retries=10` es razonable. El costo es solo tiempo en el peor caso.

### Cuándo bajarlo

Si tienes un workflow muy sensible al tiempo de respuesta y prefieres fallar rápido para reportar el problema, `max_retries=0` deshabilita los reintentos.

## `get_text()` para endpoints non-JSON

La mayoría del API responde JSON. Algunos endpoints (en particular `export.csv()`) devuelven CSV crudo. Internamente, el `HttpClient` expone dos métodos:

- `get(path, params, *, use_cache=True)` — JSON, retorna `dict | list`.
- `get_text(path, params, *, use_cache=True)` — texto crudo, retorna `str`.

Ambos comparten **el mismo pipeline de retries, cache, logging y errores**. La diferencia es solo el parseo final. El método `export.csv()` usa `get_text` y devuelve el body como string; tú decides si parsearlo con `csv.reader`, `pandas.read_csv(StringIO(...))`, o como sea.

```python
from io import StringIO
import pandas as pd
from datos_mexico import DatosMexico

with DatosMexico() as client:
    csv_text = client.export.csv()
    df = pd.read_csv(StringIO(csv_text))
    print(f"Filas: {len(df):,}")
```

## Logging

El cliente acepta un `logger` opcional en el constructor. Por default usa el logger root de Python con nivel `INFO`. Ajusta a `DEBUG` para ver cada request HTTP, cache hits/misses, y reintentos:

```python
import logging

logging.basicConfig(level=logging.DEBUG)

with DatosMexico() as client:
    client.cdmx.dashboard_stats()
```

## Lectura adicional

- [Reference: Cliente](../reference/client.md) — todos los argumentos del constructor.
- [Reference: Excepciones](../reference/exceptions.md) — jerarquía completa de errores.
- El módulo [`_http.py`](https://github.com/Datos-Mexico/datos-mexico-py/blob/main/src/datos_mexico/_http.py) implementa cache + retries + logging.
