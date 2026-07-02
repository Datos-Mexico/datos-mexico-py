# Datos estáticos del motor

Archivos públicos descargados como estáticos (deuda técnica: migrar al SDK
cuando entren al observatorio, ver `BITACORA_DECISIONES.md`).

## `cnsf_emssa09_mortalidad.csv`

Tabla de mortalidad de activos **EMSSA-09** (Experiencia Mexicana de
Seguridad Social, 2009), qx por edad (0–109) y sexo. IMSS e ISSSTE.

- **Fuente primaria:** DOF 2009-11-27, Circular S-22.2 de la CNSF,
  ANEXO 4 "Tabla de tasas de mortalidad de activos para la Seguridad
  Social, 2009". Parseada del HTML oficial:
  <https://dof.gob.mx/nota_detalle_popup.php?codigo=5120722>
- **Descarga:** 2026-07-01, script de extracción documentado en la bitácora.
- **Sanity check:** esperanza de vida al nacer implícita H=75.5 / M=84.5;
  a los 65 años H=20.9 / M=23.6. Consistente con población asegurada.
- ⚠️ SUPUESTO PROVISIONAL: tabla **estática** (sin mejoras de mortalidad
  proyectadas; la circular define factores de mejora que no se aplican en
  el skeleton) — revisar con Dra. Yáñez.

## `conapo_proyecciones_nacional_2025_2070.csv`

Proyecciones de población de CONAPO (Conciliación Demográfica 2023),
República Mexicana, población a mitad de año por edad simple (0–109) y
sexo, 2025–2070. 10,120 filas.

- **Fuente:** CONAPO, Datos Abiertos, "Proyecciones de la Población de
  México y de las Entidades Federativas 1950–2070":
  <https://conapo.segob.gob.mx/work/models/CONAPO/Datos_Abiertos/pry23/00_Pob_Mitad_1950_2070.csv>
- **Descarga:** 2026-07-01. El archivo crudo (31 MB, todas las entidades,
  1950–2070) **no se versiona**; este CSV es el filtro nacional 2025–2070.
