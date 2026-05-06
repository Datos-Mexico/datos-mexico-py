# CLAUDE.md — Contexto operativo del repositorio

Este archivo documenta el estado, convenciones y patrones del repo
datos-mexico-py para que cualquier nueva sesión de Claude Code pueda
continuar el trabajo sin perder contexto.

## Identidad del proyecto

- **Repo**: datos-mexico/datos-mexico-py
- **Sitio**: https://datosmexico.org
- **API**: https://api.datos-itam.org
- **Contexto institucional**: Observatorio independiente de estudiantes
  y egresados ITAM. Va por el Premio Amafore-ITAM 2026 (deadline 31 julio).
- **Equipo**: 7 personas full-time. Voz colectiva "Equipo de Datos México".

## Stack y decisiones técnicas inmutables

- **Python**: 3.10+ (target principal: 3.11-3.13)
- **HTTP**: httpx síncrono (NO async, NO requests)
- **Tipos**: Pydantic v2 strict
- **Cache**: TTLCache propio en memoria, default 300s, configurable
- **Retries**: tenacity con exponential backoff, 3 intentos default
- **Build**: hatchling
- **Lint**: ruff
- **Type check**: mypy --strict (NO negociable, no usar # type: ignore
  salvo casos justificados en línea)
- **Tests**: pytest + respx (mocking) + integration tests gated por
  DATOS_MEXICO_INTEGRATION_TESTS env var
- **Coverage objetivo**: 95%+ total, 90%+ por módulo

## Convenciones de código

- **Identidad Git**: David Fernando Ávila Díaz <df.avila.diaz@gmail.com>
- **Commits sin firma de Claude**: nunca incluir "Generated with",
  "Co-Authored-By: Claude", emojis, ni atribución del agente
- **Mensajes de commit**: en inglés, sobrios, sin emojis, formato
  "Subject in imperative\n\n- Bullet 1\n- Bullet 2"
- **Decimal para campos monetarios**: NUNCA float. Usar
  BeforeValidator(_to_decimal) que aplica Decimal(str(value))
- **date para fechas**: BeforeValidator(_to_date) que parsea ISO YYYY-MM-DD
- **snake_case en Python, populate_by_name=True** para aceptar
  snake_case y camelCase del API
- **extra="allow"** en model_config (la API puede agregar campos sin
  romper el cliente)
- **Docstrings estilo Google** en todas las clases y métodos públicos
- **Type hints completos** en funciones públicas Y privadas
- **Sin TODOs, FIXMEs, o código comentado** en commits
- **No catchear excepciones genéricas** (BaseException, Exception sin re-raise)

## Arquitectura del SDK

```
src/datos_mexico/
├── __init__.py              ← exports públicos
├── _version.py              ← single source of truth
├── _constants.py            ← BASE_URL, defaults, retryable codes
├── _helpers.py              ← _format_fecha, _to_decimal, _to_date, Money, DateField
├── _cache.py                ← TTLCache con thread safety
├── _http.py                 ← HttpClient con retries, cache, logging, get(), get_text()
├── _namespace.py            ← BaseNamespace para todos los namespaces
├── exceptions.py            ← jerarquía completa
├── client.py                ← clase DatosMexico (entry point)
├── models/
│   ├── base.py              ← DatosMexicoModel, ApiResponse, PaginatedResponse[T], HealthResponse
│   ├── cdmx.py              ← modelos CDMX servidores (incluye ServidorDetail)
│   ├── consar.py            ← modelos CONSAR/SAR
│   ├── enigh.py             ← modelos ENIGH
│   ├── comparativo.py       ← modelos comparativo cross-dataset
│   ├── personas.py          ← modelo Persona (raw padrón CDMX)
│   ├── nombramientos.py     ← modelo Nombramiento (raw padrón CDMX)
│   ├── demo.py              ← modelos demo (curso ITAM)
│   └── export.py            ← (sin modelos, export devuelve CSV crudo)
└── endpoints/
    ├── cdmx.py              ← CdmxNamespace
    ├── consar.py            ← ConsarNamespace
    ├── enigh.py             ← EnighNamespace
    ├── comparativo.py       ← ComparativoNamespace (cross-dataset)
    ├── personas.py          ← PersonasNamespace
    ├── nombramientos.py     ← NombramientosNamespace
    ├── demo.py              ← DemoNamespace
    └── export.py            ← ExportNamespace (CSV vía get_text)
```

