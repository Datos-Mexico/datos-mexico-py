# BRIEF — Motor de microsimulación actuarial (Sección 6)
### Handoff a Claude Code · Paper Amafore-ITAM 2026 · Equipo Datos México

> **Cómo usar este archivo:** es un documento autocontenido. Asume que quien lo lee (tú, Claude Code) **no** tiene contexto previo del proyecto. Contiene todo lo necesario para (1) auditar el repo, (2) construir un motor que corre de punta a punta, y (3) producir un entregable para la junta del equipo. Empieza por la **Tarea 0 (Auditoría)** antes de escribir una sola línea de motor.

---

## 0. TL;DR operativo

- **Qué construimos:** una microsimulación actuarial de trabajadores sintéticos que proyecta la distribución de pensiones del SAR mexicano y el costo fiscal del Fondo de Pensiones para el Bienestar (FPB), horizonte **2026–2070**.
- **Estrategia:** *walking skeleton primero*. El motor completo de punta a punta con cada bloque en su versión más cruda defendible, que **ya produce un número**. Refinar después, un bloque a la vez. **No** construir cada componente estocástico perfecto por separado.
- **Restricción temporal:** el paper va contra reloj (deadline 31 jul, cierre interno 20 jul). La Sección 6 es **ruta crítica**: las secciones 7, 8 y 9 (un tercio del paper) no pueden escribirse sin sus salidas. Prioriza *que corra y valide* sobre *que sea sofisticado*.
- **Criterio de éxito del jurado:** un modelo que **corre, valida contra el presente observado (2025) y reporta distribuciones con intervalos** vence a uno con procesos estocásticos elegantes que no replica lo observado. La validación 2025 vale más que cualquier Lee-Carter.

---

## 1. Contexto del proyecto

**El paper.** Concurso Premio de Investigación sobre Pensiones en México 2026 (Amafore-ITAM). Pregunta central: *¿cuánto le costará al Estado mexicano el FPB en los próximos ~45 años, y qué reformas contienen ese costo sin sacrificar suficiencia?* Máximo 40 cuartillas, español, referencias APA. Se evalúa: relevancia al SAR, presentación, modelos/herramientas, rigor científico, originalidad.

**El diferenciador real del equipo** (explótalo en el código, no solo en la prosa): infraestructura empírica **reproducible y auditable** sobre datos validados al peso contra fuente oficial. Ningún otro concursante probablemente llega con un motor versionado, con identidades contables verificadas y notebook ejecutable. El motor no compite por ser el más complejo; compite por ser el más **auditable**.

**La Sección 6 en el paper (8 páginas).** Responsables: Andre + Emiliano. Revisores:
- **Dra. Ángeles Yáñez** — arquitectura actuarial (anualización, tablas de mortalidad, tasas de reemplazo). *Lectora técnica más importante.*
- **Dr. Fernando Esponda** — infraestructura computacional, reproducibilidad, estabilidad numérica.
- **Dr. Rubén Martínez Avendaño** — rigor formal, convergencia de procesos estocásticos, validez de estimadores.

**Qué alimenta el motor (dependencias downstream):**
- **Sección 7 (Resultados de suficiencia):** recibe distribuciones de tasas de reemplazo y saldos.
- **Sección 8 (Sostenibilidad fiscal FPB):** recibe número de jubilados y subsidio anual requerido → responde la pregunta central del paper.
- **Sección 9 (Reformas):** reusa el motor para evaluar 7 reformas contra el escenario base.

---

## 2. TAREA 0 — Auditoría del repo (haz esto primero)

Antes de construir, inventaría qué hay. Ejecuta un recorrido del repo (`tree -L 3`, `ls -R`, revisa `README`, `requirements.txt`/`pyproject.toml`, y cualquier carpeta `data/`). Luego reporta, contra esta checklist, qué **existe y es usable**, qué **existe pero está crudo**, y qué **falta**:

| # | Insumo | Para qué | ¿Presente? |
|---|--------|----------|-----------|
| 1 | **Matrices de transición laboral** (o panel ENOE crudo para estimarlas) entre estados {formal, informal, desempleado, fuera de fuerza laboral}, idealmente por edad/género/escolaridad | Trayectorias laborales | ⬜ |
| 2 | **Tablas de mortalidad CNSF** por edad y género | Anualización de pensiones | ⬜ |
| 3 | **Proyecciones CONAPO 2025–2070** por edad y género | Cohortes de jubilación, proyección FPB | ⬜ |
| 4 | **Serie de rendimientos SIEFOREs** ~2010–2025 (generacionales, CONSAR) | Calibrar rendimiento $r$ | ⬜ |
| 5 | **Distribuciones salariales** IMSS/ENOE | Calibrar proceso de salarios | ⬜ |
| 6 | **Agregados observados 2025** (saldos, cotizantes, tamaño del SAR, distribución de saldos) | **VALIDACIÓN** — sin esto el motor no es creíble | ⬜ |

**Cómo reportar la auditoría** (esto va también como *ask* a la junta):
- Para cada insumo presente: ruta del archivo, formato, número de filas/columnas clave, rango temporal, y un `.head()` o resumen.
- Para cada insumo ausente o crudo: qué falta exactamente y si es bloqueante para el walking skeleton (la mayoría **no** lo es —ver §4).
- Verifica si el SDK `datos-mexico` (PyPI) está instalado y si `api.datos-itam.org` responde. Si el repo usa el SDK, prueba una llamada mínima.

> **Regla de desbloqueo:** CNSF y CONAPO son datos públicos. Si no están en el SDK/repo, **no bloquees el motor esperándolos** — se bajan a mano como archivo estático y se marca como deuda técnica. La ingeniería de datos y el desarrollo del motor son dos frentes que no deben acoplarse en este punto del calendario.

---

## 3. Filosofía de construcción (no negociable dado el calendario)

1. **End-to-end antes que profundidad.** Un trabajador entra → transita → cotiza → acumula → se anualiza → sale con una tasa de reemplazo. Corre ese loop completo con versiones crudas ANTES de mejorar cualquier bloque.
2. **Cada supuesto provisional se marca en código y en bitácora.** Convención literal en el código: `# ⚠️ SUPUESTO PROVISIONAL: <qué> — revisar con <quién>`. Todo lo marcado se acumula en `BITACORA_DECISIONES.md`. Esto es lo que Yáñez y Martínez Avendaño van a querer discutir; adelantarlo nos hace ver en control, no atrasados.
3. **Parsimonia.** No se parametriza nada que los datos no justifiquen. Ante la duda, la versión simple.
4. **Reproducibilidad desde el commit 1.** Semillas documentadas, configuración versionada, notebook que corre sin intervención manual.

---

## 4. Especificación técnica del motor

### 4.1 Loop de acumulación (núcleo)

Tiempo discreto. **Empieza con paso anual** para depurar rápido; migra a trimestral solo si el calendario lo permite. Por agente $i$ y periodo $t$:

$$
S_{i,t+1} = \big(S_{i,t} + A_{i,t} - C_{i,t}\big)\,(1 + r_{i,t})
$$

- $S$ = saldo en la cuenta individual
- $A$ = aportaciones del periodo (patrón + trabajador + Estado/cuota social), **solo si el estado laboral es "formal"**
- $C$ = comisiones
- $r$ = rendimiento del periodo

**Identidad contable que DEBE cumplirse en cada corrida** (check automático, aborta si falla):

$$
\Delta S = A + R - C
$$

donde $R$ es el rendimiento monetario acumulado del periodo. Si esta identidad no cuadra, hay una fuga en la tubería y todo lo demás es ruido. Este check es la primera línea de defensa de credibilidad ante el jurado.

### 4.2 Los cinco bloques — versión skeleton vs. versión refinada

Construye **la columna skeleton primero, para los cinco**. Solo cuando el loop cierra y valida, pasa a refinar por prioridad de retorno.

