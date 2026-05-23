# Changelog

Todas las versiones notables del cliente `datos-mexico` quedan documentadas
aquí. El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el versionado adhiere a [SemVer](https://semver.org/lang/es/).

## [Unreleased]

### Changed

- **Snapshot OpenAPI refrescado** (`openapi/openapi.snapshot.json`) tras el cierre de FASE 2 del audit del backend del observatorio (`DabtcAvila/datos-itam@d1c5012`, deploy verificado a producción a las 22:04 UTC del 2026-05-23). El delta es exclusivamente metadata sobre la spec congelada del SDK v0.2.1: cobertura de `description` 67.5 % → 100 %, `example` en al menos una response 0 % → 100 %, 263 declaraciones nuevas de error responses 4xx no-422 (401/403/404/409/429). Cero cambios estructurales (cero nuevos paths, métodos o parámetros). Cinco schemas `HTTPError401/403/404/409/429` agregados como referencias reutilizables; el schema `TablaDisponible` gana un campo `status: Literal["available", "schema-ready", "deprecated"]` con default backwards-compatible, absorbido transparentemente por `extra="allow"` de los modelos del SDK. La spec congelada del SDK v0.2.1 sigue funcional sin breaking change para usuarios existentes; el refresh es alineación de la referencia que `openapi-drift-cron.yml` consulta. Trabajo precedido y respaldado por peer review externo en `audits/2026-05/peer-review-fase-2.md` (0 hallazgos bloqueantes).

Pulido académico integral del SDK sin cambios en la API pública. Cero breaking changes para usuarios existentes. Cambios concentrados en infraestructura de reproducibilidad, metadata académica, sincronización docs↔código, y robustez operacional.

### Added

- **Snapshot OpenAPI versionado** (`openapi/openapi.snapshot.json`, 14,727 líneas) como registro citable del contrato API al momento del release.
- **Detección automática de drift** entre snapshot y API live:
  - Workflow continuo `openapi-drift.yml` en cada push y PR.
  - Workflow cron diario `openapi-drift-cron.yml` con gestión automática de issues.
  - Política: drift es información, no error; CI no falla por drift.
- **Script de actualización del snapshot** `openapi/update_snapshot.py` idempotente.
- **Deploy automático de docs** a Cloudflare Pages (`docs-deploy.yml`) en cada push a main que toque `docs/`, `mkdocs.yml`, o `src/**`.
- **Test de reproducibilidad permanente del README** (`tests/test_readme_examples.py`): extrae bloques de código del README, valida `compile()`, y opcionalmente ejecuta contra la API real.
- **Coverage report como artifact en GitHub Actions** (XML + HTML) con badge en README.
- **`requirements-dev.txt` con hashes SHA256** desde `uv.lock` para reproducibilidad CI universal.
- **Script `scripts/sync_requirements.sh`** para regenerar el lockfile + requirements export.
- **Script `scripts/regen_docs_figures.py`** con tres modos (dry-run, `--apply`, `--verify`) para mantener cifras vivas sincronizadas con la API.
- **Sección "Cortar un release"** en `docs/contributing.md` documentando el proceso completo (10 pasos).
- **Sección "Reproducibilidad del entorno"** en `docs/contributing.md` documentando paths `uv` y `pip --require-hashes`.
- **Sección "Gestión del drift del OpenAPI spec"** en `docs/contributing.md`.
- **Sección "Secretos requeridos por CI/CD"** en `docs/contributing.md`.
- Labels `openapi-drift` y `automated` en el repositorio GitHub para gestión automática de issues por el cron.

### Changed

- **CITATION.cff** consolidada como fuente única de metadata académica según schema CFF 1.2.0; campo `type: software` explicitado.
- **BibTeX canónico** alineado byte a byte en README, `docs/citation.md`, y notebook Amafore. Tipo `@software` (no `@misc`), author corporativo con brace doble `{{Equipo de Datos México}}` para preservar entidad en parsers BibTeX, URL apuntando al repositorio del código, campos completos (`year`, `month`, `version`, `url`, `publisher`, `license`, `note`).
- **README "Uso rápido"** corregido: el primer bloque ya no usa dict-style camelCase incorrecto (`stats['totalServidores']`) sino atributos snake_case correctos (`stats.total_servidores`); ahora corre limpio al copia-pegar.
- **README "Uso rápido"** unificado al patrón context manager `with DatosMexico() as client:` consistente con `docs/quickstart.md`.
- **45 bloques de código en `docs/`** auditados; 30 corregidos para sincronizar con los modelos Pydantic actuales del SDK (tutoriales cdmx, enigh, consar, comparativo; conceptos identidad-contable; tutorial enoe ya estaba sincronizado).
- **Convención de conteo de endpoints** documentada explícitamente: endpoints HTTP (95/114 cubiertos = 83%) como cifra canónica comparable con APIs institucionales, métodos SDK (97 públicos) como aclaración pedagógica donde aporta valor.
- **Workflow `tests.yml`** ahora usa `pip install --require-hashes -r requirements-dev.txt` para reproducibilidad universal en lugar de `pip install -e ".[dev]"` sin lock.
- **Versiones de GitHub Actions** uniformadas: `actions/upload-artifact@v7` en los 5 workflows.
- **Casing canónico Datos-Mexico** en 26 URLs sobre 17 archivos (la organización en GitHub es `Datos-Mexico`, no `datos-mexico`).
- **`docs/contributing.md`** ampliada de 36 a más de 300 líneas con guía completa de desarrollo (setup uv, tests unit + integration, ruff/mypy, cómo agregar un namespace, mkdocs serve, release process OIDC).
- **`docs/tutoriales/cdmx.md`** generalizada la nota sobre sectores test residuales (la API expone sectores con `total_servidores=0` cuya cantidad puede variar entre releases).
- **Cifras frías refrescadas** contra snapshot vigente de la API (servidores CDMX en README y tutorial).
- **`docs/conceptos/comparativo`** y `docs/index.md` con descripción precisa del alcance real de los 7 endpoints de cruce cross-dataset.
- **BibTeX del notebook Amafore** completado con `version`, `month`, `publisher`, `license`, `note` para coincidir con la versión canónica.

### Fixed

- **README ejemplo "Uso rápido"** que crasheaba con `TypeError: 'DashboardStats' object is not subscriptable` al copia-pegar la primera línea de código en una terminal de usuario.
- **Promesas stale en README**: eliminada mención "Próximamente: comparativo cross-dataset" cuando el módulo ya existe desde v0.1.0; agregado ENOE a la lista de walkthroughs.
- **Conteo de notebooks**: corregido de 5 a 6 (off-by-one introducido al agregar el notebook de ENOE).
- **Heading**: corregido `## Examples` a `## Ejemplos` (única sección en inglés en README en español).
- **`docs/api/`** directorio vacío eliminado del filesystem local.
- **`uv.lock`** ahora committeado para reproducibilidad CI verificable.
- **Patrón `.env`** ampliado a `.env*` en `.gitignore` para cubrir variantes futuras.

### Infrastructure

- 38 commits sobre v0.2.0 organizados en 5 fases de pulido (PR #6 y PR #7).
- Cobertura de tests: 99% (1964 sentencias, 29 sin cubrir).
- Suite: 234 passed, 27 skipped (gated por `DATOS_MEXICO_INTEGRATION_TESTS=1`).
- `mypy --strict`, `ruff`: clean en todo el código fuente.

### Notes for citation

`CITATION.cff` actualizada con `version: 0.2.1` y `date-released: 2026-05-13`. Los BibTeX en README, docs y notebook reflejan los mismos campos. Use `cffconvert -f bibtex -i CITATION.cff` para generar la cita canónica, o copie directamente el bloque `@software{datos_mexico_py, ...}` provisto en cualquiera de las tres ubicaciones.

## [0.2.0] — 2026-05-11

### Added

- **Módulo `enoe`** — acceso a la Encuesta Nacional de Ocupación y Empleo
  (INEGI, 2005T1–2025T1) con 19 métodos en `client.enoe.*`:
  - Catálogos y metadata (`health`, `metadata`, `indicadores`, `entidades`,
    `etapas`).
  - Indicadores agregados (`serie_nacional`, `snapshot_nacional`,
    `serie_entidad`, `snapshot_entidad`, `ranking`).
  - Distribuciones (`distribucion_sectorial_snapshot/serie`,
    `distribucion_posicion_snapshot/serie`).
  - Microdatos (`microdatos_schema`, `microdatos_count`, `microdatos_page`,
    `microdatos_iter`, `microdatos_to_pandas`).
- **Cobertura del observatorio expuesta vía SDK**: ~101.5M microdatos en
  cinco tablas (`viv`, `hog`, `sdem`, `coe1`, `coe2`), 76 mil indicadores
  agregados, 32 entidades federativas, 13 indicadores con sus caveats
  metodológicos amarrados.
- **`microdatos_iter`** — generador síncrono que pagina internamente y
  emite filas dict a dict. Acepta `limit` para acotar muestras sin
  modificar el resto de filtros.
- **`microdatos_to_pandas`** — helper opcional (requiere `pandas`) que
  materializa la iteración en un `DataFrame`. `pandas` queda en el extra
  `examples`; el resto del SDK no tiene nueva dependencia obligatoria.
- **`include_extras=True` por default** en `microdatos_page` /
  `microdatos_iter` / `microdatos_to_pandas`: el SDK no oculta el
  `extras_jsonb` con las variables ENOE no promovidas a columna
  (convención Sub-fase 3.10b del observatorio).
- **Caveats tipados** (`CaveatMetodologico`) en cada response que aplique:
  `cambio_marco_2020T3`, `redefinicion_tcco_2020T1`, `dominio_15_plus`,
  `gap_documental_2020T2`.
- **Notebook ejemplo** [`examples/06_enoe_mercado_laboral.ipynb`](examples/06_enoe_mercado_laboral.ipynb):
  desempleo histórico, ranking de 32 entidades (incl. el TOP-5 que reproduce
  exactamente el boletín INEGI 265/25), composición sectorial 2025T1 y
  análisis ponderado de edad sobre microdatos CDMX.
- **31 tests con `respx` mocks** + 2 tests de integración (gated por
  `DATOS_MEXICO_INTEGRATION_TESTS=1`) que reproducen el ranking INEGI
  265/25 contra el API en vivo.

### Notes

- El módulo `enoe` adopta el contrato `entidad_clave` canónico
  (Sub-fase 3.10c del backend): el SDK siempre envía `entidad_clave`,
  nunca el alias deprecated `entidad`.
- Diseño síncrono consistente con el resto del SDK (`httpx.Client`
  con retries y caché). La pagination corre internamente; el caller
  ve un generator estándar.

## [0.1.0] — 2026-05-06

Primer release público a PyPI con tres datasets:

- CDMX servidores públicos (246,831 servidores).
- CONSAR / SAR (serie 1998–2025, 11 AFOREs).
- ENIGH 2024 Nueva Serie (91,414 hogares en muestra, 38.8M expandidos).
