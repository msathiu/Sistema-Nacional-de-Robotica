import logging

from django.db.models import Count, F, Q
from django.db.models.functions import Coalesce, ExtractMonth
from django.utils import timezone
from registry.models import (
    Club,
    ClubLineaInvestigacion,
    EstadoEvento,
    Evento,
    Grupo,
    InscripcionGrupoEvento,
    Institucion,
    MembresiaClu,
    Participante,
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
            total=Count("id"),
            mujeres=Count("id", filter=Q(sexo="F")),
            hombres=Count("id", filter=Q(sexo="M")),
        )
        total_participantes = part_agg["total"]
        total_p_safe = total_participantes or 1
        porcentaje_mujeres = round((part_agg["mujeres"] / total_p_safe) * 100)
        porcentaje_hombres = round((part_agg["hombres"] / total_p_safe) * 100)

        # 3. Métricas de Instituciones y Clubes (Optimizado)
        inst_agg = Institucion.objects.filter(filtros_inst).aggregate(
            total=Count("id"),
            pendientes=Count("id", filter=~Q(estatus="aprobado", activa=True)),
            cobertura=Count("estado", distinct=True),
        )

        club_agg = Club.objects.filter(filtros_club).aggregate(
            aprobados=Count("id", filter=Q(status="aprobado")),
            pendientes=Count("id", filter=Q(status="pendiente")),
        )

        try:
            membresias_pendientes = MembresiaClu.objects.filter(
                estado="pendiente"
            ).count()
        except Exception:
            membresias_pendientes = 0

        total_eventos = Evento.objects.exclude(
            Q(estado_evento="borrador")
            & (Q(institucion__isnull=False) | Q(club_organizador__isnull=False))
        ).count()

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
            tutor_inst_qs = tutor_inst_qs.filter(
                Q(estado=user_estado) | Q(institucion__estado=user_estado)
            )

        total_tutores = tutor_inst_qs.values("tutor_id").distinct().count()

        # 5. Curva de Inscripción Mensual (Año Actual)
        year_actual = timezone.now().year
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
            ClubLineaInvestigacion.objects.filter(
                club__in=Club.objects.filter(filtros_club)
            )
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

        tutores_labels = [
            t["estado_nombre"] for t in tutores_stats if t["estado_nombre"]
        ]
        tutores_data = [t["total"] for t in tutores_stats if t["estado_nombre"]]

        # 8. Datos del Mapa
        conteo_db = (
            Institucion.objects.filter(filtros_inst)
            .values("estado__nombre")
            .annotate(total=Count("id"))
        )
        mapa_data = {
            registro["estado__nombre"]: registro["total"]
            for registro in conteo_db
            if registro["estado__nombre"]
        }

        # 9. Instituciones activas y aprobadas por estado
        inst_por_estado_qs = (
            Institucion.objects.filter(filtros_inst)
            .values("estado__nombre")
            .annotate(
                total=Count("id"),
                aprobadas=Count("id", filter=Q(estatus="aprobado", activa=True)),
            )
            .exclude(estado__nombre__isnull=True)
            .order_by("-aprobadas")[:10]
        )
        inst_estados_labels = [r["estado__nombre"] for r in inst_por_estado_qs]
        inst_estados_total = [r["total"] for r in inst_por_estado_qs]
        inst_estados_aprobadas = [r["aprobadas"] for r in inst_por_estado_qs]

        # 10. Eventos por estado_evento y tipo_evento
        ESTADOS_EVENTO = [
            "borrador",
            "revision",
            "abierto",
            "en_proceso",
            "finalizado",
            "rechazado",
            "cancelado",
        ]
        eventos_qs = Evento.objects.filter(activo=True)
        if user_type == "fed_regional" and user_estado:
            eventos_qs = eventos_qs.filter(estado=user_estado)
        eventos_tipo_estado = eventos_qs.values(
            "tipo_evento", "estado_evento"
        ).annotate(total=Count("id"))
        # Construir matrices separadas para institucional y club
        _ev_map = {
            (r["tipo_evento"], r["estado_evento"]): r["total"]
            for r in eventos_tipo_estado
        }
        eventos_estados_labels = ESTADOS_EVENTO
        eventos_institucional_data = [
            _ev_map.get(("institucional", s), 0) for s in ESTADOS_EVENTO
        ]
        eventos_club_data = [_ev_map.get(("club", s), 0) for s in ESTADOS_EVENTO]

        # 11. Instituciones por tipo
        inst_tipo_qs = (
            Institucion.objects.filter(
                filtros_inst,
                activa=True,
                estatus="aprobado",
            )
            .values("tipo_institucion")
            .annotate(total=Count("id"))
            .order_by("-total")
        )
        inst_tipo_labels = [r["tipo_institucion"] or "Otro" for r in inst_tipo_qs]
        inst_tipo_data = [r["total"] for r in inst_tipo_qs]

        # 12. Participantes por grado escolar
        grado_qs = (
            Participante.objects.filter(filtros_part)
            .exclude(grado_escolar__isnull=True)
            .exclude(grado_escolar="")
            .values("grado_escolar")
            .annotate(total=Count("id"))
            .order_by("grado_escolar")
        )
        grado_labels = [r["grado_escolar"] for r in grado_qs]
        grado_data = [r["total"] for r in grado_qs]

        # 13. Equipos por estado_grupo y criterio
        equipos_qs = Grupo.objects.filter(filtros_equipo)
        equipos_estado_qs = equipos_qs.values("criterio", "estado_grupo").annotate(
            total=Count("id")
        )
        CRITERIOS = ["edad", "nivel_educativo", "mixto"]
        ESTADOS_GRUPO = ["editable", "inscrito", "finalizado"]
        _eq_map = {
            (r["criterio"], r["estado_grupo"]): r["total"] for r in equipos_estado_qs
        }
        equipos_criterio_labels = ESTADOS_GRUPO
        equipos_edad_data = [_eq_map.get(("edad", s), 0) for s in ESTADOS_GRUPO]
        equipos_nivel_data = [
            _eq_map.get(("nivel_educativo", s), 0) for s in ESTADOS_GRUPO
        ]
        equipos_mixto_data = [_eq_map.get(("mixto", s), 0) for s in ESTADOS_GRUPO]

        # 14. Top 10 eventos con más inscripciones
        inscripciones_qs = (
            InscripcionGrupoEvento.objects.filter(activo=True)
            .values("evento__nombre")
            .annotate(total=Count("id"))
            .order_by("-total")[:10]
        )
        inscripciones_labels = [r["evento__nombre"] for r in inscripciones_qs]
        inscripciones_data = [r["total"] for r in inscripciones_qs]

        return {
            "total_participantes": total_participantes,
            "total_instituciones": inst_agg["total"],
            "total_clubes": club_agg["aprobados"],
            "clubes_aprobados": club_agg["aprobados"],
            "clubes_pendientes": club_agg["pendientes"],
            "membresias_pendientes": membresias_pendientes,
            "total_tutores": total_tutores,
            "total_equipos": total_equipos,
            "total_eventos": total_eventos,
            "pendientes_aprobacion": inst_agg["pendientes"],
            "cobertura_nacional": inst_agg["cobertura"],
            "data_crecimiento": data_crecimiento,
            "porcentaje_mujeres": porcentaje_mujeres,
            "porcentaje_hombres": porcentaje_hombres,
            "clubes_labels": clubes_labels,
            "clubes_data": clubes_data,
            "tutores_labels": tutores_labels,
            "tutores_data": tutores_data,
            "mapa_data": mapa_data,
            "inst_estados_labels": inst_estados_labels,
            "inst_estados_total": inst_estados_total,
            "inst_estados_aprobadas": inst_estados_aprobadas,
            # Gráfico 10: Eventos por tipo y estado
            "eventos_estados_labels": eventos_estados_labels,
            "eventos_institucional_data": eventos_institucional_data,
            "eventos_club_data": eventos_club_data,
            # Gráfico 11: Instituciones por tipo
            "inst_tipo_labels": inst_tipo_labels,
            "inst_tipo_data": inst_tipo_data,
            # Gráfico 12: Participantes por grado escolar
            "grado_labels": grado_labels,
            "grado_data": grado_data,
            # Gráfico 13: Equipos por criterio y estado
            "equipos_criterio_labels": equipos_criterio_labels,
            "equipos_edad_data": equipos_edad_data,
            "equipos_nivel_data": equipos_nivel_data,
            "equipos_mixto_data": equipos_mixto_data,
            # Gráfico 14: Top eventos por inscripciones
            "inscripciones_labels": inscripciones_labels,
            "inscripciones_data": inscripciones_data,
        }

    @staticmethod
    def get_institutional_stats(user, institution):
        """
        Calcula métricas específicas para una institución.
        """
        hoy = timezone.now().date()

        # Agregaciones para institución
        mis_grupos = Grupo.objects.filter(usuario_creador=user, activo=True)

        total_mis_participantes = (
            Participante.objects.filter(
                vinculaciones__institucion=institution, vinculaciones__status="activo"
            )
            .distinct()
            .count()
        )

        # Eventos y Clubes
        # IDs de clubes donde la institución es miembro activo
        clubes_miembro_ids = MembresiaClu.objects.filter(
            institucion=institution, estado="miembro_activo"
        ).values_list("club_id", flat=True)

        # Eventos disponibles: solo los accesibles para esta institución
        eventos_accesibles_q = (
            # Eventos institucionales públicos
            Q(tipo_evento="institucional", audiencia="publica")
            |
            # Eventos institucionales privados propios
            Q(
                tipo_evento="institucional",
                audiencia="institucional_privado",
                institucion=institution,
            )
            |
            # Eventos de club públicos
            Q(tipo_evento="club", audiencia="publica")
            |
            # Eventos de club exclusivos donde la institución es miembro
            Q(
                tipo_evento="club",
                audiencia="club_exclusivo",
                club_organizador_id__in=clubes_miembro_ids,
            )
        )

        eventos_agg = Evento.objects.filter(activo=True).aggregate(
            disponibles=Count(
                "id",
                filter=Q(fecha__gte=hoy, estado_evento="abierto")
                & eventos_accesibles_q,
                distinct=True,
            ),
            asignados=Count("id", filter=Q(grupos_inscritos__usuario_creador=user)),
        )

        mis_clubes_agg = Club.objects.filter(
            institucion_creadora=institution
        ).aggregate(
            total=Count("id"),
            aprobados=Count("id", filter=Q(status="aprobado", activo=True)),
        )

        # Eventos de club accesibles (reutiliza clubes_miembro_ids ya calculado)
        eventos_club_disponibles = (
            Evento.objects.filter(
                tipo_evento="club",
                estado_evento="abierto",
                activo=True,
            )
            .filter(
                Q(audiencia="publica")
                | Q(
                    audiencia="club_exclusivo",
                    club_organizador_id__in=clubes_miembro_ids,
                )
            )
            .distinct()
            .count()
        )

        # =============================================================================
        # PRÓXIMOS EVENTOS - Lógica robusta según requerimientos funcionales
        # =============================================================================
        # Estados que permiten ejecución futura (excluye finales y en curso)
        ESTADOS_PROXIMOS_EVENTOS = {
            EstadoEvento.ABIERTO,
            EstadoEvento.PAUSADO,
        }

        # Query optimizada: eventos futuros accesibles para la institución
        proximos_eventos = (
            Evento.objects.filter(
                activo=True,
                cancelado=False,
                fecha__gte=hoy,  # Fecha de inicio >= hoy
                estado_evento__in=ESTADOS_PROXIMOS_EVENTOS,
            )
            .filter(eventos_accesibles_q)  # Reutilizar lógica de accesibilidad
            .select_related("estado")  # Optimización ORM
            .order_by("fecha", "nombre")[  # Orden ascendente por fecha
                :5
            ]  # Limitar a 5 eventos próximos
        )

        # =============================================================================
        # EQUIPOS RECIENTES - Completar contexto del dashboard
        # =============================================================================
        grupos_recientes = (
            mis_grupos.select_related("institucion")
            .prefetch_related("participantes", "tutores")
            .order_by("-fecha_registro")[:5]
        )

        # Enriquecer grupos con nombre del tutor para el template
        for grupo in grupos_recientes:
            tutor = grupo.tutores.first()
            grupo.tutor_nombre = tutor.get_nombre_completo() if tutor else "Sin tutor"

        return {
            "total_mis_grupos": mis_grupos.count(),
            "total_mis_participantes": total_mis_participantes,
            "eventos_disponibles": eventos_agg["disponibles"],
            "eventos_asignados": eventos_agg["asignados"],
            "total_mis_clubes": mis_clubes_agg["total"],
            "mis_clubes_aprobados": mis_clubes_agg["aprobados"],
            "eventos_club_disponibles": eventos_club_disponibles,
            "proximos_eventos": proximos_eventos,
            "grupos_recientes": grupos_recientes,
        }
