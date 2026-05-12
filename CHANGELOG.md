# Changelog

Todas las versiones notables del cliente `datos-mexico` quedan documentadas
aquí. El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el versionado adhiere a [SemVer](https://semver.org/lang/es/).

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
