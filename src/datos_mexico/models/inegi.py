"""Modelos del namespace INEGI: capa de cubos, tabulados explorables, Censos Económicos y bancos de
indicadores.
"""

from __future__ import annotations

from typing import Any

from datos_mexico.models.base import DatosMexicoModel


class CuboResumen(DatosMexicoModel):
    """Un cubo del catálogo (``GET /api/v1/cubos``)."""

    clave: str
    nombre: str
    tema: str
    descripcion: str
    fuente: str
    fuente_url: str
    licencia: str


class TemaCubos(DatosMexicoModel):
    """Un tema del catálogo con sus cubos."""

    clave: str
    nombre: str
    descripcion: str
    cubos: list[CuboResumen]


class CatalogoCubos(DatosMexicoModel):
    """Catálogo completo de cubos por tema."""

    n_cubos: int
    temas: list[TemaCubos]

    def todos(self) -> list[CuboResumen]:
        """Los cubos de todos los temas, en el orden del explorador."""
        return [c for t in self.temas for c in t.cubos]


class MedidaCubo(DatosMexicoModel):
    clave: str
    titulo: str
    unidad: str | None = None
    sumable: bool
    decimales: int | None = None
    descripcion: str | None = None


class DimensionCubo(DatosMexicoModel):
    clave: str
    titulo: str
    tipo: str
    geo: str | None = None
    padre: str | None = None
    descripcion: str | None = None


class FichaCubo(CuboResumen):
    """Ficha de un cubo (``GET /api/v1/cubos/{cubo}``): medidas, dimensiones, filas y notas."""

    filas: int
    corte: str | None = None
    medidas: list[MedidaCubo]
    dimensiones: list[DimensionCubo]
    notas: list[str]
    predeterminado: dict[str, Any]


class ColumnaResultado(DatosMexicoModel):
    clave: str
    titulo: str
    tipo: str
    dimension: str | None = None
    unidad: str | None = None
    sumable: bool | None = None


class ResultadoCubo(DatosMexicoModel):
    """Resultado de una consulta (``GET /api/v1/cubos/{cubo}/datos``)."""

    cubo: str
    consulta: dict[str, Any]
    columnas: list[ColumnaResultado]
    filas: list[dict[str, Any]]
    n: int
    limitado: bool

    def to_pandas(self) -> Any:
        """Las filas como ``pandas.DataFrame`` (requiere pandas)."""
        import pandas as pd

        return pd.DataFrame(self.filas, columns=[c.clave for c in self.columnas])


class MiembroCubo(DatosMexicoModel):
    id: str | int
    nombre: str
    n: int | None = None


class MiembrosCubo(DatosMexicoModel):
    cubo: str
    dimension: str
    n: int
    limitado: bool
    items: list[MiembroCubo]


class TabuladosFamilia(DatosMexicoModel):
    """Una familia de tabulados explorables (``GET /api/v1/inegi/tabulados``)."""

    familia: str
    nombre: str
    programa: str
    edicion: str
    fuente_url: str
    archivos: int
    cuadros: int
    celdas: int
    corte: str | None = None
    cuadros_url: str
    cubo: str


class TabuladosFamilias(DatosMexicoModel):
    n: int
    items: list[TabuladosFamilia]


class TabuladoCuadroFicha(DatosMexicoModel):
    """Ficha de un cuadro: título, nombres de sus dimensiones de fila y encabezados de columna."""

    cuadro: str
    archivo: str
    hoja: str
    titulo: str
    dimensiones: list[str]
    columnas: list[str]
    celdas: int
    sha256: str
    archivo_url: str | None = None


class TabuladosCuadros(DatosMexicoModel):
    familia: str
    nombre: str
    n: int
    items: list[TabuladoCuadroFicha]


class TabuladoCelda(DatosMexicoModel):
    """Una celda del cuadro publicado: categorías de la fila (d1…d5), columna, valor u texto y
    posición.
    """

    d1: str
    d2: str
    d3: str
    d4: str
    d5: str
    columna: str
    valor: float | int | None = None
    texto: str | None = None
    orden: int


class TabuladoCuadro(DatosMexicoModel):
    """Un cuadro con sus celdas (``GET /api/v1/inegi/tabulados/{familia}/{cuadro}``)."""

    familia: str
    cuadro: TabuladoCuadroFicha
    total: int
    limit: int
    offset: int
    items: list[TabuladoCelda]

    def to_pandas(self) -> Any:
        """Las celdas como ``pandas.DataFrame`` con las dimensiones nombradas como en el cuadro
        (requiere pandas).
        """
        import pandas as pd

        nombres = list(self.cuadro.dimensiones) + [""] * 5
        filas = []
        for c in self.items:
            fila: dict[str, Any] = {}
            for i, v in enumerate((c.d1, c.d2, c.d3, c.d4, c.d5)):
                if nombres[i]:
                    fila[nombres[i]] = v
            fila["columna"] = c.columna
            fila["valor"] = c.valor
            fila["texto"] = c.texto
            fila["orden"] = c.orden
            filas.append(fila)
        return pd.DataFrame(filas)


class SaicAnio(DatosMexicoModel):
    anio: str
    censo: str
    filas: int
    filas_municipales: int | None = None
    valores: int
    fuente: str
    archivos: int | None = None
    completo: bool
    parquet_url: str | None = None
    unidades_economicas: float | int | None = None
    personal_ocupado: float | int | None = None


class SaicResumen(DatosMexicoModel):
    """Censos Económicos 2004-2024: qué hay por año censal y cómo se verificó (``GET
    /api/v1/inegi/saic``).
    """

    fuente: str
    fuente_url: str
    anios: list[SaicAnio]
    variables: int
    variables_municipales: list[str]
    actividades: int


class SaicDatos(DatosMexicoModel):
    """Filas de los Censos Económicos con las variables pedidas (``/api/v1/inegi/saic/datos``)."""

    anio: str
    variables: list[str]
    total: int
    limit: int
    offset: int
    items: list[dict[str, Any]]


class Observacion(DatosMexicoModel):
    """Una observación de un indicador del Banco de Indicadores o de una serie del BIE."""

    periodo: str | int
    valor: float | int | None = None


class Observaciones(DatosMexicoModel):
    observaciones: list[Observacion]
