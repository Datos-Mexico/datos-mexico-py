"""Modelos Pydantic del namespace ``demo``.

Datos del curso ITAM "Bases de Datos sección 001" usados como caso de
estudio en clase. NO son datos públicos del observatorio Datos México;
están aislados en este namespace para señalizar su naturaleza didáctica.
"""

from __future__ import annotations

from datos_mexico._helpers import Money
from datos_mexico.models.base import DatosMexicoModel


class EstudianteRow(DatosMexicoModel):
    """Item de ``GET /api/v1/demo/estudiantes`` y ``.../estudiantes/{id}``.

    Attributes:
        id: ID interno del registro.
        nombre_completo: Nombre completo en mayúsculas.
        rol: ``"estudiante"`` o ``"profesor"``.
        tipo: ``"profesor"``, ``"equipo"`` o ``"estudiante"``.
        seccion: Identificador de la sección del curso.
        sueldo_diario_mxn: Sueldo diario en MXN, ``Decimal``.
        reclamar_bono: Si la persona reclamó el bono didáctico.
        fecha_creacion: Timestamp ISO con microsegundos. Se mantiene como
            ``str`` porque el SDK no manipula este campo aritméticamente.
        fecha_actualizacion: Timestamp ISO con microsegundos.
    """

    id: int
    nombre_completo: str
    rol: str
    tipo: str
    seccion: str
    sueldo_diario_mxn: Money
    reclamar_bono: bool
    fecha_creacion: str
    fecha_actualizacion: str


class EstudiantesResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/demo/estudiantes``."""

    count: int
    estudiantes: list[EstudianteRow]
    seccion: str
    fuente: str = "demo.curso_bd (PostgreSQL Neon)"


class ResumenResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/demo/resumen``.

    Agregados que el dashboard ``/demo`` muestra en la KPI bar (total
    empleados, bonos reclamados, montos derivados).

    Attributes:
        total_empleados: Cantidad total de filas en el padrón demo.
        bonos_reclamados: Cantidad de personas que reclamaron el bono.
        bono_unitario_mxn: Valor del bono individual (default 50000).
        monto_distribuido_mxn: Monto ya distribuido en bonos.
        monto_disponible_mxn: Monto pendiente de reclamo.
        monto_total_posible_mxn: Monto total si todos reclamaran.
        nomina_diaria_total_mxn: Nómina diaria agregada.
        fecha: Timestamp ISO de la consulta. Como ``str`` por consistencia
            con los demás timestamps del namespace.
    """

    total_empleados: int
    bonos_reclamados: int
    bono_unitario_mxn: int = 50000
    monto_distribuido_mxn: int
    monto_disponible_mxn: int
    monto_total_posible_mxn: int
    nomina_diaria_total_mxn: Money
    fecha: str
