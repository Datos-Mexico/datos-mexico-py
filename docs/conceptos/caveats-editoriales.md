# Caveats editoriales

Muchos endpoints del API exponen, además del dato, **campos editoriales**: textos en prosa que documentan contexto, salvedades metodológicas, hipótesis activas o interpretaciones que el equipo del observatorio considera necesarias para leer correctamente la cifra. El SDK los preserva sin alteración.

Esta página explica qué son, por qué existen, cómo aparecen en la API, y cuándo conviene leerlos.

## Qué son

Cuando un investigador del observatorio expone un endpoint comparativo o un dataset con metodología no trivial, no basta con publicar la cifra. Hace falta decir, por ejemplo:

- "Este indicador suma activos de las SIEFOREs Generacionales y Adicionales pero excluye las cuentas en proceso de liquidación."
- "Las cifras están en pesos corrientes; para análisis temporal recomendamos deflactar usando el INPC."
- "Este corte usa la mediana porque la distribución es muy sesgada y el promedio sobre-representa los outliers."
- "La heterogeneidad por sexo en este puesto se explica parcialmente por la desigual antigüedad."

Esos textos son los **caveats editoriales**. Forman parte del dato. Si tu análisis los ignora, estás potencialmente sacando conclusiones que el equipo ya marcó como problemáticas.

## Por qué existen

Es una decisión metodológica explícita del observatorio: separar los microdatos brutos (que vienen de fuente oficial sin alterar) de la **interpretación** (que sí es responsabilidad del equipo). Los caveats son la frontera. Permiten:

- Defender un dato sin pretender que se interpreta por sí mismo.
- Documentar trade-offs que tomó el equipo (ej. qué hacer con missing values, qué año usar como base, qué denominador es comparable).
- Hacer reproducible no solo el cálculo sino también la lectura.

Esto no es práctica común en APIs de datos abiertos. Datos abiertos suele significar "tomas el JSON y le aplicas tu interpretación". El observatorio se compromete con una capa más: documentar la nuestra.

## Cómo aparecen en la API

El nombre del campo **no es uniforme** entre endpoints. Esto es deliberado: cada endpoint tiene una estructura distinta y forzar una nomenclatura única agregaría sobrecarga sin valor. Algunos nombres comunes:

- `note` — nota general sobre cómo leer la cifra.
- `narrative` — texto más extenso, frecuentemente usado en endpoints comparativos.
- `caveats` — lista o texto con salvedades específicas.
- `nota_hipotesis` — hipótesis activa que justifica un cálculo (común en `comparativo`).
- `interpretacion` — la lectura que hace el equipo de la cifra (cuando aplica).
- `metodologia` / `methodology` — descripción de cómo se construyó el indicador.

El SDK no normaliza estos nombres ni intenta unificarlos. Cada modelo Pydantic los expone tal cual la API los publica, con `extra="allow"` para que campos que se agreguen en el futuro se preserven sin romper el cliente. Esto significa que **leer los caveats requiere mirar el modelo del endpoint** en cuestión.

## Cómo el SDK los preserva

Los modelos están configurados con:

```python
model_config = ConfigDict(
    populate_by_name=True,
    extra="allow",  # campos no listados explícitamente se preservan
)
```

Esto implica que aunque la documentación del modelo en mkdocstrings liste solo los campos "principales", el objeto retornado puede traer campos editoriales adicionales accesibles vía `model_extra` o como atributos directos.

```python
from datos_mexico import DatosMexico

with DatosMexico() as client:
    resp = client.comparativo.aportes_vs_jubilaciones_actuales()
    print(resp.narrative)
    print(resp.caveats)
```

## Cuándo leerlos

- **Antes de publicar** una cifra del observatorio en un reporte, paper o nota: lee los caveats del endpoint correspondiente. Si una salvedad aplica al uso que vas a darle, cítala.
- **Antes de comparar** dos endpoints similares cross-dataset: los caveats suelen explicar por qué dos cifras parecidas no son directamente comparables (diferentes universos, fechas de corte, denominadores).
- **En notebooks de análisis exploratorio**: imprimir el `narrative` o `note` al inicio de la celda donde uses la cifra es una buena práctica. Documenta para tu yo futuro y para revisores.

## Cuándo no son suficientes

Los caveats editoriales documentan lo que el equipo del observatorio sabe en el momento de publicar. No documentan cosas que aún no sabemos, ni problemas que aparecen al combinar el dato con otra fuente externa. Si encuentras una inconsistencia que no aparece en los caveats, repórtala a [errores@datosmexico.org](mailto:errores@datosmexico.org) — es información valiosa que probablemente debería estar ahí.

## Lectura adicional

- [Identidad contable](identidad-contable.md) — los caveats acompañan a las validaciones cuantitativas, no las reemplazan.
- [Tutorial comparativo](../tutoriales/comparativo.md) — los endpoints de `comparativo` son los que más texto editorial traen.
