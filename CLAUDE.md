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
├── _http.py                 ← HttpClient con retries, cache, logging
├── _namespace.py            ← BaseNamespace para todos los namespaces
├── exceptions.py            ← jerarquía completa
├── client.py                ← clase DatosMexico (entry point)
├── models/
│   ├── base.py              ← DatosMexicoModel, ApiResponse, PaginatedResponse[T]
│   ├── cdmx.py              ← modelos CDMX servidores
│   ├── consar.py            ← modelos CONSAR/SAR
│   └── enigh.py             ← modelos ENIGH
└── endpoints/
    ├── cdmx.py              ← CdmxNamespace
    ├── consar.py            ← ConsarNamespace
    └── enigh.py             ← EnighNamespace
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

## Estado actual de cobertura del API (89 endpoints totales)

| Namespace | Endpoints | Estado |
|---|---|---|
| cdmx | 17 | ✅ Completo |
| consar | 34 | ✅ Completo |
| enigh | 10 | ✅ Completo |
| comparativo | 7 | ⏳ Pendiente |
| restantes (auth/me, admin públicos, otros) | ~20 | ⏳ Pendiente |

## Pendientes para próximas sesiones

- [ ] Sub-bloque 5E: namespace comparativo (/api/v1/comparativo/*) +
  endpoints restantes (auth/me, etc.)
- [ ] Sub-bloque 5F: tests integrales + fixtures cross-dataset
- [ ] Sub-bloque 5G: notebooks de ejemplo (4-5 notebooks Jupyter)
- [ ] Sub-bloque 5H: publicar a TestPyPI + validar instalación end-to-end
- [ ] Después de TestPyPI verde: release 0.1.0 a PyPI real
- [ ] Vincular el repo desde el sitio datosmexico.org
- [ ] Actualizar /metodologia del sitio para mencionar el SDK
- [ ] Documentación con mkdocs-material (opcional, después de 0.1.0)
- [ ] Actualizar GitHub Actions a actions/checkout@v5+ (Node.js 20
  deprecation prevista 2026-06-02)

## Endpoints adicionales encontrados pero NO implementados

- `GET /api/v1/servidores/{servidor_id}` — detalle de servidor con campos
  extra. Complementaría servidores_lista() del namespace cdmx.
- `GET /api/v1/catalogos/{tipo}` y `/{tipo}/{item_id}` — endpoints genéricos
  de catálogo (los específicos ya cubren todo lo útil).

## Cosas conocidas del API server-side

- Hay 2 sectores test (id=74 "Sector Test 6A3C4AA8" y id=77 "Sector Test
  B90B5FBA") con datos null en producción. El cliente tolera el null
  gracefully. Conviene cleanup server-side.
- Snapshots requieren día=01 en el parámetro fecha (YYYY-MM-DD). El
  helper _format_fecha lo enforza con ValueError temprano.
- Fecha más reciente CONSAR: 2025-06-01.

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
