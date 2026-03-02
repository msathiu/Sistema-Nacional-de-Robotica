# Policies package for registry application
from .admission_policies import (
    es_fundadora_del_club,
    es_ente_rector,
    puede_ver_membresia,
    puede_gestionar_fundadora,
    puede_gestionar_rector,
)

__all__ = [
    'es_fundadora_del_club',
    'es_ente_rector',
    'puede_ver_membresia',
    'puede_gestionar_fundadora',
    'puede_gestionar_rector',
]
