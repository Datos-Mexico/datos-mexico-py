# Peer review externo — FASE 2 del audit del Observatorio Datos México

## 0 · Metadata

| Campo | Valor |
|---|---|
| Fecha del peer review (UTC) | `2026-05-23T22:34:00Z` |
| Auditor externo | Frente SDK del Observatorio Datos México (`Datos-Mexico/datos-mexico-py`) |
| Repo auditor | `Datos-Mexico/datos-mexico-py` @ `33a4f40` (rama `main`) |
| Repo auditado | `DabtcAvila/datos-itam` (privado) |
| Commit auditado | `d1c50122dcdd682b7c414a59f3d1e03b9774bb3a` (`d1c5012`) — squash merge del PR #4 a `main` |
| Fecha del cierre del PR auditado | `2026-05-23T22:03:33Z` (deploy verificado a Railway a las 22:04 UTC) |
| Reporte de cierre del trabajo auditado | `docs/internal/audit-2026-05/fase-2-cierre.md` del repo `DabtcAvila/datos-itam` |
| Spec live auditada | `https://api.datos-itam.org/openapi.json` (277 181 bytes, descargada a las 22:30Z) |
| Snapshot pre-refresh del SDK consultado | `openapi/openapi.snapshot.json` @ `33a4f40` (403 294 bytes) |
| Python del entorno | 3.13.7 |
| Modo de operación | Solo lectura. Sin clonación local del repo auditado; evidencia obtenida vía `gh api` + `curl` a endpoints públicos del runtime. |
| Independencia | El frente SDK no participó en la ejecución de FASE 2; la auditoría es post-hoc, empírica y reproducible. |

---

## 1 · Resumen ejecutivo

FASE 2 del audit del backend del Observatorio Datos México eleva la cobertura documental del contrato API público de 67.5 % a 100 % en descripciones, de 0 % a 100 % en ejemplos por endpoint, y materializa 263 declaraciones nuevas de error responses 4xx no-422. El peer review externo verifica empíricamente las 14 métricas del cierre contra la spec live y encuentra **coincidencia exacta en todas**. Las seis decisiones bifurcadas (A-F) están implementadas exactamente como se acordaron. Cero drift estructural no declarado. Cero violaciones de Camino C. Cero exposición de PII real. Cero firmas de sistemas AI en los 25 commits internos del PR #4, en el squash commit `d1c5012`, en el cuerpo del PR, en los READMEs ni en los reportes. Las tres deudas declaradas en `fase-2-cierre.md` §9 se confirman empíricamente con sus cifras exactas.

**Conteo de hallazgos**: 0 bloqueantes · 2 no-bloqueantes con corrección sugerida · 5 observaciones neutras.

**Veredicto neutral**: FASE 2 es **académicamente sólida**. No se identifican cuestionamientos que invaliden el trabajo ni que requieran rollback. Los dos hallazgos no-bloqueantes son imprecisiones de metadata posteriores al snapshot del documento de cierre (no afectan integridad del contrato). Las observaciones neutras refinan o cuantifican deudas ya registradas, o sugieren refinamientos para fases futuras (no de FASE 2).

**Implicación para el SDK**: el cambio backend no produce breaking change para el SDK 0.2.1. El re-snapshot es seguro de ejecutar. El nuevo campo `status` en `TablaDisponible` es absorbido transparentemente por `extra="allow"` del SDK; tipar el campo de primera clase es trabajo futuro del frente SDK, no del re-snapshot.

---

## 2 · Las 10 dimensiones

### Dimensión 1 — Cobertura métrica reportada vs cobertura real

**Hallazgos** (todos categoría: ✅ coincidencia exacta — observación neutra):

| Métrica | Reportado en `fase-2-cierre.md` §2 | Medido en spec live | Estado |
|---|---|---|---|
| Endpoints totales | 114 | 114 | ✅ |
| Con `description` no vacía | 114 (100 %) | 114 | ✅ |
| Con `summary` | 114 (100 %) | 114 | ✅ |
| Con `example` en alguna response | 114 (100 %) | 114 | ✅ |
| Response 200 | 106 | 106 | ✅ |
| Response 201 | 4 | 4 | ✅ |
| Response 204 | 3 | 3 | ✅ |
| Response 401 | 18 | 18 | ✅ |
| Response 403 | 16 | 16 | ✅ |
| Response 404 | 26 | 26 | ✅ |
| Response 409 | 3 | 3 | ✅ |
| Response 422 | 71 | 71 | ✅ |
| Response 429 | 100 | 100 | ✅ |
| Response 503 | 1 | 1 | ✅ |

Las 14 cifras del cierre coinciden byte-exacto con la spec live deployada.

**Comandos**:

