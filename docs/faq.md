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

Si después de los reintentos la llamada sigue fallando, levanta `NetworkError` o `ServerError`. Esto es señal de que el problema persiste — verifica https://api.datos-itam.org/docs y reporta en https://github.com/datos-mexico/datos-mexico-py/issues si parece estar caído.

## ¿Cómo cito el SDK en mi paper?

Usa el BibTeX de [Citación](citation.md), o el botón "Cite this repository" en el [repo de GitHub](https://github.com/datos-mexico/datos-mexico-py) que exporta BibTeX/APA automáticamente desde [`CITATION.cff`](https://github.com/datos-mexico/datos-mexico-py/blob/main/CITATION.cff).

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

## ¿Hay logs de qué se cachea o qué se reintenta?

Sí, en `DEBUG` level del logger. Configuración:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

→ [Cache y retries — Logging](conceptos/cache-retries.md#logging).
