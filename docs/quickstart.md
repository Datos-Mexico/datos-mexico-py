# Quickstart

Onboarding mínimo en 10 minutos. Al terminar tendrás un script funcional que toca tres de los datasets principales y maneja errores correctamente.

Esta guía asume que ya tienes Python 3.10+ y pip instalados.

## 1. Instalación

```bash
pip install datos-mexico
```

El paquete principal no instala dependencias para notebooks ni docs — son extras opcionales:

```bash
pip install "datos-mexico[examples]"   # jupyter, pandas, matplotlib
pip install "datos-mexico[docs]"       # mkdocs-material, mkdocstrings
```

## 2. Primera llamada — health check

```python
from datos_mexico import DatosMexico

client = DatosMexico()
health = client.health()
print(health.status)
# ok
```

`health()` no se cachea: cada invocación pega al servidor. Es útil para validar conectividad antes de un workflow largo.

## 3. Una llamada de cada namespace principal

```python
from datos_mexico import DatosMexico

with DatosMexico() as client:
    stats = client.cdmx.dashboard_stats()
    print(f"CDMX: {stats.total_servidores:,} servidores públicos")

    sar = client.consar.recursos_totales()
    print(f"SAR: serie hasta {sar.fecha_max}")

    enigh = client.enigh.hogares_summary()
    print(f"ENIGH: {enigh.n_hogares_expandido:,} hogares estimados")
```

El SDK devuelve modelos Pydantic — accede a campos con sintaxis de atributo (`stats.total_servidores`) en lugar de `stats['totalServidores']`. Los campos están en `snake_case` independientemente de cómo los publica la API.

## 4. Context manager (recomendado)

Usa siempre `with DatosMexico() as client:` cuando puedas. El bloque cierra el cliente HTTP subyacente, libera las conexiones reutilizadas y garantiza que cualquier socket abierto se devuelva al pool al final.

```python
with DatosMexico() as client:
    afores = client.consar.afores()
    for a in afores.afores[:3]:
        print(a.nombre, a.codigo)
```

Si no puedes usar `with` (por ejemplo dentro de una clase de larga vida), llama a `client.close()` manualmente al terminar. Es idempotente: cerrar dos veces no levanta excepción.

## 5. Manejo básico de errores

El SDK levanta excepciones tipadas. Lo más común es `NotFoundError` (404) cuando pides un identificador que no existe, y `ValidationError` cuando pasas un parámetro mal formado a un método helper.

```python
from datos_mexico import DatosMexico, NotFoundError, ValidationError

with DatosMexico() as client:
    try:
        client.cdmx.sector_stats(sector_id=999_999)
    except NotFoundError as exc:
        print(f"Sector no existe: {exc.status_code} → {exc}")

    try:
        client.consar.recursos_por_afore(fecha="2025-13-99")
    except ValidationError as exc:
        print(f"Parámetro inválido: {exc}")
```

Para capturar cualquier error del SDK sin atrapar excepciones del intérprete, usa la clase base:

```python
from datos_mexico import DatosMexicoError, ApiError

try:
    stats = client.cdmx.dashboard_stats()
except ApiError as e:
    print(f"Error de API: {e.status_code} — {e.endpoint}")
except DatosMexicoError as e:
    print(f"Error: {e}")
```

## 6. Configuración personalizada

```python
client = DatosMexico(
    timeout=60.0,           # segundos por request (default: 30)
    cache_ttl=600,          # segundos en TTLCache (default: 300)
    max_retries=5,          # reintentos en fallos transitorios (default: 3)
)
```

Para deshabilitar el cache en una llamada específica, los métodos relevantes aceptan `use_cache=False`. Para limpiar el cache global del cliente:

```python
client.clear_cache()
```

## Próximos pasos

- [Tutorial CDMX servidores públicos](tutoriales/cdmx.md) — análisis del padrón con caveats.
- [Tutorial CONSAR/SAR](tutoriales/consar.md) — composición del sistema de pensiones.
- [Tutorial ENIGH](tutoriales/enigh.md) — desigualdad de ingreso por decil.
- [Por qué Decimal](conceptos/decimal.md) — fundamento de la decisión de tipos monetarios.
- [Reference completa](reference/client.md) — documentación auto-generada por método.

Si encuentras una cifra que no coincide con la fuente oficial, repórtalo a [errores@datosmexico.org](mailto:errores@datosmexico.org). Más detalles en [Contribuir](contributing.md).