## Patrón para agregar nuevos endpoints

1. **Extraer schemas vía OpenAPI primero**:
   ```bash
   curl -s "https://api.datos-itam.org/openapi.json" | python3 -c "..."
   ```
   NO inferir signatures de memoria — siempre verificar el spec real.

2. **Implementar la API real, no el spec del prompt**:
   Si el prompt dice "afore_codigo opcional" pero la API requiere afore_codigo,
   implementar como requerido y reportar la discrepancia.

3. **Tipos Pydantic**:
   - Cada response tiene su modelo dedicado
   - Reusar tipos compartidos cuando aplique (ej. SeriePunto, AforeRef)
   - Decimal para monetarios
   - Optional[X] para campos null en algunos casos

4. **Tests por endpoint**:
   - 1 test mocked con fixture
   - 1 test live gated (sanity check)
   - Tests de validación de parámetros

5. **Coverage**: cada módulo nuevo debe contribuir ≥ 95%

## Patrón para endpoints non-JSON (CSV, XML, archivos)

El `HttpClient` expone `get_text(path, params, *, use_cache=True)` que
reusa el mismo pipeline (retries, cache, errores) pero retorna el body
como `str` sin parseo JSON. Útil para endpoints que devuelven CSV, XML,
plain text, etc. Ejemplo: `ExportNamespace.csv()` lo usa.

No accedas a `self._http._client` directamente desde un namespace. Si
necesitas un nuevo método de transporte (ej. `get_bytes` para binarios),
agrégalo como método público a `HttpClient` siguiendo el patrón de
`get_text`: extraer la parte común vía el helper privado
`_execute_request()` y mantener cache key con prefijo distinto
(`GET:` vs `GET_TEXT:`) para evitar colisiones.

## Estado actual de cobertura del API (97 operaciones totales)

| Namespace | Endpoints | Estado |
|---|---|---|
| cdmx | 18 | ✅ Completo (incluye servidor_detail) |
| consar | 34 | ✅ Completo |
| enigh | 10 | ✅ Completo |
| comparativo | 7 | ✅ Completo |
| personas | 2 | ✅ Completo |
| nombramientos | 2 | ✅ Completo |
| demo | 3 | ✅ Completo |
| export | 1 | ✅ Completo |
| health | 1 | ✅ Completo (root client) |
| restantes (admin writes / auth) | 19 | ⏳ Out of scope |

**Cobertura total**: 78/97 operaciones (80.4%), **100% de lectura pública**.
El 19.6% restante son escrituras admin (POST/PUT/DELETE) o endpoints
auth-required (`auth/me`, `auth/register`, `auth/token`), fuera de
alcance del SDK.

## Pendientes para próximas sesiones

- [ ] Sub-bloque 5G: notebooks de ejemplo (4-5 notebooks Jupyter)
- [ ] Sub-bloque 5H: publicar a TestPyPI + validar instalación end-to-end
- [ ] Después de TestPyPI verde: release 0.1.0 a PyPI real
- [ ] Vincular el repo desde el sitio datosmexico.org
- [ ] Actualizar /metodologia del sitio para mencionar el SDK
- [ ] Documentación con mkdocs-material (opcional, después de 0.1.0)
- [ ] Actualizar GitHub Actions a actions/checkout@v5+ (Node.js 20
  deprecation prevista 2026-06-02)

## Endpoints deliberadamente NO implementados (out of scope)

- **Escrituras admin** (POST/PUT/DELETE en `/api/v1/admin/*`,
  `/api/v1/catalogos/{tipo}`, `/api/v1/personas/`, `/api/v1/nombramientos/`,
  `/api/v1/demo/estudiantes/{id}/toggle-bono`, `/api/v1/ingest/csv`):
  fuera del alcance del SDK de lectura pública.
