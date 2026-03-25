from django import template
from users.selectors import EventoActionSelector

register = template.Library()


@register.simple_tag
def get_acciones(evento, perfil, vista="mis_eventos"):
    """
    Retorna un diccionario con las acciones disponibles para un evento.
    
    Uso:
        {% get_acciones evento perfil 'mis_eventos' as acciones %}
        {% if acciones.editar %}...{% endif %}
    """
    return EventoActionSelector.get_acciones_evento(evento, perfil, vista)


@register.simple_tag
def puede_inscribir(evento, perfil):
    """
    Retorna True si el usuario puede inscribir grupos en el evento.
    
    Uso:
        {% if puede_inscribir evento perfil %}...{% endif %}
    """
    return EventoActionSelector.puede_inscribir(evento, perfil)