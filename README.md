# datos-mexico-py

[![PyPI version](https://img.shields.io/pypi/v/datos-mexico.svg)](https://pypi.org/project/datos-mexico/)
[![Python versions](https://img.shields.io/pypi/pyversions/datos-mexico.svg)](https://pypi.org/project/datos-mexico/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/Datos-Mexico/datos-mexico-py/actions/workflows/tests.yml/badge.svg)](https://github.com/Datos-Mexico/datos-mexico-py/actions/workflows/tests.yml)
[![Docs](https://img.shields.io/badge/docs-docs.datosmexico.org-black?logo=materialformkdocs)](https://docs.datosmexico.org)

Cliente Python oficial para la API del [Observatorio Datos México](https://datosmexico.org).

📖 **Documentación completa**: [docs.datosmexico.org](https://docs.datosmexico.org)

Acceso programático a microdatos públicos mexicanos curados, validados al peso contra fuentes oficiales, y documentados con sus salvedades metodológicas.

## Datasets disponibles

- **CDMX servidores públicos**: 246,831 servidores · 75 sectores · padrón vigente del Gobierno de la Ciudad de México
- **CONSAR / SAR**: serie histórica 1998–2025 · 11 AFOREs · recursos administrados, composición, comisiones, traspasos
- **ENIGH 2024 Nueva Serie**: 91,414 hogares en muestra · 38.8M expandidos · ingresos, gastos, demografía
- **ENOE — Mercado laboral INEGI**: 101.5M microdatos · 76 mil indicadores agregados · cobertura 2005T1–2025T1 · nacional + 32 entidades federativas

Además, el namespace `client.comparativo` expone 7 cruces cross-dataset (CDMX × ENIGH × CONSAR) con interpretación y caveats redactados por el observatorio.

## Instalación

```bash
pip install datos-mexico
```

Para ejecutar los notebooks de ejemplo:
```bash
pip install datos-mexico[examples]
```

Requiere Python 3.10 o superior.

## Uso rápido

```python
from datos_mexico import DatosMexico

client = DatosMexico()

# CDMX servidores públicos
stats = client.cdmx.dashboard_stats()
print(f"{stats.total_servidores:,} servidores públicos")

# SAR composición
sar = client.consar.recursos_totales()
print(f"Última fecha: {sar.fecha_max}")

# ENIGH hogares
hogares = client.enigh.hogares_summary()
print(f"{hogares.n_hogares_expandido:,} hogares estimados")

# ENOE — Top 5 estados con mayor desempleo (2025T1)
top5 = client.enoe.ranking(periodo="2025T1", indicador="tasa_desocupacion", limit=5)
for e in top5.ranking:
    print(f"  {e.rank}. {e.entidad_nombre}: {e.valor:.2f}%")
```

### ENOE — mercado laboral mexicano

El módulo `enoe` expone los 101.5M microdatos y 76 mil indicadores agregados
de la Encuesta Nacional de Ocupación y Empleo (INEGI, 2005T1–2025T1).

```python
from datos_mexico import DatosMexico

with DatosMexico() as client:
    # Catálogo de los 13 indicadores agregados disponibles
    catalogo = client.enoe.indicadores()
    for ind in catalogo.indicadores[:3]:
        print(f"  {ind.slug:30s}  {ind.nombre}")

    # Serie nacional histórica de la tasa de desocupación
    serie = client.enoe.serie_nacional(indicador="tasa_desocupacion")
    print(f"Cobertura: {serie.cobertura.n_observaciones} trimestres")
    print(f"Último punto: {serie.datos[-1].periodo} = {serie.datos[-1].valor:.2f}%")

    # Microdatos de CDMX como DataFrame (requiere pandas)
    df = client.enoe.microdatos_to_pandas(
        "sdem", periodo="2025T1", entidad_clave="09", limit=500
    )
    print(f"Muestra CDMX 2025T1: {len(df)} filas × {len(df.columns)} cols")

    # Iterar sin cargar a memoria
    for row in client.enoe.microdatos_iter(
        "sdem", periodo="2025T1", entidad_clave="09", sex=2, eda_min=18
    ):
        # procesar fila a fila
        ...
```

Cada response incluye una lista tipada de `caveats` con las salvedades
metodológicas relevantes: cambio de marco muestral en 2020T3, redefinición
del TCCO en 2020T1, gap documental ETOE en 2020T2, re-cálculo del dominio
15+ en la etapa clásica pre-2020.

## Examples

El directorio [`examples/`](examples/) contiene 5 notebooks Jupyter ejecutables que muestran flujos típicos del SDK con datos reales contra `https://api.datos-itam.org`:

- [`01_quickstart.ipynb`](examples/01_quickstart.ipynb) — onboarding en 10 minutos
- [`02_cdmx_servidores_publicos.ipynb`](examples/02_cdmx_servidores_publicos.ipynb) — análisis del padrón CDMX (distribuciones, top sectores, brecha por edad)
- [`03_sar_composicion.ipynb`](examples/03_sar_composicion.ipynb) — composición del Sistema de Ahorro para el Retiro (serie histórica, AFOREs, componentes, IMSS vs ISSSTE)
- [`04_enigh_hogares_desigualdad.ipynb`](examples/04_enigh_hogares_desigualdad.ipynb) — desigualdad de ingreso por decil ENIGH 2024 NS (composición de gasto D1 vs D10, validaciones INEGI)
- [`05_paper_amafore_workflow.ipynb`](examples/05_paper_amafore_workflow.ipynb) — workflow específico para investigación de pensiones (cross-dataset, paper Amafore-ITAM 2026)
- [`06_enoe_mercado_laboral.ipynb`](examples/06_enoe_mercado_laboral.ipynb) — mercado laboral mexicano según ENOE (desempleo histórico, ranking 32 entidades, composición sectorial, microdatos CDMX)

Para ejecutarlos:

```bash
pip install datos-mexico[examples]
jupyter notebook examples/
```

Cada notebook se renderiza en GitHub con outputs visibles (gráficas y cifras reales).

## Documentación

Documentación profesional en **[docs.datosmexico.org](https://docs.datosmexico.org)**:

- [Quickstart](https://docs.datosmexico.org/quickstart/) — onboarding en 10 minutos
- [Conceptos clave](https://docs.datosmexico.org/conceptos/decimal/) — Decimal, identidad contable, caveats editoriales, cache y retries
- [Tutoriales](https://docs.datosmexico.org/tutoriales/cdmx/) — walkthroughs por dataset (CDMX, CONSAR, ENIGH, ENOE, comparativo)
- [Reference completo](https://docs.datosmexico.org/reference/client/) — auto-generado desde docstrings
- [FAQ](https://docs.datosmexico.org/faq/)

Otros recursos:

- **Ejemplos en notebooks**: [examples/](examples/)
- **Documentación de la API HTTP**: https://api.datos-itam.org/docs

## Salvedades metodológicas

El cliente reproduce los datos tal como los publica la API del observatorio. La API a su vez reprocesa fuentes oficiales (INEGI, CONSAR, Datos Abiertos CDMX) sin alterar microdatos. Cada endpoint documenta sus límites de cobertura, fechas de corte, y validaciones contra fuente primaria.

Para precisiones técnicas profundas sobre cualquier dataset, consultar las fuentes primarias enlazadas en [docs/sources.md](docs/sources.md).

## Cómo citar

Si usas este cliente en una investigación o publicación académica, por favor cita el proyecto:

```bibtex
@software{datos_mexico_py,
  author = {{Equipo de Datos México}},
  title = {datos-mexico-py: Cliente Python para la API del Observatorio Datos México},
  year = {2026},
  publisher = {Datos México},
  url = {https://github.com/Datos-Mexico/datos-mexico-py},
}
```

GitHub también ofrece exportación BibTeX/APA automática desde el botón "Cite this repository" en la página del repo.

## Contribuir

Ver [docs/contributing.md](docs/contributing.md). Pull requests, issues, y reportes de errores en datos son bienvenidos.

## Licencia

MIT — ver [LICENSE](LICENSE).

## Contacto

- Sitio: https://datosmexico.org
- Email general: equipo@datosmexico.org
- Reportes de errores en datos: errores@datosmexico.org
- Prensa y medios: prensa@datosmexico.org

---

*Datos México es un observatorio independiente formado por estudiantes y egresados del Instituto Tecnológico Autónomo de México (ITAM).*
