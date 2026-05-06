# Contribuir a datos-mexico-py

Pull requests, reportes de errores, y sugerencias son bienvenidos.

## Reportar errores en datos

Si encuentras una cifra que no coincide con la fuente oficial, repórtalo a:

- **Email**: [errores@datosmexico.org](mailto:errores@datosmexico.org)
- **Issue**: [github.com/datos-mexico/datos-mexico-py/issues](https://github.com/datos-mexico/datos-mexico-py/issues) con etiqueta `data-error`

Por favor incluye:

1. Endpoint del cliente que llamaste
2. Cifra que obtuviste
3. Cifra esperada (con link a fuente oficial)
4. Fecha de la consulta

## Reportar bugs del cliente Python

Issues con etiqueta `bug`. Incluye:

1. Versión de Python y de `datos-mexico` (`pip show datos-mexico`)
2. Sistema operativo
3. Código mínimo para reproducir
4. Output esperado vs obtenido

## Contribuir código

1. Fork del repo
2. Crea una rama: `git checkout -b feat/mi-feature`
3. Asegúrate de que pasen los tests: `pytest`
4. Asegúrate de que pase el linter: `ruff check .`
5. Pull request descriptivo

El proyecto sigue [Semantic Versioning](https://semver.org/lang/es/).