```bash
curl -fsSL https://api.datos-itam.org/openapi.json -o /tmp/openapi-live-post-fase2.json

jq '[.paths | to_entries[] | .value | to_entries[] | .value] as $ops |
{
  total: ($ops | length),
  with_description: ([$ops[] | select((.description // "") | length > 0)] | length),
  with_summary: ([$ops[] | select((.summary // "") | length > 0)] | length),
  with_example: ([$ops[] | select(
    [.responses // {} | to_entries[] | .value.content // {} | to_entries[] | .value | (has("example") or has("examples"))] | any
  )] | length)
}' /tmp/openapi-live-post-fase2.json

jq -r '.paths | to_entries[] | .value | to_entries[] | .value.responses // {} | keys[]' \
  /tmp/openapi-live-post-fase2.json | sort | uniq -c
```

---

### Dimensión 2 — Coherencia decisiones-implementación (A-F)

**Hallazgos** (todos categoría: ✅ implementación correcta — observación neutra):

| ID | Verificación empírica | Estado |
|---|---|---|
| **A — /auth/register** | `summary = "Registro de usuarios — deshabilitado"`; `responses` declara `{403, 422}` (cero 201); el response 403 incluye example explícito con el mensaje real del runtime. | ✅ A.1 aplicada |
| **B — TablaDisponible** | Schema gana campo `status: enum["available","schema-ready","deprecated"]` con `default: "available"` (NO required), `has_data` se conserva como required. Runtime de `/enoe/metadata` confirma: 9 tablas `"available"` + 2 tablas `"schema-ready"` (exactamente `indicadores_area_metropolitana` y `indicadores_anuales_ampliado`). | ✅ B.3 aplicada |
| **C — README raíz** | Cero ocurrencias de las frases prohibidas (`"proyecto académico"`, `"semestre 2026"`, `"programa de"`, `"ITAM Bases de Datos"`, `"el autor"`) en `README.md` y `api/README.md`. Link a `datosmexico.org/quienes-somos` presente, descripción institucional consistente con Camino C. | ✅ C válida |
| **D — CRUD admin** | Muestra de 3 endpoints (`POST /personas/`, `POST /nombramientos/`, `DELETE /personas/{id}`): los tres inician `description` con `[Uso interno administrativo]` y terminan con la nota literal del cierre §5.3 (`"El SDK Python `datos-mexico` no expone este endpoint por ser operacional, no analítico."`). | ✅ D.2 aplicada |
| **E — /admin/refresh-MV** | `summary` arranca con `"[Operacional] "`; `description` contiene literalmente `"no debe consumirse desde producción de forma programática"`. | ✅ E.2 aplicada |
| **F — /health** | `summary: "Liveness probe"`, `description: "Endpoint de salud del servicio. Devuelve 200 si la API está operativa."`, response 200 con `example: {"status": "ok"}`. | ✅ F.1 aplicada |

**Comandos**:

```bash
jq '.paths["/api/v1/auth/register"].post | {summary, codes: .responses | keys}' /tmp/openapi-live-post-fase2.json
jq '.components.schemas.TablaDisponible' /tmp/openapi-live-post-fase2.json
curl -fsSL https://api.datos-itam.org/api/v1/enoe/metadata | jq '.tablas_disponibles[] | select(.status=="schema-ready") | .nombre'
grep -E "proyecto académico|semestre 2026|programa de|ITAM Bases de Datos|el autor" README.md api/README.md  # vacío
jq '.paths["/api/v1/personas/"].post.description' /tmp/openapi-live-post-fase2.json
jq '.paths["/api/v1/admin/refresh-materialized-views"].post | {summary, description}' /tmp/openapi-live-post-fase2.json
jq '.paths["/health"].get' /tmp/openapi-live-post-fase2.json
```

---

### Dimensión 3 — Coherencia constitucional (Camino C)

**Hallazgos** (categoría: observación neutra):

- `info.description` (API_DESCRIPTION global) ya normalizado al texto canónico de Camino C: `"Iniciativa de investigación con respaldo institucional del ITAM. Posicionamiento completo en [datosmexico.org/quienes-somos](https://datosmexico.org/quienes-somos)."`
- Cero ocurrencias de `"proyecto académico"`, `"semestre 2026"`, `"programa de"`, `"el autor"` en TODAS las descriptions y summaries de los 114 endpoints, en `info.description` o en los dos READMEs.
- La **única** ocurrencia de `"ITAM Bases de Datos"` en toda la spec es: `summary` del `GET /api/v1/demo/estudiantes` (`"Lista del curso ITAM Bases de Datos sección 001"`) — coincide exactamente con la excepción registrada en el prompt §1.2 y §4.2 D3 (dataset pedagógico específico). **Cero violaciones no contempladas.**

**Comandos**:

