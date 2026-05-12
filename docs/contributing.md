# Contribuir a datos-mexico-py

Pull requests, reportes de errores y sugerencias son bienvenidos. Esta página describe el ciclo de desarrollo del SDK con suficiente detalle para que una persona externa al equipo pueda abrir un PR de calidad la primera vez.

## Reportar errores en datos

Si encuentras una cifra que no coincide con la fuente oficial, no la corrijas en el SDK — el SDK reproduce lo que devuelve la API. Repórtalo:

- **Email**: [errores@datosmexico.org](mailto:errores@datosmexico.org)
- **Issue**: [github.com/Datos-Mexico/datos-mexico-py/issues](https://github.com/Datos-Mexico/datos-mexico-py/issues) con etiqueta `data-error`

Incluye:

1. Endpoint del cliente que llamaste (ej. `client.consar.recursos_totales`).
2. Cifra que obtuviste.
3. Cifra esperada con link a la fuente oficial (INEGI, CONSAR, Datos Abiertos CDMX).
4. Fecha de la consulta — los snapshots se actualizan.

## Reportar bugs del cliente Python

Issues con etiqueta `bug`. Incluye:

1. Versión de Python y de `datos-mexico` (`pip show datos-mexico`).
2. Sistema operativo.
3. Código mínimo para reproducir.
4. Output esperado vs obtenido (con traceback completo si aplica).

## Preparar el entorno de desarrollo

El proyecto usa [uv](https://docs.astral.sh/uv/) para resolución de dependencias y manejo del entorno virtual. El lockfile (`uv.lock`) está versionado para que todo el equipo y CI usen exactamente las mismas versiones.

```bash
git clone https://github.com/Datos-Mexico/datos-mexico-py.git
cd datos-mexico-py
uv sync --all-extras       # crea .venv/ con dev + examples + docs
source .venv/bin/activate
```

`uv sync` instala las dependencias del lockfile sin tocarlo. Si modificas `pyproject.toml` (agregar/quitar/bumpear una dep), corre `uv lock` para regenerar el lockfile, luego `uv sync` de nuevo.

Para verificar que tu lockfile sigue alineado con `pyproject.toml`:

```bash
uv lock --check
```

Esto es lo que CI espera; si falla en local, falla en CI.

## Reproducibilidad del entorno

El repo soporta dos caminos para instalar el entorno de desarrollo, y los dos son tratados como ciudadanos de primera clase:

### Path moderno (recomendado para dev local)

```bash
uv sync --all-extras
source .venv/bin/activate
```

Rápido (descarga paralela, resolución en segundos), usa `uv.lock` como fuente de verdad y mantiene `.venv/` actualizado automáticamente. Es el camino diario del equipo.

### Path estándar (universal y verificable)

```bash
pip install --require-hashes -r requirements-dev.txt
pip install -e . --no-deps
```

Funciona con cualquier `pip` reciente, no requiere `uv` instalado. `--require-hashes` verifica el SHA256 de cada wheel descargada contra el valor congelado en `requirements-dev.txt`; cualquier alteración intermedia (mirror comprometido, mismatch de versión) hace fallar la instalación. Es lo que CI usa en `.github/workflows/tests.yml` y lo que cualquier revisor académico externo puede ejecutar para reproducir el ambiente exacto del lockfile.

### Cuándo regenerar `requirements-dev.txt`

Cada vez que se modifiquen las dependencias del proyecto: agregar/quitar/bumpear una entrada en `pyproject.toml`, o actualizar `uv.lock`. El script auxiliar lo hace en un comando:

```bash
./scripts/sync_requirements.sh
```

Internamente corre `uv lock` para asegurar que el lockfile esté al día, y luego `uv export --format requirements-txt --extra dev --no-emit-project --output-file requirements-dev.txt`. El export excluye al proyecto editable (`-e .`): los workflows lo instalan por separado con `pip install -e . --no-deps` para no re-resolver el árbol completo de deps.

### Por qué ambos paths

`uv` es la herramienta moderna que el equipo usa día a día. Pero un revisor externo, un investigador que no tiene `uv` instalado, o un sistema de CI antiguo no debería necesitar adoptar `uv` para poder reproducir un análisis. `pip --require-hashes -r requirements-dev.txt` es el contrato universal: cualquier intérprete de Python con `pip` puede pararse en el mismo ambiente exacto, con verificación criptográfica de integridad.

## Correr los tests

Hay dos suites con propósitos distintos.

### Tests unitarios

Rápidos, deterministas, sin red. Usan `respx` para mockear `httpx` con fixtures JSON capturadas del API real (`tests/fixtures/`).

```bash
pytest tests/ --ignore=tests/integration
```

Esto es lo que corre en CI en cada push y cada PR. ~12 segundos en una laptop moderna.

Con cobertura:

```bash
pytest tests/ --ignore=tests/integration --cov=datos_mexico --cov-report=term
```

El objetivo del repo es **≥95 % de cobertura total** y **≥90 % por módulo**.

El badge de cobertura en el README es **estático** (hard-coded). El workflow de tests publica `coverage.xml` y `htmlcov/` como artifacts (gated por matrix 3.12) con retention de 30 días, de modo que cualquiera puede descargar el reporte HTML detallado desde el run. Cuando se corta una release, hay que actualizar el porcentaje del badge a mano si cambió notablemente — no usamos Codecov ni un endpoint dinámico para evitar falsos negativos cuando el endpoint cae.

### Tests integrales

Pegan a `api.datos-itam.org` y validan identidades contables, validaciones INEGI, cross-namespace workflows y propagación de errores. Lentos (~60–90 segundos), gated por variable de entorno para evitar que corran sin querer.

```bash
DATOS_MEXICO_INTEGRATION_TESTS=1 pytest tests/integration/
```

Si un test integral falla, **no modifiques el SDK para silenciarlo**. La causa suele ser una de tres: cambio real en la fuente oficial, drift en la API del observatorio, o un bug del SDK. Reporta la cifra obtenida y la esperada en el issue antes de proponer un fix.

### Reproducibilidad del README

Los bloques de código ` ```python ` del `README.md` se validan automáticamente con `tests/test_readme_examples.py`: cada bloque pasa `compile()` en CI, y con `DATOS_MEXICO_INTEGRATION_TESTS=1` también se ejecuta contra la API real. Si la evolución de los modelos Pydantic o de los métodos públicos rompe un ejemplo del README, el test falla antes del merge.

## Lint y type-check

`ruff` y `mypy --strict` son obligatorios en CI; no hay excepciones aceptadas en el código fuente.

```bash
ruff check .
mypy src/
```

`# type: ignore` se acepta solo con un comentario explicando la causa, y solo en líneas donde una librería externa no aporte stubs (ej. `pandas` está marcado como `ignore_missing_imports` en `pyproject.toml`).

## Convención de commits

Los mensajes históricos del repo mezclan dos estilos. Hoy se prefiere el formato de [Conventional Commits](https://www.conventionalcommits.org/) con scope opcional:

```
feat(enoe): SDK v0.2.0 con módulo ENOE
fix(readme): corregir bloque "Uso rápido" que crasheaba con TypeError
docs(examples): actualizar BibTeX del notebook Amafore a v0.2.0
chore: trackear uv.lock para reproducibilidad del environment
test(consar): agregar fixture para precios_gestion_comparativo
```

Prefijos en uso: `feat`, `fix`, `docs`, `chore`, `test`, `refactor`. El scope (entre paréntesis) nombra el módulo o la área tocada — opcional, útil cuando el commit toca un namespace específico.

Estilo del cuerpo del mensaje:

- Subject en imperativo, sin punto final.
- Línea en blanco entre subject y cuerpo.
- Cuerpo en prosa, párrafos cortos, justifica el *por qué* — el *qué* lo dice el diff.
- Sin emojis.
- Sin atribuciones a herramientas (`Generated with X`, `Co-Authored-By: Y`).

## Cómo agregar un nuevo namespace

El flujo típico cuando la API expone un dataset nuevo (ej. una sección `educacion/`):

1. **Verificar el spec**: descarga el `openapi.json` live para tener los paths y schemas reales en mano.

   ```bash
   curl -s https://api.datos-itam.org/openapi.json > /tmp/spec.json
   ```

2. **Definir los modelos Pydantic** en `src/datos_mexico/models/educacion.py`. Convenciones:
   - `snake_case` para nombres de campo en Python; `Field(alias="...")` para mapear el `camelCase` de la API.
   - `Decimal` para campos monetarios (vía el alias `Money`), nunca `float`.
   - `date` (vía `DateField`) para fechas ISO.
   - `Optional[X]` para campos que la API puede devolver null.
   - `model_config = {"extra": "allow"}` heredado vía `DatosMexicoModel` — la API puede agregar campos sin romper el cliente.

3. **Definir el namespace** en `src/datos_mexico/endpoints/educacion.py`. Hereda de `BaseNamespace`. Un método público por endpoint, con docstring estilo Google que incluya ejemplo `>>>`, type hints completos y `return` tipado.

4. **Capturar fixtures** del API real con un script ad-hoc, guardándolas en `tests/fixtures/educacion_*.json`. Esto evita que los tests dependan de la red.

5. **Escribir tests unit** con `respx` mockeando las respuestas. Mínimo:
   - Un test feliz por método público.
   - Tests de validación para parámetros (fechas, IDs).
   - Un test que verifique cómo se cachea la respuesta.

6. **Opcionalmente, integration tests** en `tests/integration/test_educacion_real.py` con asserts sobre identidades contables o cruces con fuente oficial. Estos van marcados con `@pytest.mark.integration`.

7. **Documentar**:
   - `docs/reference/educacion.md` — wrapper de mkdocstrings que renderiza desde docstrings.
   - `docs/tutoriales/educacion.md` — walkthrough narrado, con ejemplos ejecutables.
   - Mencionar en `docs/index.md` y en el README.

8. **PR descriptivo** con motivación, lista de endpoints cubiertos y cualquier discrepancia detectada vs el spec.

## Gestión del drift del OpenAPI spec

El repo versiona un snapshot del spec live en `openapi/openapi.snapshot.json`. Dos workflows de CI vigilan el drift entre ese snapshot y la API en `https://api.datos-itam.org/openapi.json`:

- **Continuo** (`.github/workflows/openapi-drift.yml`) — en cada push a `main` y cada PR. Si detecta drift, deja warning en el run summary, sube el diff como artifact (`openapi-drift-diff`, retention 30 días) y comenta el PR con un diff truncado. **No falla CI**.
- **Cron diario** (`.github/workflows/openapi-drift-cron.yml`) — 09:00 UTC. Si detecta drift, abre o actualiza un issue con label `openapi-drift`. Si el snapshot está sincronizado, cierra automáticamente cualquier issue abierto con esa label.

### Actualizar el snapshot local

Desde la raíz del repo:

```bash
uv run python openapi/update_snapshot.py
```

El script es idempotente: dos ejecuciones consecutivas producen el mismo archivo byte a byte (salvo cambios upstream).

### Qué hacer cuando CI marca drift

1. Revisar el diff (artifact `openapi-drift-diff` o issue automático).
2. Decidir si el SDK absorbe el cambio. La cobertura del SDK es **decisión editorial del equipo**, no una meta mecánica; un endpoint nuevo en la API no obliga a implementarlo en el SDK.
3. Si se absorbe el cambio: implementar lo necesario en el SDK, correr `uv run python openapi/update_snapshot.py`, y commitear ambos diffs en el mismo PR.
4. Si no se absorbe: dejar el issue abierto como registro intencional, o cerrarlo manualmente con justificación.

**Política**: el drift es información, no error. El SDK cubre la lectura pública (95 de 114 operaciones). Las escrituras admin y los endpoints auth-required están deliberadamente fuera de alcance.

## Documentación local

Los docs viven en `docs/` y se publican en [docs.datosmexico.org](https://docs.datosmexico.org) (mkdocs-material en Cloudflare Pages).

Para correr el dev server local:

```bash
mkdocs serve
# → http://127.0.0.1:8000
```

Para validar antes de un PR doc-only:

```bash
mkdocs build --strict
```

`--strict` falla si hay links rotos internos o warnings de mkdocstrings. Si pasa local, pasa el deploy.

## Secretos requeridos por CI/CD

Los workflows automatizados consumen secretos configurados en GitHub (Settings → Secrets and variables → Actions). No están versionados en el repo y deben configurarse una vez por cuenta de organización o por fork que pretenda desplegar.

### `CLOUDFLARE_API_TOKEN`

Token de API de Cloudflare con permiso `Cloudflare Pages: Edit` sobre la cuenta donde vive el proyecto `datos-mexico-docs`. Usado por `.github/workflows/docs-deploy.yml`.

Cómo crearlo:

1. Entrar a `https://dash.cloudflare.com/profile/api-tokens`.
2. **Create Token** → plantilla **Create Custom Token**.
3. Permissions: `Account` → `Cloudflare Pages` → `Edit`.
4. Account Resources: `Include` → la cuenta que aloja el proyecto Pages.
5. Crear el token y copiar el valor (no se vuelve a mostrar).

### `CLOUDFLARE_ACCOUNT_ID`

Identificador numérico de la cuenta Cloudflare. Aparece en el sidebar derecho de `https://dash.cloudflare.com/` al seleccionar la cuenta, o en la URL después de iniciar sesión.

### Cómo configurarlos en el repo

`https://github.com/Datos-Mexico/datos-mexico-py/settings/secrets/actions` → **New repository secret**. Crear ambos con los nombres exactos `CLOUDFLARE_API_TOKEN` y `CLOUDFLARE_ACCOUNT_ID`.

Sin estos secretos, el workflow `docs-deploy.yml` falla al llegar al step de Cloudflare. El resto del CI (tests, lint, drift detection) no los necesita.

## Versionado y releases

El proyecto sigue [Semantic Versioning](https://semver.org/lang/es/):

- **MAJOR** (`X.0.0`) — breaking change en la API pública del SDK (rename de método, cambio de tipo de retorno, deprecación).
- **MINOR** (`0.X.0`) — features nuevas backwards-compatible (nuevo namespace, nuevos métodos).
- **PATCH** (`0.0.X`) — bug fixes, mejoras de docs, actualizaciones internas sin impacto en la superficie pública.

La versión vive en un solo lugar: `src/datos_mexico/_version.py`. `pyproject.toml` la lee dinámicamente vía `hatch.version.path`. `CITATION.cff` y los notebooks que citen versión hay que actualizarlos a mano al cortar release.

Los releases se publican a PyPI vía OIDC Trusted Publishing, sin tokens en el repo. El workflow (`.github/workflows/publish.yml`) se dispara con tags `v*` y corre `build → publish-testpypi → publish-pypi` en serie. Si TestPyPI falla, PyPI no se ejecuta. Una vez verde, se crea el GitHub Release con notas.

Reglas duras al cortar release:

- Nunca reusar un número de versión ya publicado a PyPI; PyPI rechaza re-uploads incluso tras delete.
- Si TestPyPI falla, bumpear la siguiente patch (no intentar arreglar el número "manchado").
- `CHANGELOG.md` se actualiza antes del tag, formato Keep a Changelog.

## Code review

Los PRs requieren OK explícito antes de merge cuando tocan código, workflows o `pyproject.toml`. Los PRs doc-only (cambios únicamente a `.md`) se pueden mergear sin OK explícito dado el bajo riesgo.

Convención de revisión: comentario en español, foco en el *por qué*, no en el *qué*. Si bloquea, decirlo explícitamente; si es sugerencia, prefijar con `nit:` o `sugerencia:`.