- **Auth** (`GET /api/v1/auth/me`, `POST /api/v1/auth/register`,
  `POST /api/v1/auth/token`): el SDK no maneja autenticación con tokens
  de usuario; los endpoints de lectura pública no la requieren.

Si en el futuro se decide soportar admin/auth, añadir un namespace
dedicado `auth` y opcionalmente `admin`, y extender `HttpClient` con
soporte para Bearer tokens.

## Cosas conocidas del API server-side

- Hay 2 sectores test (id=74 "Sector Test 6A3C4AA8" y id=77 "Sector Test
  B90B5FBA") con datos null en producción. El cliente tolera el null
  gracefully. Conviene cleanup server-side.
- Snapshots requieren día=01 en el parámetro fecha (YYYY-MM-DD). El
  helper _format_fecha lo enforza con ValueError temprano.
- Fecha más reciente CONSAR: 2025-06-01.
- `consar.recursos_por_componente()` devuelve datos **jerárquicos**, no
  una partición plana. El array `componentes` mezcla rows con
  `categoria` en `{'total', 'aggregate', 'component', 'operativo'}`.
  Para sumar componentes correctamente filtrar por
  `categoria in ('component', 'operativo')`. Sumar todas las filas
  sobre-cuenta el SAR ~3x. Documentado en el docstring del método y
  validado por `tests/integration/test_data_integrity.py`.

## Tests integrales

El proyecto tiene dos suites:

- **Tests unitarios** (rápidos, mocked con `respx`): ~2 segundos.
  ```bash
  pytest tests/
  ```
  CI corre solo esto. Default sin env var.

- **Tests integrales** (lentos, contra API real, gated): ~60–90 segundos.
  ```bash
  DATOS_MEXICO_INTEGRATION_TESTS=1 pytest tests/integration/
  ```
  Requiere conectividad a https://api.datos-itam.org. CI no los corre.

- Excluir explícitamente integrales: `pytest tests/ -m "not integration"`.

Los tests integrales (`tests/integration/`, 27 tests en 6 módulos)
validan:

- **Lifecycle del cliente**: context manager, close idempotente,
  instancias múltiples independientes, User-Agent canónico.
- **Cross-namespace workflows**: full observatory overview (cdmx +
  consar + enigh + comparativo en una sola sesión), namespace isolation,
  chained calls (sectores → servidor_detail; persona → nombramientos).
- **Identidades contables**: SAR componentes ≈ por_afore, ENIGH deciles
  particionan el universo, rubros de gasto suman 100%, monotonía
  temporal de la serie SAR.
- **Validaciones INEGI**: las 13 cifras del observatorio cuadran con
  las publicadas por INEGI (todas `passing=True`).
- **Cache cross-endpoint**: keys distintos para `get()` vs `get_text()`,
  `use_cache=False`, `clear_cache()`.
- **Propagación de errores**: 404 consistente cross-namespace,
  `ValidationError` con diagnostics, pcts como `Decimal`.
- **Workflows de investigador**: distribución de servidores CDMX,
  análisis temporal SAR, desigualdad ENIGH por decil, y el flujo
  específico del paper Amafore-ITAM 2026.

**Si un test integral falla, NO modificar el SDK para hacer pasar el
test — eso oculta bugs reales.** Reportar el delta exacto (cifra
obtenida vs cifra esperada) y triagear si la falla es del API, del
SDK, o del test.

## Workflow para sesión nueva de Claude Code

1. Lee este archivo CLAUDE.md primero
2. cd "/Users/davicho/Datos México/datos-mexico-py"
3. source .venv/bin/activate
4. git status (debe estar clean)
5. git pull origin main (sync con remoto)
6. Lee el último commit para entender estado: git log -1
7. Revisa pendientes en este archivo
8. Si arrancas un nuevo namespace, sigue el patrón documentado arriba

## Recursos externos

- API OpenAPI spec: https://api.datos-itam.org/openapi.json
- API Swagger UI: https://api.datos-itam.org/docs
- Repo: https://github.com/datos-mexico/datos-mexico-py
- PyPI: https://pypi.org/project/datos-mexico/ (cuando se publique)
- TestPyPI: https://test.pypi.org/project/datos-mexico/ (en preparación)
