import logging
from django.db import transaction
from registry.models import Grupo, Participante, Tutor

logger = logging.getLogger(__name__)

class GrupoService:
    """
    Servicio para gestionar el ciclo de vida de los Grupos (Equipos).
    """

    @staticmethod
    def crear_grupo(usuario, nombre_grupo, tutor_id=None, cedulas_participantes=None):
        """
        Crea un grupo con sus tutores y participantes.
        """
        if not nombre_grupo or not nombre_grupo.strip():
            raise ValueError("El nombre del grupo es obligatorio")

        with transaction.atomic():
            nuevo_grupo = Grupo.objects.create(
                nombre=nombre_grupo.strip(),
                usuario_creador=usuario,
                criterio="proyecto",
            )

            if tutor_id:
                try:
                    tutor = Tutor.objects.get(id=tutor_id, status="activo")
                    nuevo_grupo.tutores.add(tutor)
                except Tutor.DoesNotExist:
                    logger.warning(f"Tutor {tutor_id} no encontrado.")

            if cedulas_participantes:
                for cedula in cedulas_participantes:
                    if cedula.strip():
                        try:
                            participante = Participante.objects.get(cedula=cedula.strip())
                            nuevo_grupo.participantes.add(participante)
                        except Participante.DoesNotExist:
                            logger.warning(f"Participante con cédula {cedula} no encontrado.")

            return nuevo_grupo

    @staticmethod
    def editar_grupo(grupo_id, usuario, nuevo_nombre=None, eliminar_indices=None, nuevas_cedulas=None):
        """
        Edita un grupo existente.
        """
        try:
            grupo = Grupo.objects.get(id=grupo_id, usuario_creador=usuario)
        except Grupo.DoesNotExist:
            raise ValueError("El Equipo no existe o no tienes permiso para editarlo.")

        with transaction.atomic():
            if nuevo_nombre:
                grupo.nombre = nuevo_nombre
                grupo.save()

            if eliminar_indices:
                participantes_actuales = list(grupo.participantes.all())
                for idx_str in eliminar_indices:
                    try:
                        idx = int(idx_str)
                        if idx < len(participantes_actuales):
                            grupo.participantes.remove(participantes_actuales[idx])
                    except (ValueError, IndexError):
                        pass

            if nuevas_cedulas:
                for cedula in nuevas_cedulas:
                    if cedula.strip():
                        try:
                            participante = Participante.objects.get(cedula=cedula.strip())
                            grupo.participantes.add(participante)
                        except Participante.DoesNotExist:
                            logger.warning(f"Participante con cédula {cedula} no encontrado.")
            
            return grupo

    @staticmethod
    def eliminar_grupo(grupo_id, usuario):
        """
        Elimina un grupo y sus relaciones.
        """
        try:
            grupo = Grupo.objects.get(id=grupo_id, usuario_creador=usuario)
        except Grupo.DoesNotExist:
            raise ValueError("El equipo no existe o no tienes permiso para eliminarlo.")

        with transaction.atomic():
            grupo.participantes.clear()
            grupo.delete()
