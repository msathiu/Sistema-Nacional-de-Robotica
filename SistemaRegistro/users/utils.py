from typing import Optional, Tuple

import nh3
from registry.models import Estado, Municipio, Parroquia


class LocationUtils:
    """
    Utilidades para la resolución de objetos geográficos (Estado, Municipio, Parroquia).
    """

    @staticmethod
    def resolve_location(
        estado_id=None, municipio_id=None, parroquia_id=None
    ) -> Tuple[Optional[Estado], Optional[Municipio], Optional[Parroquia]]:
        """
        Resuelve los objetos de ubicación a partir de sus IDs u objetos de forma segura.
        """
        estado = None
        municipio = None
        parroquia = None

        # Resolución de Estado
        if isinstance(estado_id, Estado):
            estado = estado_id
        elif estado_id:
            try:
                estado = Estado.objects.get(id=estado_id)
            except (Estado.DoesNotExist, ValueError, TypeError):
                pass

        # Resolución de Municipio
        if isinstance(municipio_id, Municipio):
            municipio = municipio_id
        elif municipio_id:
            try:
                municipio = Municipio.objects.get(id=municipio_id)
            except (Municipio.DoesNotExist, ValueError, TypeError):
                pass

        # Resolución de Parroquia
        if isinstance(parroquia_id, Parroquia):
            parroquia = parroquia_id
        elif parroquia_id:
            try:
                parroquia = Parroquia.objects.get(id=parroquia_id)
            except (Parroquia.DoesNotExist, ValueError, TypeError):
                pass

        return estado, municipio, parroquia


class StringUtils:
    """
    Utilidades para limpieza y formateo de cadenas (cédulas, nombres, etc).
    """

    @staticmethod
    def clean_numeric_id(value: Optional[str]) -> str:
        """
        Limpia una cadena dejando solo los dígitos (útil para cédulas).
        """
        if not value:
            return ""
        return "".join(filter(str.isdigit, str(value)))

    @staticmethod
    def clean_html(value: Optional[str]) -> str:
        """
        Sanitiza contenido de texto libre usando nh3.
        Elimina etiquetas inseguras y mantiene texto limpio.
        """
        if not value:
            return ""
        cleaned = nh3.clean(
            str(value),
            tags=set(),
            attributes={},
            clean_content_tags=None,
            strip_comments=True,
            link_rel="noopener noreferrer",
        )
        return cleaned.strip()

    @staticmethod
    def flash_plain(text: Optional[str]) -> str:
        """
        Texto para django.contrib.messages (success/error/warning/info).

        Elimina cualquier HTML para que en plantillas baste con {{ message }} sin |safe,
        manteniendo el escape automático de Django como última capa.
        """
        return StringUtils.clean_html(text)

    @staticmethod
    def format_username_from_id(nacionalidad: str, numeric_id: str) -> str:
        """
        Genera un username estándar a partir de la nacionalidad y la cédula limpia.
        """
        if nacionalidad == "E":  # Escolar
            return f"E-{numeric_id}"
        return f"{nacionalidad}-{numeric_id}"