```bash
jq -r '.info.description' /tmp/openapi-live-post-fase2.json | \
  grep -iE "proyecto académico|semestre 2026|programa de|ITAM Bases de Datos|el autor" || echo "OK"

jq -r '[.info.description] +
       [.paths | to_entries[] | .value | to_entries[] | .value | (.summary // ""), (.description // "")]
       | .[]' /tmp/openapi-live-post-fase2.json | \
  grep -inE "proyecto académico|semestre 2026|programa de|el autor"
# → cero matches

jq -r '.paths | to_entries[] | .key as $p | .value | to_entries[] | .key as $m | .value |
       {path: $p, method: $m, summary: (.summary // ""), description: (.description // "")} |
       select((.summary | contains("ITAM Bases de Datos")) or (.description | contains("ITAM Bases de Datos"))) |
       "\(.method | ascii_upcase) \(.path)"' /tmp/openapi-live-post-fase2.json
# → único match: GET /api/v1/demo/estudiantes (excepción aceptada)
```

---

### Dimensión 4 — Atribución académica en commits y artefactos

**Hallazgos** (categoría: observación neutra — cumplimiento):

- Squash commit `d1c5012`: autor `DabtcAvila <100218485+DabtcAvila@users.noreply.github.com>`; mensaje cubre los 25 commits internos del PR; **cero matches** para `claude|opus|co-authored|🤖|generated with|AI assist`.
- 25/25 commits internos del PR #4: autoría `David Fernando Ávila Díaz <df.avila.diaz@gmail.com>` en todos; cero firmas AI en cuerpo de ningún commit.
- Cuerpo del PR #4: cero firmas AI.
- READMEs (raíz y `api/`) y los tres reportes del audit (`fase-1-inventario.md`, `fase-2-plan.md`, `fase-2-cierre.md`): cero atribución a sistemas AI. Los únicos matches de `grep -i "claude"` son:
  - `fase-1-inventario.md:" ./.claude/  (config local de herramientas, untracked)"` — referencia a un directorio gitignored, no atribución de autoría.
  - `fase-2-cierre.md` línea 140 — autodeclaración explícita de "cero menciones de Claude/Co-Authored-By/Generated with/AI" (el grep matchea su propio negativo).

**Comandos**:

```bash
gh api repos/DabtcAvila/datos-itam/commits/d1c5012 | jq -r '.commit | "\(.author.name) <\(.author.email)>", .message' | \
  grep -iE "claude|opus|co-authored|🤖|generated with|AI assist" || echo "OK"

gh api 'repos/DabtcAvila/datos-itam/pulls/4/commits?per_page=30' | \
  jq -r '.[] | "\(.sha[0:7]) | \(.commit.author.name) <\(.commit.author.email)>"'

gh api repos/DabtcAvila/datos-itam/pulls/4 | jq -r '.body' | \
  grep -iE "claude|opus|🤖|co-authored|generated with|AI assist" || echo "OK"

grep -iE "claude|opus|🤖|co-authored|generated with|AI assist" README.md api/README.md \
                                                                docs/internal/audit-2026-05/*.md
```

---

### Dimensión 5 — Disciplina de no-exposición de datos

**Hallazgos** (categoría: observación neutra — cumplimiento):

- **CURPs**: cero matches del regex `[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[A-Z0-9][0-9]` en cualquier example de la spec.
- **RFCs personas (4 letras)**: cero matches.
- **RFCs morales (3 letras)**: cero matches.
- **Nombres + apellidos**: único nombre completo en examples es `"MARIA RODRIGUEZ LOPEZ"` con `id=42`, sueldo redondeado `18500.0`, sector genérico `"Secretaría de Educación"`, puesto genérico `"DOCENTE FRENTE A GRUPO"` → combinación sintética estándar (listada explícitamente en §4.2 D5 del prompt como aceptable).
- Otros campos `"nombre"` encontrados: instituciones (`"Secretaría de Educación"`, `"Procuraduría General de Justicia"`), cargos (`"DIRECTOR EJECUTIVO"`, `"POLICIA"`), entidades federativas (`"Yucatán"`), categorías metodológicas (`"Tasa de desocupación"`), nombres de tablas (`"microdatos_sdem"`, `"indicadores_area_metropolitana"`). Cero datos personales identificables.

**Comandos**:

```bash
jq -r '.. | objects | .example // empty | tostring' /tmp/openapi-live-post-fase2.json | \
  grep -oE '[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[A-Z0-9][0-9]'    # → vacío

jq -r '.. | objects | .example // empty | tostring' /tmp/openapi-live-post-fase2.json | \
  grep -oE '\b[A-ZÑ&]{3,4}[0-9]{6}[A-Z0-9]{3}\b'           # → vacío

jq -r '.. | objects | .example // empty | tostring' /tmp/openapi-live-post-fase2.json | \
  grep -oE '"nombre"[^,}]*' | sort -u                       # inspección manual
```

---

### Dimensión 6 — Coherencia spec ↔ runtime (muestra)

**Hallazgos** (categoría: observación neutra — cumplimiento):

