"""Construye la serie anual de rendimiento BRUTO real del sistema 1997-2025.

Genera ``consar_rendimiento_bruto_anual.csv`` a partir de:

- ``client.consar.precios_gestion_serie`` (precio de gestión interna, diario,
  1997-07 → 2025-12, por AFORE x SIEFORE). El precio de gestión es BRUTO
  (antes de comisiones): verificado empíricamente — CAGR gestión ~11.2% vs
  NAV ~10.1%, brecha ≈ serie de comisiones CONSAR. Las comisiones se cargan
  explícitas en el loop del motor (C), por eso aquí NO se netean.
- ``client.consar.recursos_por_afore`` (pesos por activos a nivel AFORE,
  mensual desde 1998-05).
- ``motor/data/inpc_mensual.csv`` (INPC general SP1, Banxico SIE) para
  deflactar: r_real = (1 + r_nominal) / (1 + pi) - 1.

Método (bitácora #23):
- Retorno del año t por par = precio del último día hábil de t / último día
  hábil de t-1, menos 1.
- Agregación: promedio simple entre SIEFOREs dentro de cada AFORE (los
  activos por SIEFORE no existen históricamente en el SDK — TODO Fase 2),
  ponderado por recursos administrados entre AFOREs (dic del año t-1;
  1997-1998 sin dato de pesos → pesos iguales).
- 1997: retorno jul-dic observado sin anualizar (el SAR arranca en jul-97;
  saldos del año ínfimos, efecto trivial), deflactado con INPC jul→dic.

Uso:  .venv/bin/python motor/data/build_rendimientos_brutos.py
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from datos_mexico import DatosMexico

SALIDA = Path(__file__).parent / "consar_rendimiento_bruto_anual.csv"
INPC = Path(__file__).parent / "inpc_mensual.csv"
ANIOS = range(1997, 2026)


def cargar_inpc() -> dict[tuple[int, int], float]:
    with INPC.open() as f:
        return {
            (int(r["anio"]), int(r["mes"])): float(r["inpc"])
            for r in csv.DictReader(f)
        }


def main() -> None:
    inpc = cargar_inpc()

    with DatosMexico() as client:
        # 1. universo de pares (AFORE x SIEFORE) desde snapshots de varias épocas
        pares: set[tuple[str, str]] = set()
        for fecha in ("1997-12-01", "2003-12-01", "2010-12-01", "2017-11-01", "2025-12-01"):
            try:
                snap = client.consar.precios_gestion_snapshot(fecha)
                pares |= {(f.afore_codigo, f.siefore_slug) for f in snap.filas}
            except Exception:
                continue
        print(f"universo: {len(pares)} pares AFORE x SIEFORE")

        # 2. precio de cierre de año por par (último día disponible de cada año)
        cierre: dict[tuple[str, str], dict[int, float]] = {}
        base_1997: dict[tuple[str, str], float] = {}
        for i, (afore, siefore) in enumerate(sorted(pares), 1):
            try:
                serie = client.consar.precios_gestion_serie(
                    afore_codigo=afore, siefore_slug=siefore
                ).serie
            except Exception:
                continue
            por_anio: dict[int, float] = {}
            for punto in serie:
                por_anio[punto.fecha.year] = float(punto.precio)  # queda el último
            cierre[(afore, siefore)] = por_anio
            primero = serie[0]
            if primero.fecha.year == 1997:
                base_1997[(afore, siefore)] = float(primero.precio)
            if i % 20 == 0:
                print(f"  {i}/{len(pares)} series descargadas…")

        # 3. pesos por AFORE (recursos administrados, dic del año previo)
        pesos_afore: dict[int, dict[str, float]] = {}
        for anio in ANIOS:
            try:
                r = client.consar.recursos_por_afore(f"{anio - 1}-12-01")
                pesos_afore[anio] = {
                    f.afore_codigo: float(f.recursos_administrados_mm)
                    for f in r.afores
                }
            except Exception:
                pesos_afore[anio] = {}

    # 4. retorno anual agregado
    filas_csv = []
    for anio in ANIOS:
        # retorno por par
        ret_por_afore: dict[str, list[float]] = defaultdict(list)
        for (afore, siefore), precios in cierre.items():
            p0 = (
                base_1997.get((afore, siefore))
                if anio == 1997
                else precios.get(anio - 1)
            )
            p1 = precios.get(anio)
            if p0 and p1 and p0 > 0:
                ret_por_afore[afore].append(p1 / p0 - 1.0)
        if not ret_por_afore:
            continue
        # promedio simple entre siefores dentro de la afore
        ret_afore = {a: sum(v) / len(v) for a, v in ret_por_afore.items()}
        # ponderado por activos entre afores
        w = pesos_afore.get(anio, {})
        w = {a: w.get(a, 0.0) for a in ret_afore}
        total = sum(w.values())
        if total > 0:
            r_nom = sum(ret_afore[a] * w[a] for a in ret_afore) / total
            metodo_w = "activos_afore"
        else:
            r_nom = sum(ret_afore.values()) / len(ret_afore)
            metodo_w = "pesos_iguales"

        # inflación dic-dic (1997: jul-dic, ventana igual al retorno)
        if anio == 1997:
            pi = inpc[(1997, 12)] / inpc[(1997, 7)] - 1.0
        else:
            pi = inpc[(anio, 12)] / inpc[(anio - 1, 12)] - 1.0
        r_real = (1.0 + r_nom) / (1.0 + pi) - 1.0
        filas_csv.append(
            {
                "anio": anio,
                "r_nominal_bruto": round(r_nom, 6),
                "inflacion_dic_dic": round(pi, 6),
                "r_real_bruto": round(r_real, 6),
                "n_afores": len(ret_afore),
                "ponderacion": metodo_w,
            }
        )

    with SALIDA.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas_csv[0].keys()))
        w.writeheader()
        w.writerows(filas_csv)
    print(f"\n{SALIDA.name}: {len(filas_csv)} años")
    for r in filas_csv:
        print(f"  {r['anio']}: nominal {r['r_nominal_bruto']:+.2%} | "
              f"inflación {r['inflacion_dic_dic']:+.2%} | real {r['r_real_bruto']:+.2%}")


if __name__ == "__main__":
    main()
