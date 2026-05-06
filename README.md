# datos-mexico-py

Cliente Python oficial para la API del [Observatorio Datos México](https://datosmexico.org).

Acceso programático a microdatos públicos mexicanos curados, validados al peso contra fuentes oficiales, y documentados con sus salvedades metodológicas.

## Datasets disponibles

- **CDMX servidores públicos**: 246,831 servidores · 75 sectores · padrón vigente del Gobierno de la Ciudad de México
- **CONSAR / SAR**: serie histórica 1998–2025 · 11 AFOREs · recursos administrados, composición, comisiones, traspasos
- **ENIGH 2024 Nueva Serie**: 91,414 hogares en muestra · 38.8M expandidos · ingresos, gastos, demografía

Próximamente: tipos comparativos cross-dataset.

## Instalación

```bash
pip install datos-mexico
```

Requiere Python 3.10 o superior.

## Uso rápido

```python
from datos_mexico import DatosMexico

client = DatosMexico()

# CDMX servidores públicos
stats = client.cdmx.dashboard_stats()
print(f"{stats['totalServidores']:,} servidores públicos")

# SAR composición
sar = client.consar.recursos_totales()
print(f"Última fecha: {sar['fecha_max']}")

# ENIGH hogares
hogares = client.enigh.hogares_summary()
print(f"{hogares['n_hogares_expandido']:,} hogares estimados")
```

## Documentación

- **Quickstart**: [docs/quickstart.md](docs/quickstart.md)
- **API completa**: [docs/api/](docs/api/)
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
  url = {https://github.com/datos-mexico/datos-mexico-py},
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