| Bloque | **Skeleton (Fase 1)** | **Refinado (Fase 3, por prioridad)** |
|--------|----------------------|--------------------------------------|
| **Trayectorias laborales** | Matriz de Markov **homogénea** (una sola matriz de transición, de proporciones ENOE agregadas; incluso hand-coded) | Markov **heterogéneo** con covariables edad/género/escolaridad estimado del panel ENOE. Selección por ajuste out-of-sample. *(Prioridad 1)* |
| **Salarios** | Determinístico o con shock trivial | Log-lineal AR(1): ver §4.3. Calibrado IMSS + ENOE. *(Prioridad 2)* |
| **Rendimientos SIEFOREs** | $r$ constante real (p. ej. **4% anual** — marcar como provisional) | Modelo de regímenes o GBM calibrado con serie 2010–2025 + glide path por edad. *(Prioridad 3)* |
| **Mortalidad** | Tabla CNSF **estática** por edad/género | Lee-Carter con drift: ver §4.4. *(Prioridad 4 — opcional, va al anexo si sobra tiempo)* |
| **Reglas SAR** | **BIEN DESDE EL INICIO** — es determinístico y conocido. Ver §4.5. | (Ya correcto; solo verificar contra DOF/CONSAR) |

> El único bloque que **no** se aproxima en el skeleton son las **reglas SAR** (§4.5): son ley, son públicas, y equivocarlas es un error de credibilidad barato de evitar.

### 4.3 Proceso de salarios (versión refinada)

Salario cotizable en logaritmos, con componente individual persistente:

$$
\log w_{i,t} = \mu_i + \phi\,(\log w_{i,t-1} - \mu_i) + \varepsilon_{i,t}, \qquad \varepsilon_{i,t}\sim\mathcal{N}(0,\sigma^2)
$$

- $\mu_i$: nivel salarial de largo plazo del agente (por perfil edad/género/escolaridad/sector)
- $\phi \in (0,1)$: persistencia
- Opcional (si Emiliano lo entrega calibrado): descomposición permanente + transitoria.

Calibración: componente de nivel con ENIGH/IMSS por perfil; $\phi$ y $\sigma$ con el panel ENOE. **⚠️ Marcar $\phi$, $\sigma$ como provisionales hasta calibración de Sección 4.**

### 4.4 Mortalidad (versión refinada — OPCIONAL)

Lee-Carter:

$$
\ln m_{x,t} = a_x + b_x\,k_t + \varepsilon_{x,t}, \qquad k_t = k_{t-1} + d + \eta_t
$$

con $k_t$ caminata aleatoria con drift $d$. Para el skeleton, usa la tabla CNSF estática ($m_{x}$ fijo). **Lee-Carter es extensión de anexo, no bloqueante.**

### 4.5 Reglas SAR — parámetros duros (construir con precisión)

> **⚠️ Claude Code: estos parámetros deben verificarse contra fuente primaria (DOF, CONSAR) antes de fijarlos.** Los valores abajo son el mejor conocimiento del equipo a la fecha del brief; trátalos como punto de partida a confirmar, no como verdad final. Documenta la fuente exacta de cada uno.

- **Aportación obligatoria (RCV) — reforma 2020, calendario gradual 2023–2030.** La aportación total sube de forma escalonada hacia **15%** del salario base hacia 2030 (la aportación patronal es la que crece; en 2024 el total rondaba **8.5%**). *Construir el vector año→tasa explícito y citarlo.*
- **Cuota social (aportación del Estado):** aplica hasta **4 UMA** de salario. *Verificar tabla vigente.*
- **Tope salarial de cotización:** **25 UMA**.
- **Comisiones:** tope ligado a promedios internacionales (post-2020). Usar serie CONSAR.
- **Semanas de cotización requeridas:** reducidas de 1250 a **750** en 2021, con aumento gradual hasta **1000 en 2031**.
- **Edad de retiro:** **65 años** (60 con elegibilidad).
- **UMA:** usar valor observado por año; proyectar con inflación (Banxico) hacia adelante.

### 4.6 Anualización, Pensión Garantizada (PG) y FPB

Al retiro, el saldo $S_{i,\text{ret}}$ se convierte en pensión mensual vía factor actuarial:

$$
P_i = \frac{S_{i,\text{ret}}}{12 \cdot \ddot{a}_{x}}, \qquad \ddot{a}_{x} = \sum_{k\geq 0} v^{k}\, {}_{k}p_{x}
$$

donde $\ddot{a}_x$ es el valor presente actuarial de una anualidad vitalicia (renta anticipada) para edad de retiro $x$, $v = (1+i)^{-1}$ la tasa de descuento, y ${}_{k}p_x$ la probabilidad de supervivencia (de la tabla CNSF).