| Endpoint | HTTP | Shape runtime | Coincide con spec | Estado |
|---|---|---|---|---|
| `GET /health` | 200 | `{"status":"ok"}` | exacto | ✅ |
| `POST /api/v1/auth/register` (body válido) | 403 | `{"detail":"Registration is currently disabled..."}` | exacto con example | ✅ |
| `GET /api/v1/dashboard/stats` | 200 | 31 keys camelCase | shape coherente con example | ✅ |
| `GET /api/v1/enoe/metadata` | 200 | 17 keys top-level, idénticas a las del example | exacto | ✅ |
| `GET /api/v1/enigh/metadata` | 200 | 11 keys top-level | responde 200 con shape esperado | ✅ |
| `GET /api/v1/sectores/?per_page=2` | 200 | array de objetos con `{id, nombre, total_servidores, sueldo_bruto_avg, count_hombres, count_mujeres}` | shape coincide con example | ✅ |
| `GET /api/v1/consar/afores` | 200 | `{count: 11, afores: [...]}` | el placeholder genérico no refleja este shape (deuda registrada — ver D7) | ⚠️ deuda registrada |

Cero discrepancias spec ↔ runtime fuera de lo declarado en las deudas. El deploy de Railway aplicó los cambios correctamente.

**Comandos**:

```bash
curl -fsS https://api.datos-itam.org/health
curl -sS -o /dev/null -w 'HTTP %{http_code}\n' -X POST https://api.datos-itam.org/api/v1/auth/register \
  -H 'Content-Type: application/json' -d '{"username":"x","email":"x@y.invalid","password":"abcdefgh"}'
curl -fsS https://api.datos-itam.org/api/v1/dashboard/stats | jq 'keys'
curl -fsS https://api.datos-itam.org/api/v1/enoe/metadata | jq 'keys'
curl -fsS https://api.datos-itam.org/api/v1/sectores/?per_page=2 | jq '.[0]'
curl -fsS https://api.datos-itam.org/api/v1/consar/afores | head -c 300
```

---

### Dimensión 7 — Verificación de las 3 deudas registradas

**Hallazgos** (categoría: observación neutra — deudas confirmadas):

| Deuda | Verificación empírica | Estado |
|---|---|---|
| **1 — Placeholder CONSAR** | 34 de 34 endpoints CONSAR comparten **byte-exacto** el mismo example `{"count":11,"fecha":"2025-06-01","source":"CONSAR — Sistema de Ahorro para el Retiro"}`. La cuantificación del cierre (34 endpoints) es exacta. | ✅ confirmada |
| **2 — Strings runtime en inglés** | Cada una de las 6 strings declaradas aparece exactamente 1 vez en la spec (probablemente vía `$ref` a los HTTPError* schemas centralizados, no duplicada por endpoint). | ✅ confirmada |
| **3 — Examples implícitos** | `GET /api/v1/servidores/{servidor_id}` response 200: declara `description` + `$ref: #/components/schemas/ServidorDetail`, sin `example` explícito. `POST /api/v1/catalogos/{tipo}` response 201: declara `description` + schema vacío, sin `example` explícito. | ✅ confirmada |

**Sub-observación cuantitativa de Deuda 1**: el placeholder CONSAR declara los campos `fecha` y `source`, pero el runtime real de `/consar/afores` devuelve `{count, afores}` (sin `fecha`, sin `source`, con un campo `afores` que el placeholder no anuncia). El placeholder no solo es genérico/desinformativo (como el cierre declara) sino que **describe campos que no existen en runtime**. Sigue dentro del scope ya registrado de la Deuda 1 ("no refleja el shape específico de cada response"), pero el peer review documenta esta cuantificación adicional para informar la priorización de la sub-fase futura.

**Comandos**:

```bash
jq -r '.paths | to_entries[] | select(.key | test("consar")) | .key as $path |
       .value | to_entries[] | .value.responses["200"].content."application/json".example // empty |
       tostring' /tmp/openapi-live-post-fase2.json | sort | uniq -c

for s in "Could not validate credentials" "Admin privileges required" "Rate limit exceeded" \
         "Incorrect username or password" "Cannot delete persona" "Registration is currently disabled"; do
  printf "%-40s : %s\n" "$s" "$(grep -c "$s" /tmp/openapi-live-post-fase2.json)"
done

jq '.paths["/api/v1/servidores/{servidor_id}"].get.responses["200"]' /tmp/openapi-live-post-fase2.json
jq '.paths["/api/v1/catalogos/{tipo}"].post.responses["201"]' /tmp/openapi-live-post-fase2.json
```

---

### Dimensión 8 — Drift estructural snapshot pre-refresh ↔ spec live

**Hallazgos** (categoría: observación neutra — drift coherente con el declarado):

