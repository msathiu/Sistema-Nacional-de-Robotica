"""
Utilidades comunes para la aplicación registry.
"""

import logging
import re
from typing import Any, Dict

from django.db.models import QuerySet

logger = logging.getLogger(__name__)


def normalizar_cedula(cedula: str) -> str:
    """
    Normaliza una cédula venezolana al formato estándar sin prefijo.
    
    Convierte:
    - "V-19111111" -> "19111111"
    - "V19111111" -> "19111111"
    - "v-19111111" -> "19111111"
    - "19111111" -> "19111111"
    - "E-19111111" -> "19111111" (extranjeros también se normalizan)
    
    Args:
        cedula: Cédula en cualquier formato válido
        
    Returns:
        str: Cédula normalizada solo con números
    """
    if not cedula:
        return ""
    
    # Convertir a string y limpiar espacios
    cedula = str(cedula).strip().upper()
    
    # Remover prefijo V- o E- (con o sin guión)
    cedula_limpia = re.sub(r'^[VE]-?', '', cedula)
    
    # Remover cualquier carácter no numérico
    cedula_limpia = re.sub(r'[^0-9]', '', cedula_limpia)
    
    return cedula_limpia


def buscar_participante_por_cedula(cedula: str):
    """
    Busca un participante por cédula, normalizando antes de la búsqueda.
    Intenta encontrar el participante con diferentes formatos de cédula.
    
    Args:
        cedula: Cédula en cualquier formato
        
    Returns:
        Participante o None si no se encuentra
    """
    from .models import Participante
    
    if not cedula:
        return None
    
    cedula_normalizada = normalizar_cedula(cedula)
    
    if not cedula_normalizada:
        return None
    
    # Intentar buscar con diferentes formatos
    formatos_a_buscar = [
        cedula_normalizada,                    # 19111111
        f"V-{cedula_normalizada}",             # V-19111111
        f"V{cedula_normalizada}",              # V19111111
        f"E-{cedula_normalizada}",             # E-19111111
        f"E{cedula_normalizada}",              # E19111111
    ]
    
    for formato in formatos_a_buscar:
        try:
            return Participante.objects.get(cedula=formato)
        except Participante.DoesNotExist:
            continue
    
    return None


def validar_cedula_venezolana(cedula: str) -> bool:
    """
    Valida el formato de una cédula venezolana.

    Args:
        cedula: Cédula a validar (formato: V12345678 o E12345678)

    Returns:
        bool: True si la cédula es válida, False en caso contrario.
    """
    if not cedula:
        return False

    # Remover espacios y convertir a mayúsculas
    cedula = cedula.strip().upper()

    # Verificar formato básico
    if len(cedula) < 2:
        return False

    # Verificar prefijo (V o E)
    if cedula[0] not in ["V", "E"]:
        return False

    # Verificar que el resto sean dígitos
    numero = cedula[1:]
    if not numero.isdigit():
        return False

    # Verificar longitud (entre 6 y 9 dígitos)
    if len(numero) < 6 or len(numero) > 9:
        return False

    return True


def validar_rif_venezolano(rif: str) -> bool:
    """
    Valida el formato de un RIF venezolano.

    Args:
        rif: RIF a validar (formato: J-12345678-9)

    Returns:
        bool: True si el RIF es válido, False en caso contrario.
    """
    if not rif:
        return False

    # Remover espacios
    rif = rif.strip().upper()

    # Verificar formato con guiones
    partes = rif.split("-")
    if len(partes) != 3:
        return False

    prefijo, numero, digito = partes

    # Verificar prefijo (J, G, V, E)
    if prefijo not in ["J", "G", "V", "E"]:
        return False

    # Verificar que el número tenga 8 dígitos
    if not numero.isdigit() or len(numero) != 8:
        return False

    # Verificar que el dígito verificador sea un dígito
    if not digito.isdigit() or len(digito) != 1:
        return False

    return True


def formatear_telefono_venezolano(codigo_area: str, numero: str) -> str:
    """
    Formatea un número de teléfono venezolano.

    Args:
        codigo_area: Código de área (ej: 0424)
        numero: Número de teléfono (7 dígitos)

    Returns:
        str: Teléfono formateado (ej: 0424-1234567)
    """
    if not codigo_area or not numero:
        return ""

    return f"{codigo_area}-{numero}"


def obtener_estadisticas_institucion(institucion) -> Dict[str, Any]:
    """
    Obtiene estadísticas de una institución.

    Args:
        institucion: Instancia del modelo Institucion

    Returns:
        dict: Diccionario con estadísticas de la institución
    """
    from .models import Evento, Grupo, Participante

    try:
        participantes = Participante.objects.filter(
            institucion=institucion, activo=True
        )

        grupos = Grupo.objects.filter(
            usuario_creador__userprofile__institution=institucion, activo=True
        )

        eventos = Evento.objects.filter(institucion=institucion, activo=True)

        return {
            "total_participantes": participantes.count(),
            "total_grupos": grupos.count(),
            "total_eventos": eventos.count(),
            "participantes_activos": participantes.filter(activo=True).count(),
        }
    except Exception as e:
        logger.error(
            f"Error al obtener estadísticas de institución {institucion.id}: {e}"
        )
        return {
            "total_participantes": 0,
            "total_grupos": 0,
            "total_eventos": 0,
            "participantes_activos": 0,
        }


def validar_edad_minima(fecha_nacimiento, edad_minima: int = 4) -> bool:
    """
    Valida que una persona tenga la edad mínima requerida.

    Args:
        fecha_nacimiento: Fecha de nacimiento
        edad_minima: Edad mínima requerida (por defecto 4 años)

    Returns:
        bool: True si cumple con la edad mínima, False en caso contrario.
    """
    from datetime import date

    if not fecha_nacimiento:
        return False

    today = date.today()
    edad = (
        today.year
        - fecha_nacimiento.year
        - ((today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
    )

    return edad >= edad_minima


def limpiar_queryset_inactivos(queryset: QuerySet) -> QuerySet:
    """
    Filtra un queryset para excluir registros inactivos.

    Args:
        queryset: QuerySet a filtrar

    Returns:
        QuerySet: QuerySet filtrado sin registros inactivos
    """
    if hasattr(queryset.model, "activo"):
        return queryset.filter(activo=True)
    return queryset


def generar_codigo_seguro(longitud: int = 8, prefijo: str = "") -> str:
    """
    Genera un código alfanumérico seguro.

    Args:
        longitud: Longitud del código a generar
        prefijo: Prefijo opcional para el código

    Returns:
        str: Código generado
    """
    import string

    from django.utils.crypto import get_random_string

    chars = string.ascii_uppercase + string.digits
    codigo = get_random_string(length=longitud, allowed_chars=chars)

    if prefijo:
        return f"{prefijo}{codigo}"

    return codigo