> **⚠️ La convención exacta de anualización (mensual vs. anual, anticipada vs. vencida, tasa técnica $i$) debe cerrarse con la Dra. Yáñez.** Es el punto donde un actuario mira primero. En el skeleton usa la forma anual anticipada de arriba y márcala como provisional.

**Lógica PG / FPB (distinguir con cuidado — confirmar con Fabiola/Yáñez):**
1. **PG (Pensión Garantizada):** piso de ley. Post-2020 es un *tabulador* (edad × semanas cotizadas × salario promedio), no un monto fijo. Si el trabajador cumple requisitos y $P_i <$ PG, se le lleva a PG.
2. **FPB (complemento):** lleva la pensión hacia un piso vinculado al salario promedio de cotización, con tope **16,777.68 pesos/mes (valor 2024, actualizable con inflación)**. El **complemento FPB** es lo que cuesta al Estado:

$$
\text{Complemento}_{i,t} = \max\big(0,\ \text{piso}_t - P_{i,t}\big)
$$

3. **Costo fiscal anual del FPB** (salida clave para Sección 8):

$$
\text{Costo}_t = \sum_{i \in \text{jubilados}_t} 12 \cdot \text{Complemento}_{i,t}
$$

---

## 5. Validación (la bisagra de credibilidad — NO omitir)

Antes de refinar cualquier bloque, el motor debe **reproducir el agregado observado 2025**. Un jurado técnico no cree una proyección a 45 años si el modelo no replica el presente.

**Targets observados 2025/2026 (verificar contra boletín CONSAR antes del envío):**

| Métrica | Valor de referencia | Fuente |
|---------|--------------------|--------|
| Tamaño del SAR (feb 2026) | ~**8.67 billones** de pesos (~20% del PIB) | CONSAR |
| Cuentas individuales | ~**69.9 millones** | CONSAR feb 2026 |
| Cuentas inhabilitadas | ~**5.1 millones** | CONSAR 4T 2024 |
| Cuentas resguardadas en FPB | ~**2.3 millones** | CONSAR 4T 2024 |
| FPB — constitución inicial | ~**40 mil millones** (cuentas inactivas 70+) | DOF/CONSAR 2024 |
| Gasto público en pensiones 2025 | ~**23.5% del gasto programable / ~6% del PIB** | CIEP |

El motor debe reproducir al menos: **tamaño agregado del SAR, distribución de saldos y número de cotizantes**. Figura de validación obligatoria: agregados simulados vs. observados.

---

## 6. Escenarios

Re-ejecución con parámetros distintos, **no** rearquitectura:

- **Base:** reforma 2020 según calendario, supuestos centrales.
- **Optimista:** mayor formalización, **+2 pp** en densidad de cotización.
- **Pesimista:** recesión / reversión parcial, **−2 pp** en densidad.

Reportar siempre **distribuciones e intervalos** (percentiles 10/25/50/75/90), no puntos. Análisis de sensibilidad obligatorio (tornado plot en Sección 8 — la densidad de cotización debe emerger como la variable más influyente; verificar).

---

## 7. Contratos de interfaz (resolver con el equipo)

Para no construir en el vacío ni reprocesar después, fijar formatos explícitos:

**ENTRADA — desde Sección 4 (Emiliano):**
- Matrices de transición laboral: formato, dimensiones, desagregación (¿por edad/género/escolaridad?).
- Distribuciones salariales calibradas por perfil.
- Parámetros de densidad de cotización.
> *Ask a la junta: ¿en qué formato exacto entrega Sección 4 estos objetos y cuándo?*

**SALIDA — hacia Secciones 7 y 8 (Ian, Fabiola):**
- Diseñar el schema de salida **ahora**. Propuesta mínima (un registro por agente-simulación):

```
agente_id | escenario | cohorte_retiro | genero | densidad_cotizacion |
saldo_final | pension_mensual | tasa_reemplazo | requiere_PG (bool) |
requiere_FPB (bool) | complemento_FPB_anual | edad_retiro | semilla
```

- Y un agregado por año-escenario para Sección 8:

```
anio | escenario | n_jubilados | n_bajo_piso | costo_FPB_total |
costo_FPB_p10 | costo_FPB_p90 | costo_como_pct_PIB
```