- **Paths**: idénticos. `diff` entre `keys(.paths)` del snapshot pre-refresh y de la spec live → vacío.
- **Combinaciones path + método**: idénticas. `diff` entre listas `\(method) \(path)` → vacío.
- **Parámetros por endpoint**: idénticos. `diff` sobre `{name, in, required}` ordenado → vacío.
- **Schemas nuevos en la spec live (5)**: `HTTPError401`, `HTTPError403`, `HTTPError404`, `HTTPError409`, `HTTPError429` — declarados en `api/app/schemas/errors.py` (cierre §5.1). Esperado por FASE 2.
- **Schema modificado: `TablaDisponible`** — gana campo `status: enum[...]` con `default: "available"`. No es campo `required`, por lo que es **backwards-compatible**. Esperado por Decisión B.

Cero drift estructural fuera de lo declarado. FASE 2 hizo exactamente los cambios que dice haber hecho, ni uno más ni uno menos.

**Comandos**:

```bash
diff <(jq -S '.paths | keys' /tmp/openapi-snapshot-pre-refresh.json) \
     <(jq -S '.paths | keys' /tmp/openapi-live-post-fase2.json)   # → vacío

diff <(jq -S '[.paths | to_entries[] | .key as $p | .value | keys[] | "\(.) \($p)"] | sort' \
      /tmp/openapi-snapshot-pre-refresh.json) \
     <(jq -S '[.paths | to_entries[] | .key as $p | .value | keys[] | "\(.) \($p)"] | sort' \
      /tmp/openapi-live-post-fase2.json)   # → vacío

diff <(jq -S '[.paths | to_entries[] | .key as $p | .value | to_entries[] | .key as $m |
              (.value.parameters // []) | map({name, in, required}) | sort_by(.name) | "\($m) \($p) \(.)"
             ] | sort' /tmp/openapi-snapshot-pre-refresh.json) \
     <(jq -S '... mismo ...' /tmp/openapi-live-post-fase2.json)   # → vacío

diff <(jq -S '.components.schemas | keys' /tmp/openapi-snapshot-pre-refresh.json) \
     <(jq -S '.components.schemas | keys' /tmp/openapi-live-post-fase2.json)
#   → +HTTPError401, +HTTPError403, +HTTPError404, +HTTPError409, +HTTPError429

diff <(jq -S '.components.schemas.TablaDisponible' /tmp/openapi-snapshot-pre-refresh.json) \
     <(jq -S '.components.schemas.TablaDisponible' /tmp/openapi-live-post-fase2.json)
#   → +status (con default, no required) + description expandida
```

---

### Dimensión 9 — Inconsistencias entre los reportes de las dos fases

**Hallazgo 9.A** (categoría: no-bloqueante con corrección sugerida — metadata stale):

`fase-2-cierre.md` §0 declara:

- `Total de commits de la fase: 22 commits granulares (1 plan + 1 resolución decisiones + 1 schemas + 17 routers/health + 2 READMEs)`
- `Commit más reciente del branch: 0e4abc2 — docs(api): README del backend FastAPI`

Pero el PR #4 contiene **25 commits internos**, y el más reciente es `9f477d9` (`docs(audit/fase-2): registrar 3 deudas académicas para fase futura`). Tres commits posteriores a la redacción inicial del cierre no se reflejaron en la metadata:

```
34a4e20 | docs(audit/fase-2): cierre con matriz pre/post + log de decisiones + 22 commits
1618c19 | docs(api/main): normalizar prosa institucional del API_DESCRIPTION según Camino C
9f477d9 | docs(audit/fase-2): registrar 3 deudas académicas para fase futura
```

El `34a4e20` es el commit del propio cierre — autorreferencial, podría justificarse omitirlo. Pero los commits `1618c19` (normalización Camino C en API_DESCRIPTION global, decisión académica relevante) y `9f477d9` (registro de las 3 deudas que vive en §9 del propio documento) deberían reflejarse en la metadata §0 y en la tabla §4. **Sugerencia de corrección**: actualizar `Total de commits` a 25 (o explicitar "22 commits granulares del cuerpo + 3 commits posteriores al snapshot del documento") y actualizar `Commit más reciente del branch` a `9f477d9`.

**Hallazgo 9.B** (categoría: no-bloqueante con corrección sugerida — discrepancia de conteos entre fases):

FASE 1 §2.2 declara distribución por router: `consar 46, enoe 18, enigh 11, comparativo 7, demo 8, catalogos 11, personas 5, nombramientos 5, otros 13`. Suma: **124**. Pero FASE 1 también declara "114 endpoints declarados en código ≡ 114 en spec OpenAPI live". Hay inconsistencia interna de FASE 1 (suma 124 ≠ total 114), no entre fases.

FASE 2 (commit log + Deuda 1 + §5.4) usa cifras distintas: `consar 34, enoe 17, enigh 10`. Verificación empírica contra la spec live:

