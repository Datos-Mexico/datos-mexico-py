# Catálogo de datasets del Observatorio Datos México

Este documento es el catálogo canónico de los datasets actualmente
disponibles a través del SDK público del Observatorio Datos México. Por
cada dataset declara el nombre canónico, la fuente oficial publicadora,
la URL de descarga, la cobertura empírica del corpus expuesto, la
granularidad, el volumen, las llaves de cruce con otros datasets, y las
limitaciones documentadas.

El catálogo es artefacto vivo y se versiona en este repositorio.

---

## 1. Propósito de este documento

El catálogo articula con disciplina académica qué publica el observatorio
en su SDK público. Es la fuente de verdad que el resto de artefactos del
observatorio —el sistema de generación de artículos pregunta-respuesta,
las publicaciones académicas, la documentación interna— consulta cuando
necesita saber qué está disponible.

Este documento es complemento del MANIFESTO institucional y del documento
ARQUITECTURA-ARTICULOS, ambos publicados en el repositorio institucional
del observatorio. El MANIFESTO declara la identidad del observatorio y
su modelo de crecimiento por ciclos temáticos profundos. El documento
ARQUITECTURA-ARTICULOS articula la arquitectura del componente
artículos pregunta-respuesta del corpus. Este catálogo articula el
componente datos del observatorio: qué hay, de dónde viene, con qué
disciplina académica se sostiene.

El catálogo no documenta la implementación técnica del SDK ni de la API
del observatorio. Tampoco documenta la operación específica de
actualización de cada dataset, que vive en capa separada. El catálogo es
descriptivo del contenido público, no prescriptivo del proceso interno.

---

## 2. Convenciones de uso del catálogo

**Nombre canónico.** Cada dataset se identifica por el nombre del
namespace del SDK que lo expone. El nombre canónico es estable: cambios
de nombre se versionan explícitamente en el historial del catálogo.

**Fuente oficial publicadora.** Cada dataset cita la organización
gubernamental o académica que lo publica originalmente. El observatorio
reprocesa los datos sin alterar microdatos: la fuente oficial es la
autoridad última sobre cada cifra.

**Cifras del catálogo.** Las cifras cuantitativas citadas corresponden a
la versión del SDK vigente al momento de cada release del catálogo. Los
cambios en cifras entre releases reflejan actualizaciones reales de los
datasets, no inestabilidad del catálogo.

**Citación académica.** El catálogo se cita como artefacto del SDK
`datos-mexico` con la versión correspondiente. El formato de citación
del SDK está documentado en `CITATION.cff` del repositorio.

**Lo que este catálogo no representa.** El catálogo no es documentación
técnica del SDK ni de los endpoints individuales —ese material vive en
`docs.datosmexico.org` y en los docstrings del código. El catálogo es
artefacto académico que articula los datasets como contenido público del
observatorio, independiente del cliente programático con el que se
accedan.

---

## 3. Principio de actualización continua

El observatorio asume como pilar operacional la actualización continua
de los datasets de su catálogo. Cada dataset se actualiza al ritmo de su
fuente oficial publicadora: las series de mayor frecuencia se incorporan
más cercanas en el tiempo, las series de menor frecuencia respetan la
cadencia de su organismo publicador.

Cuando un usuario académico consulta el observatorio, opera bajo la
premisa de que los datasets reflejan la versión más reciente disponible
públicamente de la fuente. La operación específica de actualización es
responsabilidad de capa separada del observatorio y no se detalla en
este catálogo.

Las cadencias específicas por dataset, las fechas de captura puntuales y
los mecanismos operacionales de absorción de actualizaciones son
información complementaria que vive en otros artefactos. Este catálogo
describe el contenido del observatorio; no describe cómo el observatorio
mantiene ese contenido al día.

---

## 4. Datasets fuente del observatorio

El observatorio expone actualmente cuatro datasets fuente principales,
articulados como secciones independientes. Cada dataset proviene
directamente de una fuente oficial pública mexicana y se incorpora al
SDK con la disciplina académica declarada en el MANIFESTO.

### 4.1. Servidores Públicos del Gobierno de la Ciudad de México

**Nombre canónico.** `cdmx`.

**Fuente oficial publicadora.** Gobierno de la Ciudad de México, Datos
Abiertos CDMX.

**URL canónica de la fuente.** https://datos.cdmx.gob.mx/