> *Ask a la junta: confirmar con Ian/Fabiola qué columnas necesitan para no rehacer el output.*

---

## 8. Entregables (en orden de construcción)

**Para la junta (walking skeleton, primera iteración):**
1. **Estructura de repo + README** con narrativa del proyecto y cómo correr.
2. **Notebook / script que corre end-to-end** y produce figuras sin intervención manual.
3. **Check contable** $\Delta S = A + R - C$ automático y pasando.
4. **Figura 1 — validación:** agregados simulados vs. observados 2025 (aunque sea cruda).
5. **Figura 2 — resultado preliminar:** distribución de tasa de reemplazo, cohorte 2050, escenario base.
6. **`BITACORA_DECISIONES.md`:** todo supuesto provisional marcado, con quién debe validarlo.
7. **`ASKS_JUNTA.md`:** bloqueos y decisiones que el equipo debe resolver (auditoría de datos, contratos de interfaz, agenda con Yáñez).

**Para la Sección 6 final (iteraciones posteriores):**
- Texto de 8 páginas (estructura 6.1–6.10 del plan de fase B).
- Repositorio público del motor, ejecutable.
- Figuras técnicas F1–F5 (arquitectura, matrices de transición, validación de salarios, trayectorias de ejemplo, validación agregada 2025).
- Especificación técnica formal en anexo (ecuaciones, calibraciones, supuestos, semillas).

---

## 9. Guardrails — qué NO hacer

- **NO** construyas los cinco bloques perfectos por separado antes de cerrar el loop. Eso garantiza cinco piezas a medias y cero cifras.
- **NO** te claves en debates de supuestos actuariales durante la construcción del skeleton. Marca `# ⚠️ SUPUESTO PROVISIONAL`, documenta en bitácora, y sigue. La corrección viene con Yáñez, después.
- **NO** bloquees el motor esperando a que CNSF/CONAPO entren al SDK. Son públicos; archivo estático y adelante.
- **NO** prometas para la primera junta: validación completa contra 2025, matrices ENOE reales, salarios AR(1), rendimientos estocásticos, Lee-Carter. Todo eso es Fase 2–3.
- **NO** reportes puntos donde debes reportar distribuciones.
- **NO** uses `localStorage`/almacenamiento de navegador; esto corre en Python local.

---

## 10. Stack y convenciones

- **Lenguaje:** Python. Vectorización con NumPy; Numba solo si el perfilado lo justifica (no premies velocidad antes de correctitud).
- **Reproducibilidad:** `random seeds` documentados y versionados; configuración de parámetros/escenarios/fuentes en archivo versionado (YAML/JSON).
- **Datos:** microdatos **no** se versionan en Git; se accede vía SDK `datos-mexico` o archivos estáticos referenciados. CNSF/CONAPO como estáticos si aún no están en el SDK.
- **Escala:** empieza con **5,000–10,000 agentes** para iterar rápido; escala a 50,000–100,000 solo cuando el motor valide.
- **Trazabilidad:** cualquier número debe rastrearse a su fuente o a una línea del notebook.
- **Entorno:** macOS ARM64, Homebrew, Node disponible. Repo del observatorio Datos México (org: github.com/Datos-Mexico).

---

## 11. Primer movimiento sugerido para Claude Code

1. Ejecuta la **Tarea 0** (auditoría del repo) y reporta la checklist de §2.
2. Propón la estructura de directorios del motor (p. ej. `motor/`, `data/`, `config/`, `notebooks/`, `outputs/`, `BITACORA_DECISIONES.md`, `ASKS_JUNTA.md`).
3. Construye el **walking skeleton** (§4, columna skeleton) sobre 5,000 agentes.
4. Implementa el **check contable** y córrelo.
5. Genera las **dos figuras** (validación cruda + distribución de tasa de reemplazo).
6. Redacta `BITACORA_DECISIONES.md` y `ASKS_JUNTA.md`.

No pidas permiso para cada paso; avanza el loop completo y reporta al final con los archivos generados, la checklist de auditoría, y la lista de asks para la junta.

---
*Documento de handoff · Sección 6 · Equipo Datos México · ITAM · generado para transferir contexto a Claude Code.*
