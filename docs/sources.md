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

## ENOE (Encuesta Nacional de Ocupación y Empleo)

- **Fuente**: [INEGI ENOE / ENOE_N — 15 años y más](https://www.inegi.org.mx/programas/enoe/15ymas/)
- **Periodicidad**: trimestral
- **Cobertura temporal**: 2005T1 – 2025T1 (80 trimestres; gap documental en 2020T2, sustituido por la encuesta telefónica de transición ETOE)
- **Etapas metodológicas**: `clasica` (pre-2020T1, marco muestral CPV 2010), `etoe_telefonica` (2020T2 transición COVID), `enoe_n` (Nueva ENOE post-2020T3, marco muestral derivado del CPV 2020)
- **Universo**: ~101.5 millones de microdatos en cinco tablas (`viv`, `hog`, `sdem`, `coe1`, `coe2`); nacional + 32 entidades federativas
- **Dominio operativo**: el observatorio mantiene 15 años o más en toda la serie. INEGI publicaba originalmente 14+ en la etapa clásica pre-2014T4; el observatorio reconstruyó la serie sobre el dominio uniforme para que sea comparable.
- **Caveats tipados**: `cambio_marco_2020T3`, `redefinicion_tcco_2020T1`, `dominio_15_plus`, `gap_documental_2020T2`

## API HTTP del observatorio

Todos los endpoints expuestos por este cliente Python están documentados en formato OpenAPI 3.1.0:

- **URL del spec**: https://api.datos-itam.org/openapi.json
- **Documentación interactiva (Swagger UI)**: https://api.datos-itam.org/docs