**Cobertura del corpus expuesto.** Padrón vigente del personal del Poder
Ejecutivo del Gobierno de la Ciudad de México. El dataset es un
snapshot del padrón en su versión más reciente publicada, sin serie
temporal histórica.

**Granularidad principal.** Persona individual del padrón, con sus
campos asociados de puesto, sector, tipo de contratación, tipo de
personal, sueldo bruto y características demográficas. La granularidad
agregada se expone en sectores de gobierno como unidad organizativa.

**Volumen aproximado.** Aproximadamente 246,836 servidores públicos
distribuidos en 75 sectores del Gobierno de la Ciudad de México, más
ocho catálogos auxiliares para construcción de filtros (sectores,
puestos, sexos, tipos de contratación, tipos de personal, tipos de
nómina, niveles salariales, universos presupuestales).

**Llaves de cruce con otros datasets.** Las dimensiones del dataset que
permiten cruce con otros componentes del catálogo son `sexo`, `edad`,
`sueldo_bruto` y el conjunto de identificadores categóricos del padrón
(`sector_id`, `tipo_contratacion_id`, `tipo_personal_id`,
`universo_id`). El dataset no porta clave geográfica explícita —es un
solo padrón institucional de la entidad federativa Ciudad de México
(clave INEGI `09`)— por lo que su cruce geográfico con datasets que sí
portan clave de entidad se realiza implícitamente filtrando esos
datasets por la clave `09`.

**Limitaciones documentadas.** El padrón cubre exclusivamente al Poder
Ejecutivo del Gobierno de la Ciudad de México: no incluye dependencias
del Gobierno Federal con sede en la Ciudad de México, organismos
constitucionales autónomos locales, ni empresas paraestatales. La fuente
oficial publica ocasionalmente sectores en estado de prueba con
contenido sin asignar; al momento de este catálogo, el dataset incluye
dos sectores con `total_servidores=0` (identificadores 74 y 77) que el
SDK preserva sin alterar para mantener fidelidad con la fuente.

**Modos de acceso alternativos en el SDK.** El observatorio expone el
padrón también mediante modos de acceso alternativos del SDK
—namespaces de tablas normalizadas y exportación a formato CSV— cuya
documentación técnica vive en el README del SDK y no en este catálogo
académico.

---

### 4.2. CONSAR — Sistema de Ahorro para el Retiro

**Nombre canónico.** `consar`.

**Fuente oficial publicadora.** Comisión Nacional del Sistema de Ahorro
para el Retiro (CONSAR), órgano desconcentrado de la Secretaría de
Hacienda y Crédito Público.

**URL canónica de la fuente.** https://www.gob.mx/consar

**Cobertura del corpus expuesto.** Serie histórica del Sistema de Ahorro
para el Retiro mexicano desde mayo de 1998 hasta la fecha más reciente
publicada por la fuente. Cubre recursos administrados, composición por
componente, comisiones, traspasos, rendimientos por SIEFORE, precios
NAV y precios de gestión, cuentas, medidas regulatorias y activo neto.

**Granularidad principal.** Combinación de AFORE × SIEFORE × tipo de
recurso × métrica × fecha mensual. La granularidad temporal nativa es
mensual (con día de corte 01).

**Volumen aproximado.** 11 AFOREs activas, 11 SIEFOREs, 15 tipos de
recurso, 327 puntos mensuales en la serie base, expuestos a través de
treinta y cuatro endpoints organizados en doce grupos lógicos
(catálogos, recursos administrados, PEA cotizantes, comisiones, flujos,
traspasos, rendimientos, precios NAV, precios de gestión, cuentas,
medidas regulatorias, activo neto).

**Llaves de cruce con otros datasets.** Las dimensiones de cruce del
dataset son `afore_codigo` (cadena alfanumérica que identifica a cada
AFORE), `siefore_slug` (identificador de cada SIEFORE), `fecha` (con
día de corte fijo en 01), y el catálogo de tipos de recurso. El dataset
opera a nivel nacional sin desagregación geográfica por entidad
federativa.

**Limitaciones documentadas.** El endpoint que expone recursos por
componente devuelve una estructura jerárquica, no una partición plana:
las filas se clasifican por categoría en `total`, `aggregate`,
`component` y `operativo`, y la suma correcta de componentes requiere
filtrar exclusivamente a categorías `component` y `operativo`. Sumar
indiscriminadamente sobre todas las filas sobre-cuenta el SAR
aproximadamente tres veces. Esta restricción está documentada en el
docstring del método correspondiente del SDK y validada por la suite de
tests de integridad del observatorio. Las cifras monetarias del dataset
se publican en pesos mexicanos corrientes, no en pesos constantes.

