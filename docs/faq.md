# FAQ

Preguntas frecuentes con respuestas operativas.

## ¿Qué versión de Python necesito?

Python **3.10 o superior**. El SDK se prueba en CI contra 3.10, 3.11, 3.12 y 3.13.

## ¿Cómo instalo el SDK?

```bash
pip install datos-mexico
```

Para los notebooks de ejemplo (jupyter, pandas, matplotlib): `pip install "datos-mexico[examples]"`. Para construir esta documentación localmente: `pip install "datos-mexico[docs]"`.

## ¿Soporta async / asyncio?

**No.** El SDK usa `httpx` síncrono deliberadamente. Para 99 % de los casos de uso del observatorio (notebooks de análisis, scripts de research, ETLs ad-hoc) async no aporta beneficio neto y sí complica la API. Si tu workflow necesita concurrencia, considera correr el SDK desde un `ThreadPoolExecutor` — la suite integral del SDK valida que cada instancia es segura para usar desde múltiples threads.

## ¿Por qué `Decimal` y no `float`?

Para preservar la exactitud decimal de los microdatos. Sumas de cifras monetarias en `float` acumulan error que para análisis financiero serio es inaceptable. Lectura completa: [Por qué Decimal](conceptos/decimal.md).

## ¿Cómo invalido el cache?

Por llamada (algunos métodos lo aceptan): `client.cdmx.dashboard_stats(use_cache=False)`.

Global: `client.clear_cache()`.

Bajar TTL global a cero al construir: `DatosMexico(cache_ttl=0)`.

→ [Cache y retries](conceptos/cache-retries.md).

## ¿Qué hago si la API no responde?

El SDK reintenta automáticamente con backoff exponencial en errores transitorios (5xx, 429, timeouts, conexión perdida). Por default hace 3 reintentos.

Si después de los reintentos la llamada sigue fallando, levanta `NetworkError` o `ServerError`. Esto es señal de que el problema persiste — verifica https://api.datos-itam.org/docs y reporta en https://github.com/Datos-Mexico/datos-mexico-py/issues si parece estar caído.

## ¿Cómo cito el SDK en mi paper?

Usa el BibTeX de [Citación](citation.md), o el botón "Cite this repository" en el [repo de GitHub](https://github.com/Datos-Mexico/datos-mexico-py) que exporta BibTeX/APA automáticamente desde [`CITATION.cff`](https://github.com/Datos-Mexico/datos-mexico-py/blob/main/CITATION.cff).

## ¿Cómo contribuyo?

Lee [Contribuir](contributing.md). Los reportes de errores en datos van a `errores@datosmexico.org`. Bugs del cliente Python van como issues en GitHub.

## ¿Por qué los caveats editoriales son tan importantes?

Porque el observatorio no publica solo datos — publica datos **con interpretación documentada**. Los caveats son la interpretación del equipo. Si tu análisis los ignora, estás potencialmente sacando conclusiones que el equipo ya marcó como problemáticas. → [Caveats editoriales](conceptos/caveats-editoriales.md).

## ¿Cuál es la fecha más reciente disponible para SAR?

A 2025-06: **2025-06-01**. El observatorio actualiza la serie cuando CONSAR publica nuevos cortes (típicamente con retraso de 2 a 4 meses respecto al mes de referencia).

## ¿Por qué `recursos_por_componente()` devuelve datos jerárquicos?

Porque el SAR mexicano se descompone en niveles (total → RCV/vivienda/voluntarias → IMSS/ISSSTE) que el observatorio publica en una sola estructura plana con un campo `categoria` que indica el nivel de agregación. Sumar todas las filas sin filtrar sobre-cuenta el SAR ~3×. Filtra `categoria in ('component', 'operativo')` para sumas correctas. → [Tutorial CONSAR](tutoriales/consar.md#composicion-del-sar-recursos-por-componente).

## ¿Hay rate limiting?

Sí, prudente. El cache del SDK (default 300s TTL) reduce tráfico significativamente para workflows interactivos típicos. Si tu workflow legítimamente necesita muchas requests, considera bajar el cache o pegarse al `export.csv()` y trabajar localmente.

## ¿Cómo accedo a microdatos individuales de ENOE?

El módulo `enoe` expone tres familias de acceso a microdatos:

```python
# Schema de una tabla
schema = client.enoe.microdatos_schema("sdem")

# Conteo previo con filtros (útil para evitar pulls gigantes)
n = client.enoe.microdatos_count("sdem", periodo="2025T1", entidad_clave="09")

# Iterador síncrono (pagina internamente, no carga todo en memoria)
for row in client.enoe.microdatos_iter(
    "sdem", periodo="2025T1", entidad_clave="09", limit=500,
):
    ...

# Materializar a DataFrame (requiere pandas; instala con datos-mexico[examples])
df = client.enoe.microdatos_to_pandas(
    "sdem", periodo="2025T1", entidad_clave="09", limit=500,
)
```

Las cinco tablas son `viv` (vivienda), `hog` (hogar), `sdem` (sociodemográfica), `coe1` y `coe2` (cuestionario de ocupación y empleo). → [Tutorial ENOE](tutoriales/enoe.md).

## ¿Por qué la ENOE tiene tres "etapas metodológicas"?

Porque la encuesta cambió de marco muestral en 2020T3 (post-CPV 2020) y tuvo una sustitución por ETOE telefónica en 2020T2 durante la suspensión operativa por COVID. El observatorio etiqueta cada cifra con su etapa:

- `clasica` — pre-2020T1, marco muestral del CPV 2010.
- `etoe_telefonica` — 2020T2, suspensión presencial.
- `enoe_n` — post-2020T3, marco muestral del CPV 2020.

Para comparaciones cross-etapa, leer el caveat tipado `cambio_marco_2020T3` que viene en cada response que cruza la frontera. → [Tutorial ENOE — Caveats metodológicos](tutoriales/enoe.md#caveats-metodologicos).

## ¿Por qué hay un gap en 2020T2 sin microdatos ENOE?

Por la suspensión operativa de la ENOE presencial durante la primera ola de COVID-19. INEGI levantó una encuesta telefónica de transición (ETOE) que el observatorio expone como `etapa="etoe_telefonica"`, pero no publica microdatos brutos para ese trimestre. Está documentado con el caveat tipado `gap_documental_2020T2`.

## ¿Hay logs de qué se cachea o qué se reintenta?

Sí, en `DEBUG` level del logger. Configuración:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

→ [Cache y retries — Logging](conceptos/cache-retries.md#logging).
