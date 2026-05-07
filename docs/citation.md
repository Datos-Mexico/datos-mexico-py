# Citación

Si usas este SDK en una investigación, reporte o publicación académica, por favor cita el proyecto.

## BibTeX

```bibtex
@software{datos_mexico_py,
  author    = {{Equipo de Datos México}},
  title     = {datos-mexico-py: Cliente Python para la API del Observatorio Datos México},
  year      = {2026},
  version   = {0.1.0},
  publisher = {Datos México},
  url       = {https://github.com/datos-mexico/datos-mexico-py},
  note      = {Documentación: https://docs.datosmexico.org}
}
```

## En texto académico

> El análisis se realizó con el cliente Python oficial del Observatorio Datos México (Equipo de Datos México, 2026).

O bien:

> Los datos del SAR se obtuvieron vía la API del Observatorio Datos México usando el cliente Python `datos-mexico` v0.1.0.

## CITATION.cff

El repositorio incluye un [`CITATION.cff`](https://github.com/datos-mexico/datos-mexico-py/blob/main/CITATION.cff) en el formato estándar de Citation File Format. GitHub renderiza un botón **"Cite this repository"** en la página principal del repo que exporta automáticamente a BibTeX o APA.

Contenido actual del CITATION.cff:

```yaml
cff-version: 1.2.0
message: "If you use this software, please cite it using the following metadata."
title: "datos-mexico-py: Cliente Python para la API del Observatorio Datos México"
abstract: "Cliente Python oficial para acceder programáticamente a los datos públicos mexicanos curados por el Observatorio Datos México."
authors:
  - name: "Equipo de Datos México"
    website: "https://datosmexico.org"
    email: "equipo@datosmexico.org"
version: 0.1.0
date-released: 2026-05-06
license: MIT
repository-code: "https://github.com/datos-mexico/datos-mexico-py"
url: "https://datosmexico.org"
```

## Voz colectiva

Todo lo que publica el Observatorio Datos México sale firmado por el **Equipo de Datos México**, no por personas individuales. Si vas a citar, usa la forma colectiva. Esto es una decisión deliberada del equipo: la responsabilidad es compartida y el crédito también.

## DOI

El SDK aún no tiene DOI asignado para esta versión. Cuando se asigne (probablemente vía Zenodo en una release próxima), aparecerá en el `CITATION.cff` y en esta página.

## Citar la API HTTP separadamente

Si tu paper usa también la API HTTP directamente (por ejemplo desde otro lenguaje), considera citar la API además del SDK:

> Datos provenientes de la API del Observatorio Datos México (`https://api.datos-itam.org`).

## Sobre el observatorio

El Observatorio Datos México es un esfuerzo independiente de estudiantes y egresados del ITAM, con el respaldo institucional para participar en el Premio Amafore-ITAM 2026. Es voluntario, sin fines de lucro, y los datos son de libre acceso.

Para más contexto institucional, sitio: [datosmexico.org](https://datosmexico.org).