---

### 4.3. ENIGH — Encuesta Nacional de Ingresos y Gastos de los Hogares

**Nombre canónico.** `enigh`.

**Fuente oficial publicadora.** Instituto Nacional de Estadística y
Geografía (INEGI).

**URL canónica de la fuente.** https://www.inegi.org.mx/programas/enigh/nc/2024/

**Cobertura del corpus expuesto.** Edición 2024 Nueva Serie de la
ENIGH. La Nueva Serie incorpora ajustes metodológicos en la captura de
ingresos respecto a la ENIGH Tradicional, y ambas versiones coexisten
como ediciones publicadas por INEGI. El observatorio expone la Nueva
Serie como versión canónica del dataset en su catálogo actual.

**Granularidad principal.** Hogar mexicano, expresado tanto en muestra
como en expansión a la población nacional mediante los factores de
elevación de INEGI. La granularidad agregada se expone en deciles
nacionales de ingreso y en las treinta y dos entidades federativas.

**Volumen aproximado.** 91,414 hogares en muestra, expandidos a 38.8
millones de hogares en la población nacional, distribuidos en nueve
rubros de gasto monetario y diez deciles de ingreso, expuestos a través
de diez endpoints (hogares, gastos por rubro, demografía, tres
actividades económicas de los hogares, metadata, validaciones contra
cifras oficiales).

**Llaves de cruce con otros datasets.** Las dimensiones de cruce son
`entidad` (clave INEGI de dos dígitos, compatible directamente con la
clave de entidad de ENOE), y los deciles nacionales de ingreso. Las
dimensiones internas del hogar (composición demográfica, ingreso
corriente, gasto por rubro) sirven como base de los análisis
comparativos editoriales documentados en sección 5.

**Limitaciones documentadas.** El dataset es de corte transversal, no
longitudinal: los hogares observados en la edición 2024 no son los
mismos observados en ediciones anteriores ni serán los mismos en
ediciones posteriores. La Nueva Serie coexiste con la ENIGH Tradicional;
las cifras de ambas no son directamente comparables sin ajuste
metodológico explícito. Las cifras expandidas a la población nacional
dependen de los factores de elevación publicados por INEGI: cualquier
cambio en esos factores impacta toda la expansión.

---

### 4.4. ENOE — Encuesta Nacional de Ocupación y Empleo

**Nombre canónico.** `enoe`.

**Fuente oficial publicadora.** Instituto Nacional de Estadística y
Geografía (INEGI), Encuesta Nacional de Ocupación y Empleo / ENOE_N
para población de 15 años o más.

**URL canónica de la fuente.** https://www.inegi.org.mx/programas/enoe/15ymas/

**Cobertura del corpus expuesto.** Serie trimestral desde el primer
trimestre de 2005 hasta el primer trimestre de 2025, abarcando ochenta
trimestres. La serie incluye un gap documental en el segundo trimestre
de 2020, periodo en el que INEGI sustituyó la captura presencial por la
Encuesta Telefónica de Ocupación y Empleo (ETOE) como respuesta a las
restricciones sanitarias de ese momento.

**Granularidad principal.** Microdato individual organizado en cinco
tablas (`viv`, `hog`, `sdem`, `coe1`, `coe2`) que cubren vivienda,
hogar, características sociodemográficas, y dos cuestionarios de
ocupación y empleo. Los agregados se exponen a nivel nacional, por cada
una de las treinta y dos entidades federativas, por sector económico
según la clasificación SCIAN (doce sectores), y por posición en la
ocupación (cuatro categorías: subordinados, empleadores, cuenta propia,
no remunerados).

**Volumen aproximado.** Aproximadamente 101.5 millones de microdatos en
las cinco tablas, derivando 76 mil indicadores agregados y trece
indicadores agregados principales con caveats metodológicos tipados,
expuestos a través de diecisiete endpoints organizados en cuatro grupos
(catálogos y metadata, indicadores agregados, distribuciones,
microdatos).

**Llaves de cruce con otros datasets.** Las dimensiones de cruce son
`entidad_clave` (clave INEGI de dos dígitos, compatible directamente con
la clave `entidad` de ENIGH), `periodo` (formato `YYYYTQ`), `etapa`
(`clasica`, `etoe_telefonica`, `enoe_n`), `sex` (codificación INEGI
1=hombre, 2=mujer) y `eda` (edad).

