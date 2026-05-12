# Snapshot del OpenAPI spec

Este directorio versiona el OpenAPI spec de `https://api.datos-itam.org` que
sirve como referencia para el SDK. El snapshot se usa para:

- Detectar cambios en la API que el SDK aún no absorbe (drift).
- Servir como contrato congelado: lo que el SDK soporta a partir de la
  versión del repo apuntada por el último commit que modifique este snapshot.

## Cómo actualizar el snapshot

Desde la raíz del repo:

    uv run python openapi/update_snapshot.py

El script descarga `https://api.datos-itam.org/openapi.json`, normaliza el
JSON (indent=2, claves ordenadas, trailing newline) y escribe a
`openapi/openapi.snapshot.json`. Es idempotente: dos ejecuciones consecutivas
producen el mismo archivo byte a byte (salvo cambios upstream).

El script también acepta una ruta de salida como argumento; CI la usa para
escribir a `/tmp` y comparar contra el snapshot versionado.

## Política de drift

La cobertura del SDK (qué endpoints del API expone como métodos Python) es
una **decisión editorial del equipo**, no una meta de cobertura mecánica.
El drift entre snapshot versionado y API live es **información, no error**:

- Endpoints nuevos en la API → evaluar si pertenecen al alcance del SDK
  (lectura pública vs admin/auth) y decidir si se implementan.
- Cambios de schema en endpoints existentes → revisar si rompen modelos
  Pydantic del SDK y absorber con cuidado.
- Endpoints retirados → considerar deprecación en el SDK.

CI marca el drift en el run summary y deja un artifact con el diff
completo, pero **nunca falla el build por drift**. El cron diario abre o
actualiza un issue con label `openapi-drift` para que el equipo lo
revise; si el drift desaparece, el issue se cierra automáticamente.

Cuando el equipo decida absorber un cambio, corre el script de update,
agrega los cambios necesarios al SDK, y commitea ambos en el mismo PR.
