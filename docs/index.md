# datos-mexico

**Cliente Python oficial para la API del [Observatorio Datos México](https://datosmexico.org).**

Acceso programático a microdatos públicos mexicanos curados, validados al peso contra fuentes oficiales, y documentados con sus salvedades metodológicas.

```python
from datos_mexico import DatosMexico

with DatosMexico() as client:
    stats = client.cdmx.dashboard_stats()
    print(f"{stats.total_servidores:,} servidores públicos en CDMX")
```

## Por qué existe

El Observatorio Datos México es un esfuerzo independiente de estudiantes y egresados del ITAM para hacer accesibles, comparables y reproducibles los datos públicos mexicanos. Los microdatos del SAR, ENIGH, padrones de servidores públicos y otros conjuntos están dispersos en formatos heterogéneos, fuentes con cobertura desigual, y publicaciones intermitentes.

La API del observatorio (`api.datos-itam.org`) reprocesa esas fuentes preservando el dato bruto, agregando una capa de validaciones cruzadas (identidades contables, cuadres con publicaciones oficiales) y documentando cada caveat metodológico relevante.

Este SDK es la forma idiomática de consumirla desde Python: tipos Pydantic estrictos, `Decimal` para campos monetarios, cache configurable, retries con backoff exponencial y errores tipados que respetan la jerarquía HTTP. Está pensado para que un investigador, un analista o un periodista de datos pueda escribir un script reproducible sin tener que normalizar respuestas crudas de un endpoint REST.

## Lo que cubre el SDK

El SDK expone 95 operaciones de lectura pública distribuidas en diez namespaces:

| Namespace | Cobertura | Endpoints |
|---|---|---|
| `client.cdmx` | Padrón de servidores públicos del Gobierno de la CDMX | 18 |
| `client.consar` | Sistema de Ahorro para el Retiro (CONSAR/SAR) | 34 |
| `client.enigh` | Encuesta Nacional de Ingresos y Gastos de los Hogares 2024 NS | 10 |
| `client.enoe` | Encuesta Nacional de Ocupación y Empleo (INEGI, 2005T1–2025T1) | 17 |
| `client.comparativo` | Indicadores cross-dataset CDMX × CONSAR × ENIGH | 7 |
| `client.personas` | Tabla normalizada de personas del padrón CDMX | 2 |
| `client.nombramientos` | Tabla normalizada de nombramientos del padrón CDMX | 2 |
| `client.demo` | Dataset didáctico (curso ITAM Bases de Datos) | 3 |
| `client.export` | Descarga CSV cruda del padrón | 1 |
| `client.health()` | Sondeo del backend | 1 |

Cobertura total: **95/114 operaciones** (83 %), 100 % de las lecturas públicas. El 17 % restante corresponde a escrituras administrativas (POST/PUT/DELETE) y endpoints `auth/*`, fuera del alcance del SDK.

## Cómo arrancar

→ [Quickstart](quickstart.md): instalación, primera llamada, manejo de errores y context manager en menos de 10 minutos.

→ [Tutoriales](tutoriales/cdmx.md): walkthroughs narrados por dataset, con caveats explícitos.

→ [Reference](reference/client.md): documentación auto-generada de cada método y modelo desde los docstrings del código.

## Cómo citar

→ [Citación](citation.md): BibTeX, ejemplo en texto académico y CITATION.cff.

## Voz colectiva

Todo lo que publica el Observatorio Datos México sale firmado por el **Equipo de Datos México**, no por personas individuales. Esto incluye este SDK, los notebooks de ejemplo, los caveats redactados en cada endpoint y la documentación que estás leyendo. El equipo es un colectivo de siete personas full-time del ITAM que sostiene el proyecto.

Si encuentras un bug, una imprecisión metodológica o tienes una propuesta de mejora, abre un *issue* en el [repositorio](https://github.com/datos-mexico/datos-mexico-py). Si vas a citar el proyecto en un paper, usa la [forma colectiva de citación](citation.md).