**Limitaciones documentadas.** La serie atraviesa tres etapas
metodológicas heterogéneas que requieren atención académica explícita.
Primera, el cambio de marco muestral en el tercer trimestre de 2020
(`cambio_marco_2020T3`): INEGI migró del marco derivado del Censo de
Población y Vivienda 2010 al marco derivado del Censo de Población y
Vivienda 2020. Segunda, la redefinición del Tipo de Cobertura del
Cuestionario de Ocupación (TCCO) en el primer trimestre de 2020
(`redefinicion_tcco_2020T1`). Tercera, el gap documental del segundo
trimestre de 2020 (`gap_documental_2020T2`). Adicionalmente, el
observatorio mantiene un dominio operativo uniforme de quince años o
más en toda la serie histórica (`dominio_15_plus`), recalculando la
etapa clásica pre-2014T4 sobre el dominio 15+ para reconstruir la serie
comparable. INEGI publicaba originalmente catorce años o más en esa
etapa clásica. Estos cuatro caveats están tipados explícitamente en cada
response del SDK que los toque, para que el lector pueda incorporarlos
a su análisis sin requerir investigación adicional.

---

## 5. Análisis comparativos editoriales

El observatorio expone en su SDK una capa adicional de endpoints que
cruzan información de los datasets fuente y agregan contenido editorial
producido por el equipo académico del observatorio. Esta capa es
distinta en naturaleza de los datasets fuente: no es replicación de
información oficial sino articulación interpretativa del observatorio
sobre esa información.

**Nombre canónico.** `comparativo`.

**Naturaleza del artefacto.** Los endpoints comparativos contienen,
además de las métricas precomputadas, campos editoriales explícitos
(`note`, `narrative`, `interpretacion`, `caveats`,
`caveats_interpretativos`). Estos campos son contenido académico
humano del observatorio sobre los datos oficiales, y el SDK los
preserva sin alteración. La clasificación como "editorial" es
deliberada: el artefacto no se presenta como dato observacional puro
sino como articulación académica del observatorio que el lector puede
auditar y cuestionar.

**Datasets fuente que combina.** CDMX (servidores públicos), CONSAR
(SAR), y ENIGH (hogares). La combinación específica varía por endpoint.

**Cobertura del corpus expuesto.** Siete endpoints comparativos
editoriales: ingreso del servidor CDMX frente a ingreso del hogar
nacional y CDMX, gastos del hogar CDMX frente a nacional desagregado
por rubro, decil de pertenencia del servidor CDMX en la distribución
ENIGH bajo distintos supuestos de perceptores, comparación entre
brackets alto y bajo de la distribución de sueldos CDMX y los deciles
extremos de ENIGH, bancarización del hogar CDMX frente a nacional,
actividad económica del hogar CDMX frente a nacional, y aportes del
servidor CDMX frente a jubilaciones actualmente recibidas por hogares
ENIGH.

**Granularidad principal.** Heterogénea por endpoint: ratios y
diferenciales agregados, posicionamiento en deciles, comparaciones de
brackets extremos, porcentajes y razones poblacionales.

**Volumen aproximado.** Siete endpoints editoriales preagregados, cada
uno produciendo una respuesta tipada con métricas cuantitativas más
campos editoriales de contexto, interpretación y caveats.

**Llaves de cruce.** Las llaves de cruce internas son los pares
específicos que cada endpoint articula: sueldo CDMX × ingreso del hogar
ENIGH (con su decil correspondiente), aportes CDMX × jubilaciones
ENIGH × estructura SAR. Los cruces están preagregados; el lector
consume el resultado del cruce, no los inputs crudos.

**Limitaciones documentadas.** Los campos editoriales son contenido
humano y, por construcción, reflejan la articulación del equipo
académico del observatorio sobre los datos al momento de su producción.
El campo `interpretacion` del endpoint de aportes frente a jubilaciones
declara explícitamente que la comparación NO es proyección actuarial:
es contraste entre dos realidades coexistentes del sistema de
pensiones. Esa declaración es paradigmática del registro académico de
toda la capa comparativa: el observatorio publica articulaciones, no
predicciones.

---

## 6. Llaves de cruce entre datasets fuente

