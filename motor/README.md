# Motor de microsimulación actuarial — Sección 6

Walking skeleton del motor del paper Amafore-ITAM 2026: proyecta la
distribución de pensiones del SAR y el costo fiscal del FPB (2026–2070)
con trabajadores sintéticos. Ver `BRIEF_MOTOR_SECCION6.md` (contexto),
`BITACORA_DECISIONES.md` (supuestos) y `ASKS_JUNTA.md` (bloqueos).

## Cómo correr

```bash
uv venv .venv --python 3.12
uv pip install -p .venv/bin/python -e . numpy pandas matplotlib pyyaml
.venv/bin/python -m motor.run_skeleton          # con API en vivo
.venv/bin/python -m motor.run_skeleton --sin-api  # solo fallbacks estáticos
```

Corre 3 escenarios × 5 semillas (~1.2 s), verifica la identidad contable
**ΔS = A + R − C en cada periodo** (aborta si falla), valida contra
agregados CONSAR 2025 vía `client.consar` y escribe todo en `outputs/`.

## Estructura

| Archivo | Qué hace |
|---|---|
| `config.yaml` | Parámetros, semillas y escenarios versionados |
| `reglas_sar.py` | Reglas SAR (ley): aportaciones, cuota social, semanas, comisiones, anualidad |
| `datos.py` | Carga EMSSA-09/CONAPO estáticos + CONSAR/ENOE vía SDK (con fallback) |
| `motor.py` | Loop de acumulación vectorizado + check contable |
| `validacion.py` | Simulado vs observado 2025 |
| `figuras.py` | Figura 1 (validación) y Figura 2 (tasa de reemplazo 2050) |
| `run_skeleton.py` | Orquestador end-to-end |
| `data/` | Estáticos CNSF/CONAPO (fuentes en `data/README.md`) |
| `outputs/` | `agentes.csv`, `agregados_anuales.csv`, `validacion_2025.csv`, `ledger_contable_base.csv`, figuras |

## Salidas (contratos §7 del brief)

- `agentes.csv`: un registro por agente-simulación (`agente_id, escenario,
  cohorte_retiro, genero, densidad_cotizacion, saldo_final, pension_mensual,
  tasa_reemplazo, requiere_PG, requiere_FPB, complemento_FPB_anual,
  edad_retiro, semilla`).
- `agregados_anuales.csv`: por año-escenario (`n_jubilados, n_bajo_piso,
  costo_FPB_total_mm, costo_FPB_p10/p90_mm, costo_como_pct_PIB`).