| Router | FASE 1 | FASE 2 | Empírico (spec live) | Coincide |
|---|---|---|---|---|
| consar | 46 | 34 | **34** | FASE 2 |
| enoe | 18 | 17 | **17** | FASE 2 |
| enigh | 11 | 10 | **10** | FASE 2 |
| comparativo | 7 | 7 | 7 | ambas |
| catalogos | 11 | (NA) | 11 | FASE 1 |
| personas | 5 | (NA) | 5 | FASE 1 |
| nombramientos | 5 | (NA) | 5 | FASE 1 |
| demo (público + admin) | 8 | (NA) | 4 + 4 | FASE 1 |

**FASE 2 está correcta empíricamente** en los conteos donde difiere de FASE 1. La inconsistencia es que FASE 2 **no documenta la reconciliación con FASE 1** (no dice "la cifra correcta es 34, FASE 1 declaró 46 por contar X en lugar de Y"). Una sub-sección de "ajustes vs FASE 1" en `fase-2-cierre.md` aclararía la trazabilidad.

**Hallazgo 9.C** (categoría: observación neutra — hallazgo bloqueante de FASE 1 no mencionado):

FASE 1 §2.1 declara un hallazgo bloqueante de seguridad: credencial Neon hardcoded en historia git. FASE 2 no lo menciona ni siquiera para registrar que sigue pendiente. Es coherente con el scope declarado de FASE 2 (integridad del contrato API público, no security), pero un cierre académicamente completo registraría brevemente "deudas heredadas de FASE 1 que persisten fuera de scope de FASE 2". El prompt §1.3 indica que este hallazgo es riesgo aceptado mientras el repo sea privado y la mitigación queda para fase futura — por lo tanto NO es deuda nueva del peer review, solo se documenta su no-mención.

**Comandos**:

```bash
jq -r 'length' /tmp/pr-4-commits.json   # → 25
jq -r '.[] | "\(.sha[0:7]) | \(.commit.message | split("\n")[0])"' /tmp/pr-4-commits.json

jq -r '
.paths | to_entries[] | .key as $path | .value | to_entries[] | .key as $method | "\($path)|\($method)"
' /tmp/openapi-live-post-fase2.json | \
awk -F'|' '{split($1, a, "/"); router=a[4]; if (router == "") router="root"; count[router]++}
           END {for (r in count) print r, count[r]}' | sort
# → consar 34, enoe 17, enigh 10, ...

grep -iE "credencial|secret|neon.*password|filter-repo|BFG|rotación" \
  docs/internal/audit-2026-05/fase-2-cierre.md   # → vacío
```

---

### Dimensión 10 — Impacto del cambio sobre el SDK Python

**Hallazgos** (categoría: observación neutra — re-snapshot seguro, sub-fase futura posible):

- **Namespaces del SDK alineados con routers backend**: el SDK expone 9 namespaces (`cdmx`, `comparativo`, `consar`, `demo`, `enigh`, `enoe`, `export`, `nombramientos`, `personas`) cubriendo los routers públicos. Los routers que el SDK no expone (`admin`, `analytics`, `auth`, `catalogos`, `dashboard`, `ingest`, `sectores`, `servidores`) corresponden a operaciones administrativas o de uso interno del laboratorio Worker, no del SDK. Coherente con Decisión D (nota explícita en backend).
- **Generación de docstrings**: los docstrings del SDK están escritos a mano en `src/datos_mexico/endpoints/*.py`, no se generan desde el spec. Los cambios de FASE 2 en descriptions/examples del backend no afectan la documentación pública del SDK 0.2.1.
- **Modelo `EnoeTablaInfo` (homólogo del backend `TablaDisponible`)**: declara `{nombre, descripcion, n_filas, has_data}`, sin `status`. El cambio del backend (B.3) añade `status` con default `"available"`. El SDK absorbe el cambio sin breaking change vía `model_config = ConfigDict(strict=True, extra="allow", ...)` en `DatosMexicoModel`. El campo `status` queda aceptado por Pydantic pero **no expuesto como atributo tipado** del modelo. Sub-fase futura del SDK puede tipar el campo (`status: Literal["available", "schema-ready", "deprecated"] = "available"`) si el equipo decide promoverlo a primera clase.
- **5 HTTPError* schemas nuevos del backend**: no son consumidos por el SDK (que maneja errores vía `httpx.HTTPStatusError` y excepciones propias en `exceptions.py`), por lo que el re-snapshot incorporará los schemas en `openapi/openapi.snapshot.json` sin requerir cambios en el código del SDK.
- **Re-snapshot post-FASE-2 es seguro de ejecutar**: cero rotura para el SDK 0.2.1 publicado en PyPI. Es alineación de la referencia interna que el workflow `openapi-drift-cron.yml` consulta.

**Comandos**:

```bash
ls src/datos_mexico/endpoints/   # cdmx, comparativo, consar, demo, enigh, enoe, export, nombramientos, personas
grep -E "class EnoeTablaInfo" src/datos_mexico/models/enoe.py   # → línea 48
sed -n '48,55p' src/datos_mexico/models/enoe.py
sed -n '15,30p' src/datos_mexico/models/base.py   # ConfigDict(extra="allow")
```

---

## 3 · Apéndice A — Comandos completos para reproducir el peer review

```bash
# Setup
curl -fsSL https://api.datos-itam.org/openapi.json -o /tmp/openapi-live-post-fase2.json
cp openapi/openapi.snapshot.json /tmp/openapi-snapshot-pre-refresh.json
gh api -H "Accept: application/vnd.github.raw" \
  repos/DabtcAvila/datos-itam/contents/docs/internal/audit-2026-05/fase-1-inventario.md > /tmp/fase-1-inventario.md
gh api -H "Accept: application/vnd.github.raw" \
  repos/DabtcAvila/datos-itam/contents/docs/internal/audit-2026-05/fase-2-plan.md > /tmp/fase-2-plan.md
gh api -H "Accept: application/vnd.github.raw" \
  repos/DabtcAvila/datos-itam/contents/docs/internal/audit-2026-05/fase-2-cierre.md > /tmp/fase-2-cierre.md
gh api -H "Accept: application/vnd.github.raw" \
  repos/DabtcAvila/datos-itam/contents/README.md > /tmp/datos-itam-readme.md
gh api -H "Accept: application/vnd.github.raw" \
  repos/DabtcAvila/datos-itam/contents/api/README.md > /tmp/datos-itam-api-readme.md
gh api repos/DabtcAvila/datos-itam/commits/d1c5012 > /tmp/d1c5012-commit.json
gh api repos/DabtcAvila/datos-itam/pulls/4 > /tmp/pr-4-metadata.json
gh api 'repos/DabtcAvila/datos-itam/pulls/4/commits?per_page=30' > /tmp/pr-4-commits.json

# D1: cobertura métrica
jq '[.paths | to_entries[] | .value | to_entries[] | .value] as $ops |
{
  total: ($ops | length),
  with_description: ([$ops[] | select((.description // "") | length > 0)] | length),
  with_summary: ([$ops[] | select((.summary // "") | length > 0)] | length),
  with_example: ([$ops[] | select(
    [.responses // {} | to_entries[] | .value.content // {} | to_entries[] | .value | (has("example") or has("examples"))] | any
  )] | length)
}' /tmp/openapi-live-post-fase2.json

jq -r '.paths | to_entries[] | .value | to_entries[] | .value.responses // {} | keys[]' \
  /tmp/openapi-live-post-fase2.json | sort | uniq -c

# D2: decisiones A-F (ver sección 2 dimensión 2 arriba)

# D3: Camino C
jq -r '.info.description' /tmp/openapi-live-post-fase2.json | \
  grep -iE "proyecto académico|semestre 2026|programa de|ITAM Bases de Datos|el autor" || echo OK
jq -r '[.info.description] +
       [.paths | to_entries[] | .value | to_entries[] | .value | (.summary // ""), (.description // "")] | .[]' \
  /tmp/openapi-live-post-fase2.json | grep -inE "proyecto académico|semestre 2026|programa de|el autor"

# D4: atribución
jq -r '.commit.message' /tmp/d1c5012-commit.json | grep -iE "claude|opus|co-authored|🤖|generated with"
jq -r '.[] | "\(.sha[0:7]) | \(.commit.author.name) <\(.commit.author.email)>"' /tmp/pr-4-commits.json
jq -r '.body' /tmp/pr-4-metadata.json | grep -iE "claude|opus|🤖|co-authored|generated with"

# D5: PII
jq -r '.. | objects | .example // empty | tostring' /tmp/openapi-live-post-fase2.json | \
  grep -oE '[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[A-Z0-9][0-9]'
jq -r '.. | objects | .example // empty | tostring' /tmp/openapi-live-post-fase2.json | \
  grep -oE '\b[A-ZÑ&]{3,4}[0-9]{6}[A-Z0-9]{3}\b'

# D6: runtime sampling
curl -fsS https://api.datos-itam.org/health
curl -sS -o /dev/null -w 'HTTP %{http_code}\n' -X POST https://api.datos-itam.org/api/v1/auth/register \
  -H 'Content-Type: application/json' -d '{"username":"x","email":"x@y.invalid","password":"abcdefgh"}'
curl -fsS https://api.datos-itam.org/api/v1/dashboard/stats | jq 'keys'
curl -fsS https://api.datos-itam.org/api/v1/enoe/metadata | jq '.tablas_disponibles[] | select(.status=="schema-ready") | .nombre'
curl -fsS https://api.datos-itam.org/api/v1/sectores/?per_page=2

# D7: deudas registradas
jq -r '.paths | to_entries[] | select(.key | test("consar")) | .key as $p |
       .value | to_entries[] | .value.responses["200"].content."application/json".example // empty | tostring' \
  /tmp/openapi-live-post-fase2.json | sort | uniq -c
for s in "Could not validate credentials" "Admin privileges required" "Rate limit exceeded" \
         "Incorrect username or password" "Cannot delete persona" "Registration is currently disabled"; do
  printf "%-40s : %s\n" "$s" "$(grep -c "$s" /tmp/openapi-live-post-fase2.json)"
done
jq '.paths["/api/v1/servidores/{servidor_id}"].get.responses["200"]' /tmp/openapi-live-post-fase2.json
jq '.paths["/api/v1/catalogos/{tipo}"].post.responses["201"]' /tmp/openapi-live-post-fase2.json

# D8: drift estructural
diff <(jq -S '.paths | keys' /tmp/openapi-snapshot-pre-refresh.json) \
     <(jq -S '.paths | keys' /tmp/openapi-live-post-fase2.json)
diff <(jq -S '[.paths | to_entries[] | .key as $p | .value | keys[] | "\(.) \($p)"] | sort' \
       /tmp/openapi-snapshot-pre-refresh.json) \
     <(jq -S '[.paths | to_entries[] | .key as $p | .value | keys[] | "\(.) \($p)"] | sort' \
       /tmp/openapi-live-post-fase2.json)
diff <(jq -S '.components.schemas | keys' /tmp/openapi-snapshot-pre-refresh.json) \
     <(jq -S '.components.schemas | keys' /tmp/openapi-live-post-fase2.json)
diff <(jq -S '.components.schemas.TablaDisponible' /tmp/openapi-snapshot-pre-refresh.json) \
     <(jq -S '.components.schemas.TablaDisponible' /tmp/openapi-live-post-fase2.json)

# D9: inconsistencias entre fases
jq -r 'length' /tmp/pr-4-commits.json   # → 25
jq -r '.[] | "\(.sha[0:7]) | \(.commit.message | split("\n")[0])"' /tmp/pr-4-commits.json
jq -r '
.paths | to_entries[] | .key as $path | .value | to_entries[] | .key as $method | "\($path)|\($method)"
' /tmp/openapi-live-post-fase2.json | \
awk -F'|' '{split($1, a, "/"); router=a[4]; if (router == "") router="root"; count[router]++}
           END {for (r in count) print r, count[r]}' | sort

# D10: impacto SDK
ls src/datos_mexico/endpoints/
grep -nE "class.*Tabla|class.*Metadata" src/datos_mexico/models/enoe.py
sed -n '15,30p' src/datos_mexico/models/base.py
```

