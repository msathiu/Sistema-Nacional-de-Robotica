import logging
from datetime import datetime
from django.db.models import Count, F, Q
from django.db.models.functions import Coalesce, ExtractMonth
from registry.models import (
    Participante,
    Institucion,
    Club,
    Evento,
    MembresiaClu,
    Grupo,
    ClubLineaInvestigacion,
    TutorInstitucion,
)

logger = logging.getLogger(__name__)

class ReportService:
    """
    Servicio especializado para la generación de reportes, métricas y estadísticas.
    Centraliza la lógica de agregaciones para dashboards y reportes gerenciales.
    """

    @staticmethod
    def get_dashboard_stats(user_type, user_estado=None):
        """
        Calcula de forma optimizada todas las métricas para el dashboard administrativo.
        Usa agregaciones de Django para minimizar las consultas a la base de datos.
        """
        filtros_inst = Q(eliminado=False)
        filtros_club = Q(activo=True)
        filtros_part = Q()

        # 1. Soberanía Territorial: Filtrar por estado si es regional
        if user_type == "fed_regional" and user_estado:
            filtros_inst &= Q(estado=user_estado)
            filtros_club &= Q(institucion_creadora__estado=user_estado)
            filtros_part &= Q(estado=user_estado)

        # 2. Métricas de Participantes (Optimizado con aggregate)
        part_agg = Participante.objects.filter(filtros_part).aggregate(
            total=Count('id'),
            mujeres=Count('id', filter=Q(sexo='F')),
            hombres=Count('id', filter=Q(sexo='M'))
        )
        total_participantes = part_agg['total']
        total_p_safe = total_participantes or 1
        porcentaje_mujeres = round((part_agg['mujeres'] / total_p_safe) * 100)
        porcentaje_hombres = round((part_agg['hombres'] / total_p_safe) * 100)

        # 3. Métricas de Instituciones y Clubes (Optimizado)
        inst_agg = Institucion.objects.filter(filtros_inst).aggregate(
            total=Count('id'),
            pendientes=Count('id', filter=~Q(estatus="aprobado", activa=True)),
            cobertura=Count('estado', distinct=True)
        )
        
        club_agg = Club.objects.filter(filtros_club).aggregate(
            aprobados=Count('id', filter=Q(status="aprobado")),
            pendientes=Count('id', filter=Q(status="pendiente"))
        )

        try:
            membresias_pendientes = MembresiaClu.objects.filter(estado="pendiente").count()
        except Exception:
            membresias_pendientes = 0

        total_eventos = Evento.objects.count()

        # 4. Equipos y Tutores (Optimizado)
        filtros_equipo = Q()
        if user_type == "fed_regional" and user_estado:
            filtros_equipo = Q(institucion__estado=user_estado)
        
        total_equipos = Grupo.objects.filter(filtros_equipo).count()

        # Contar tutores "creados"/vinculados (aunque aún no estén asignados a grupos)
        # evitando duplicidad por múltiples vinculaciones con DISTINCT por tutor_id.
        # Alineado con el listado: por defecto se contabiliza todo (activo/inactivo/etc),
        # solo se excluye si el usuario aplica filtros explícitos en la UI.
        tutor_inst_qs = TutorInstitucion.objects.all()
        if user_type == "fed_regional" and user_estado:
            # Equivalente a la lógica usada en `lista_tutores` para fed_regional:
            # - vinculaciones regionales por `estado`
            # - vinculaciones institucionales por `institucion.estado`
            tutor_inst_qs = tutor_inst_qs.filter(Q(estado=user_estado) | Q(institucion__estado=user_estado))

        total_tutores = tutor_inst_qs.values("tutor_id").distinct().count()

        # 5. Curva de Inscripción Mensual (Año Actual)
        year_actual = datetime.now().year
        registros_por_mes = (
            Institucion.objects.filter(filtros_inst, fecha_registro__year=year_actual)
            .annotate(mes=ExtractMonth("fecha_registro"))
            .values("mes")
            .annotate(total=Count("id"))
            .order_by("mes")
        )
        data_crecimiento = [0] * 12
        for r in registros_por_mes:
            if r["mes"]:
                data_crecimiento[r["mes"] - 1] = r["total"]

        # 6. Especialidades de Clubes (Radar Chart)
        clubes_stats = (
            ClubLineaInvestigacion.objects.filter(club__in=Club.objects.filter(filtros_club))
            .values("linea__nombre")
            .annotate(total=Count("id"))
            .order_by("-total")
        )
        clubes_labels = [c["linea__nombre"] or "General" for c in clubes_stats]
        clubes_data = [c["total"] for c in clubes_stats]
        if not clubes_labels:
            clubes_labels, clubes_data = ["Sin Datos"], [0]

        # 7. Distribución de Tutores por Estado (Top 5)
        # Se deriva del estado de la vinculación del tutor:
        # - `regional` => TutorInstitucion.estado__nombre
        # - `institucional` => TutorInstitucion.institucion.estado__nombre
        # - `central` => sin estado (se excluye del gráfico)
        tutores_stats = (
            tutor_inst_qs.annotate(
                estado_nombre=Coalesce(
                    F("estado__nombre"),
                    F("institucion__estado__nombre"),
                )
            )
            .exclude(estado_nombre__isnull=True)
            .values("estado_nombre")
            .annotate(total=Count("tutor_id", distinct=True))
            .order_by("-total")[:5]
        )

        tutores_labels = [t["estado_nombre"] for t in tutores_stats if t["estado_nombre"]]
        tutores_data = [t["total"] for t in tutores_stats if t["estado_nombre"]]

        # 8. Datos del Mapa
        conteo_db = Institucion.objects.filter(filtros_inst).values("estado__nombre").annotate(total=Count("id"))
        mapa_data = {registro["estado__nombre"]: registro["total"] for registro in conteo_db if registro["estado__nombre"]}

        return {
            "total_participantes": total_participantes,
            "total_instituciones": inst_agg['total'],
            "total_clubes": club_agg['aprobados'],
            "clubes_aprobados": club_agg['aprobados'],
            "clubes_pendientes": club_agg['pendientes'],
            "membresias_pendientes": membresias_pendientes,
            "total_tutores": total_tutores,
            "total_equipos": total_equipos,
            "total_eventos": total_eventos,
            "pendientes_aprobacion": inst_agg['pendientes'],
            "cobertura_nacional": inst_agg['cobertura'],
            "data_crecimiento": data_crecimiento,
            "porcentaje_mujeres": porcentaje_mujeres,
            "porcentaje_hombres": porcentaje_hombres,
            "clubes_labels": clubes_labels,
            "clubes_data": clubes_data,
            "tutores_labels": tutores_labels,
            "tutores_data": tutores_data,
            "mapa_data": mapa_data,
        }

    @staticmethod
    def get_institutional_stats(user, institution):
        """
        Calcula métricas específicas para una institución.
        """
        hoy = datetime.now().date()
        
        # Agregaciones para institución
        mis_grupos = Grupo.objects.filter(usuario_creador=user, activo=True)
        
        total_mis_participantes = (
            Participante.objects.filter(
                vinculaciones__institucion=institution, 
                vinculaciones__status="activo"
            )
            .distinct()
            .count()
        )

        # Eventos y Clubes
        eventos_agg = Evento.objects.filter(activo=True).aggregate(
            disponibles=Count('id', filter=Q(fecha__gte=hoy, estado_evento="abierto")),
            asignados=Count('id', filter=Q(grupos_inscritos__usuario_creador=user))
        )

        mis_clubes_agg = Club.objects.filter(institucion_creadora=institution).aggregate(
            total=Count('id'),
            aprobados=Count('id', filter=Q(status="aprobado", activo=True))
        )

        return {
            "total_mis_grupos": mis_grupos.count(),
            "total_mis_participantes": total_mis_participantes,
            "eventos_disponibles": eventos_agg['disponibles'],
            "eventos_asignados": eventos_agg['asignados'],
            "total_mis_clubes": mis_clubes_agg['total'],
            "mis_clubes_aprobados": mis_clubes_agg['aprobados'],
        }