Las llaves de cruce entre datasets fuente verificadas empíricamente son
las siguientes:

**Clave de entidad federativa INEGI.** La clave de dos dígitos publicada
por INEGI es compatible directamente entre ENOE (`entidad_clave`) y
ENIGH (`entidad`). El cruce geográfico es directo: una pregunta que
combine indicadores ENOE de mercado laboral con composición de hogares
ENIGH puede usar la clave INEGI común como dimensión de unión.

**Cruce implícito CDMX × ENIGH/ENOE.** El dataset CDMX no porta clave
geográfica explícita —es un solo padrón de la entidad federativa Ciudad
de México (clave INEGI `09`)—. El cruce con ENIGH y ENOE se realiza
implícitamente filtrando esos datasets por la clave `09`. Los endpoints
comparativos editoriales aplican esta convención de forma sistemática.

**Cobertura geográfica de CONSAR.** El dataset CONSAR opera a nivel
nacional sin desagregación geográfica por entidad federativa. Los
cruces que involucran CONSAR son temáticos (pensiones, jubilaciones,
aportes) más que geográficos.

**Compatibilidad temporal.** Los cuatro datasets tienen granularidades
temporales distintas: ENOE trimestral, CONSAR mensual, ENIGH 2024 como
snapshot único, y CDMX como snapshot vigente sin fecha explícita. Los
cruces temporales entre datasets requieren explicitar la convención
empleada en cada caso. La capa de análisis comparativos editoriales
(sección 5) documenta sus convenciones temporales en los campos
`caveats` y `caveats_interpretativos` de cada endpoint.

Las llaves de cruce internas de cada dataset (`afore_codigo` y
`siefore_slug` en CONSAR, `tipo_recurso` en CONSAR, `decil` en ENIGH,
`sector_id` en CDMX, `sector_clave` SCIAN y `pos_clave` en ENOE) no
participan en cruces inter-dataset sino en cruces intra-dataset.

---

## 7. Exclusiones explícitas del catálogo

El SDK también expone un namespace `demo` destinado a docencia
universitaria (curso de Bases de Datos del Instituto Tecnológico
Autónomo de México) que no forma parte del catálogo del observatorio.
Su exclusión es deliberada para preservar la coherencia del catálogo
público como artefacto exclusivamente del observatorio.

El namespace `demo` permanece accesible a quien lo necesite —es público
como el resto del SDK— pero no se cataloga como dataset del
observatorio porque su contenido es didáctico, no académico-público.

---

## 8. Compromisos del catálogo

El observatorio asume públicamente los siguientes compromisos
específicos sobre este catálogo. Estos compromisos son adicionales a
los del MANIFESTO sección 9 y a los del documento ARQUITECTURA-ARTICULOS
sección 11, y no los reemplazan.

Toda cifra cuantitativa citada en este catálogo es derivable
empíricamente del SDK al momento del release correspondiente. El lector
académico puede reproducir cada cifra interrogando el SDK con la
versión citada.

Todo dataset listado en este catálogo declara visiblemente su fuente
oficial publicadora, la URL canónica de la fuente, la cobertura del
corpus que el observatorio expone, la granularidad, el volumen
aproximado, las llaves de cruce y las limitaciones documentadas. Esa
información está disponible al lector sin requerir interpretación
indirecta.

Toda incorporación de un dataset nuevo al SDK se acompaña de la
actualización correspondiente de este catálogo en el mismo ciclo de
release. El catálogo no se rezaga sistemáticamente respecto del SDK:
es artefacto vivo sincronizado con la versión publicada.

Todo cambio sustantivo a un dataset existente —cobertura ampliada,
nueva limitación detectada, cambio metodológico en la fuente oficial
absorbido por el observatorio— queda registrado en el historial Git de
este catálogo, con descripción explícita del cambio y su motivo. La
sustitución silenciosa de cifras no existe en el catálogo del
observatorio.

El catálogo no es objeto de paywall, suscripción ni autenticación. El
acceso al SDK público al que este catálogo describe permanece gratuito,
abierto y citable académicamente según los compromisos del MANIFESTO.

Los errores detectados en el catálogo —cifras desactualizadas
respecto del SDK, llaves de cruce mal documentadas, limitaciones
omitidas— pueden reportarse a los canales de comunicación del
observatorio y se corrigen explícitamente con errata registrada en el
historial del repositorio.

---

*Observatorio Datos México · datosmexico.org*
