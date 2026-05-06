"""Namespace ``demo``: dataset didáctico del curso ITAM Bases de Datos."""

from __future__ import annotations

from datos_mexico._namespace import BaseNamespace
from datos_mexico.models.demo import (
    EstudianteRow,
    EstudiantesResponse,
    ResumenResponse,
)


class DemoNamespace(BaseNamespace):
    """Endpoints del dataset ``demo`` (curso ITAM "Bases de Datos sección 001").

    Estos endpoints exponen una tabla didáctica usada en clase. **No** son
    datos del observatorio Datos México: aparecen aislados en su propio
    namespace para evitar confusión con los datasets de servidores
    públicos, pensiones y hogares.
    """

    def estudiantes(self) -> EstudiantesResponse:
        """Lista del curso completo (estudiantes + profesor).

        Endpoint: ``GET /api/v1/demo/estudiantes``
        """
        return self._get_validated(
            "/api/v1/demo/estudiantes", EstudiantesResponse
        )

    def estudiante(self, estudiante_id: int) -> EstudianteRow:
        """Detalle de una persona del curso por ID.

        Endpoint: ``GET /api/v1/demo/estudiantes/{id}``

        Raises:
            NotFoundError: Si no existe un registro con ese ID.
        """
        return self._get_validated(
            f"/api/v1/demo/estudiantes/{estudiante_id}", EstudianteRow
        )

    def resumen(self) -> ResumenResponse:
        """Agregados de la KPI bar del dashboard ``/demo``.

        Endpoint: ``GET /api/v1/demo/resumen``
        """
        return self._get_validated(
            "/api/v1/demo/resumen", ResumenResponse
        )
