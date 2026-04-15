"""
MapaService: lógica de consultas para el mapa territorial del dashboard fed_central.

Principios aplicados:
- Una sola fuente de verdad para filtros base por capa
- Queries con select_related implícito via values() — sin N+1
- Cache key sanitizada con unicodedata para cubrir todos los diacríticos
- Helper _qs_a_dict centralizado para evitar repetición
- api_mapa_resumen reutiliza los mismos métodos en lugar de duplicar lógica
"""
import unicodedata
from django.db.models import Count, F, Q
from django.db.models.functions import Coalesce

from registry.models import (
    Club, Evento, Institucion, Participante, TutorInstitucion
)


def _slug(texto: str) -> str:
    """Normaliza texto para uso seguro en cache keys."""
    normalizado = unicodedata.normalize("NFD", texto)
    sin_tildes = "".join(c for c in normalizado if unicodedata.category(c) != "Mn")
    return sin_tildes.lower().replace(" ", "_")


def _qs_a_dict(qs, campo: str) -> dict:
    return {r[campo]: r["total"] for r in qs if r[campo]}


# ── Filtros base por capa ────────────────────────────────────────────────────

def _filtro_instituciones(solo_activas: bool) -> Q:
    """
    solo_activas=True  → aprobadas y operativas (estatus=aprobado, activa=True, eliminado=False)
    solo_activas=False → registradas vigentes (aprobadas + pendientes, excluye rechazadas y eliminadas)
    """
    if solo_activas:
        return Q(eliminado=False, activa=True, estatus="aprobado")
    return Q(eliminado=False, estatus__in=["aprobado", "pendiente"])


def _qs_instituciones(solo_activas: bool, **extra_filtros):
    return Institucion.objects.filter(_filtro_instituciones(solo_activas), **extra_filtros)


def _qs_clubes(**extra_filtros):
    return Club.objects.filter(activo=True, status="aprobado", **extra_filtros)


def _qs_eventos(**extra_filtros):
    return Evento.objects.filter(activo=True, **extra_filtros)


def _qs_tutores():
    return (
        TutorInstitucion.objects
        .annotate(estado_nombre=Coalesce(F("estado__nombre"), F("institucion__estado__nombre")))
        .exclude(estado_nombre__isnull=True)
    )


def _qs_participantes(**extra_filtros):
    return Participante.objects.filter(**extra_filtros)


# ── Nivel 1: datos por estado (colorea el mapa) ──────────────────────────────

def datos_por_estado(capa: str, solo_activas: bool) -> dict:
    if capa == "instituciones":
        qs = _qs_instituciones(solo_activas).values("estado__nombre").annotate(total=Count("id"))
        return _qs_a_dict(qs, "estado__nombre")

    if capa == "clubes":
        qs = _qs_clubes().values("institucion_creadora__estado__nombre").annotate(total=Count("id"))
        return _qs_a_dict(qs, "institucion_creadora__estado__nombre")

    if capa == "eventos":
        qs = _qs_eventos().values("estado__nombre").annotate(total=Count("id"))
        return _qs_a_dict(qs, "estado__nombre")

    if capa == "tutores":
        qs = (_qs_tutores().values("estado_nombre").annotate(total=Count("tutor_id", distinct=True)))
        return {r["estado_nombre"]: r["total"] for r in qs}

    if capa == "participantes":
        qs = _qs_participantes().values("estado__nombre").annotate(total=Count("id"))
        return _qs_a_dict(qs, "estado__nombre")

    return {}


# ── Nivel 2: municipios de un estado ─────────────────────────────────────────

def municipios_por_estado(capa: str, estado: str, solo_activas: bool, limit: int = 15) -> list:
    if capa == "instituciones":
        qs = (_qs_instituciones(solo_activas, estado__nombre=estado)
              .values("municipio__nombre").annotate(total=Count("id")).order_by("-total")[:limit])
        return [{"nombre": r["municipio__nombre"], "total": r["total"]} for r in qs if r["municipio__nombre"]]

    if capa == "participantes":
        qs = (_qs_participantes(estado__nombre=estado)
              .values("municipio__nombre").annotate(total=Count("id")).order_by("-total")[:limit])
        return [{"nombre": r["municipio__nombre"], "total": r["total"]} for r in qs if r["municipio__nombre"]]

    if capa == "eventos":
        qs = (_qs_eventos(estado__nombre=estado)
              .values("municipio__nombre").annotate(total=Count("id")).order_by("-total")[:limit])
        return [{"nombre": r["municipio__nombre"], "total": r["total"]} for r in qs if r["municipio__nombre"]]

    return []


# ── Nivel 3: parroquias de un municipio ──────────────────────────────────────

def parroquias_por_municipio(capa: str, estado: str, municipio: str, solo_activas: bool) -> list:
    if capa == "instituciones":
        qs = (_qs_instituciones(solo_activas, estado__nombre=estado, municipio__nombre=municipio)
              .values("parroquia__nombre").annotate(total=Count("id")).order_by("-total"))
        return [{"nombre": r["parroquia__nombre"], "total": r["total"]} for r in qs if r["parroquia__nombre"]]

    if capa == "participantes":
        qs = (_qs_participantes(estado__nombre=estado, municipio__nombre=municipio)
              .values("parroquia__nombre").annotate(total=Count("id")).order_by("-total"))
        return [{"nombre": r["parroquia__nombre"], "total": r["total"]} for r in qs if r["parroquia__nombre"]]

    if capa == "eventos":
        qs = (_qs_eventos(estado__nombre=estado, municipio__nombre=municipio)
              .values("parroquia__nombre").annotate(total=Count("id")).order_by("-total"))
        return [{"nombre": r["parroquia__nombre"], "total": r["total"]} for r in qs if r["parroquia__nombre"]]

    return []


# ── Resumen completo (tooltip del mapa: todas las capas por estado) ───────────

def resumen_todas_capas(solo_activas: bool = True) -> dict:
    """
    Ejecuta 5 queries y las combina en un dict indexado por estado.
    Usado por el tooltip del mapa para mostrar todos los indicadores al hover.
    """
    inst          = datos_por_estado("instituciones", solo_activas)
    clubes        = datos_por_estado("clubes",        solo_activas)
    eventos       = datos_por_estado("eventos",       solo_activas)
    tutores       = datos_por_estado("tutores",       solo_activas)
    participantes = datos_por_estado("participantes", solo_activas)

    todos = set(inst) | set(clubes) | set(eventos) | set(tutores) | set(participantes)
    return {
        estado: {
            "instituciones":  inst.get(estado, 0),
            "clubes":         clubes.get(estado, 0),
            "eventos":        eventos.get(estado, 0),
            "tutores":        tutores.get(estado, 0),
            "participantes":  participantes.get(estado, 0),
        }
        for estado in todos
    }