---

## 4 · Apéndice B — Dimensiones no verificables hoy

Cero dimensiones no verificables. El peer review pudo cubrir las 10 dimensiones declaradas en el prompt §4.2 con evidencia empírica directa:

- Spec live: accesible públicamente vía `https://api.datos-itam.org/openapi.json`.
- Repo privado `DabtcAvila/datos-itam`: `gh` autenticado con cuenta `DabtcAvila` (token con scope `repo`), acceso a contents y a metadata de PRs/commits.
- Runtime de endpoints públicos: accesible para los 7 endpoints muestreados en D6.
- Snapshot pre-refresh del SDK: vive localmente en el repo del auditor.

Restricción honrada: cero mutaciones (POST/PUT/DELETE) contra endpoints que pudieran escribir a producción. El único POST muestreado (`/auth/register`) está documentadamente bloqueado en 403, no muta.

---

## 5 · Cross-link

Este reporte es trabajo independiente del frente SDK del Observatorio Datos México auditando externamente FASE 2 del backend. Para trazabilidad bidireccional académica, este artifact debe ser referenciado desde:

- `docs/internal/audit-2026-05/fase-2-cierre.md` del repo `DabtcAvila/datos-itam` — cross-link agregable como sub-sección posterior al cierre.

La actualización del cross-link en el repo backend queda a discreción del operador del observatorio; no es trabajo del frente SDK ni de esta sesión.

---

## 6 · Próximos pasos sugeridos para el operador (recomendación neutral)

Esta sección es trabajo del operador después de leer el reporte, no recomendación normativa.

1. **Si el operador acepta los dos hallazgos no-bloqueantes** (9.A metadata stale, 9.B reconciliación de conteos): un commit pequeño sobre `fase-2-cierre.md` para actualizar §0 (25 commits, último `9f477d9`) y agregar una nota de reconciliación con FASE 1 sobre los conteos. Cierra el ciclo académico de manera limpia.
2. **Decisión sobre el re-snapshot del SDK**: el peer review confirma que es seguro de ejecutar. Sub-fase futura del SDK puede absorber `TablaDisponible.status` como atributo tipado de `EnoeTablaInfo`.
3. **Las 3 deudas declaradas** quedan registradas como están — el peer review las confirma, no las disputa ni cuestiona su categorización.
