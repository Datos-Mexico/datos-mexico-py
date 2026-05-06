# Fuentes primarias

El Observatorio Datos México reprocesa datos de las siguientes fuentes oficiales sin alterar los microdatos. Para precisiones metodológicas profundas, recomendamos consultar directamente la fuente.

## CDMX servidores públicos

- **Fuente**: [Datos Abiertos del Gobierno de la Ciudad de México](https://datos.cdmx.gob.mx/)
- **Universo**: padrón de personal del Poder Ejecutivo del Gobierno de la Ciudad de México
- **Cobertura**: snapshot vigente; no incluye Gobierno Federal con sede en CDMX, organismos autónomos locales, ni empresas paraestatales

## CONSAR / Sistema de Ahorro para el Retiro

- **Fuente**: [Comisión Nacional del Sistema de Ahorro para el Retiro (CONSAR)](https://www.gob.mx/consar)
- **Periodicidad**: mensual
- **Cobertura temporal**: mayo 1998 a fecha más reciente disponible
- **Incluye**: 11 AFOREs activas, recursos administrados, composición por componente, comisiones, traspasos, rendimientos por SIEFORE

## ENIGH (Encuesta Nacional de Ingresos y Gastos de los Hogares)

- **Fuente**: [INEGI ENIGH 2024 Nueva Serie](https://www.inegi.org.mx/programas/enigh/nc/2024/)
- **Naturaleza**: encuesta de corte transversal, no longitudinal
- **Universo**: hogares mexicanos representados por factores de elevación
- **Diferencia con ENIGH Tradicional**: incorpora ajustes metodológicos en captura de ingresos; ambas versiones coexisten

## API HTTP del observatorio

Todos los endpoints expuestos por este cliente Python están documentados en formato OpenAPI 3.1.0:

- **URL del spec**: https://api.datos-itam.org/openapi.json
- **Documentación interactiva (Swagger UI)**: https://api.datos-itam.org/docs
