"""
Configuración de campos del formulario de registro de institución.
Centraliza la lógica de qué campos mostrar/ocultar según el tipo de institución.
"""

# Subcategorías por tipo
SUBCATEGORIAS_EDUCATIVA = [
    {"value": "preescolar", "text": "Preescolar"},
    {"value": "primaria", "text": "Primaria (1ra y 2da etapa)"},
    {"value": "secundaria", "text": "Secundaria (3ra etapa)"},
    {"value": "media_general", "text": "Media General"},
    {"value": "media_tecnica", "text": "Media Técnica"},
]

SUBCATEGORIAS_OTRA_PRIVADA = [
    {"value": "empresa", "text": "Empresa"},
    {"value": "fundacion", "text": "Fundación"},
]

# Configuración principal por tipo de institución
INSTITUCION_FORM_CONFIG = {
    "particular": {
        "hidden_fields": [
            "campoRazonSocial",
            "camposRIF",
            "categoriasContainer",
            "dependenciaContainer",
            "campoCodigoMPPE",
            "campoCodigoInfocentro",
        ],
        "visible_fields": ["camposParticular"],
        "required_fields": [
            "particularNombres",
            "particularApellidos",
            "particularNacionalidad",
            "particularCedula",
        ],
        "optional_fields": ["razonSocial", "rifLetra", "rifNumero", "codigoMPPE"],
        "default_values": {"particularNacionalidad": "V", "rifLetra": "V"},
        "readonly_fields": {"rifLetra": False, "rifNumero": False},
        "mostrar_categorias": False,
        "mostrar_dependencia": False,
        "mostrar_codigo_mppe": False,
        "mostrar_codigo_infocentro": False,
        "rif_config": {"letra": "V", "fijo": False, "numero_fijo": ""},
    },
    "educativa": {
        "hidden_fields": ["camposParticular", "campoCodigoInfocentro"],
        "visible_fields": [
            "campoRazonSocial",
            "camposRIF",
            "categoriasContainer",
            "campoCodigoMPPE",
        ],
        "required_fields": [
            "razonSocial",
            "naturaleza",
            "subcategoria",
            "codigoMPPE",
        ],
        "optional_fields": [],
        "default_values": {},
        "readonly_fields": {"rifLetra": True, "rifNumero": True},
        "mostrar_categorias": True,
        "mostrar_dependencia": False,
        "mostrar_codigo_mppe": True,
        "mostrar_codigo_infocentro": False,
        "rif_config": {"letra": "G", "fijo": True, "numero_fijo": "20000009-0"},
        "subcategorias": SUBCATEGORIAS_EDUCATIVA,
        "requiere_naturaleza": True,
    },
    "publica": {
        "hidden_fields": [
            "camposParticular",
            "categoriasContainer",
            "dependenciaContainer",
            "campoCodigoMPPE",
            "campoCodigoInfocentro",
        ],
        "visible_fields": ["campoRazonSocial", "camposRIF"],
        "required_fields": ["razonSocial", "rifLetra", "rifNumero"],
        "optional_fields": ["codigoMPPE"],
        "default_values": {},
        "readonly_fields": {"rifLetra": False, "rifNumero": False},
        "mostrar_categorias": False,
        "mostrar_dependencia": False,
        "mostrar_codigo_mppe": False,
        "mostrar_codigo_infocentro": False,
        "rif_config": {"letra": "G", "fijo": False, "numero_fijo": ""},
    },
    "privada": {
        "hidden_fields": [
            "camposParticular",
            "categoriasContainer",
            "dependenciaContainer",
            "campoCodigoMPPE",
            "campoCodigoInfocentro",
        ],
        "visible_fields": ["campoRazonSocial", "camposRIF"],
        "required_fields": ["razonSocial", "rifLetra", "rifNumero"],
        "optional_fields": ["codigoMPPE"],
        "default_values": {},
        "readonly_fields": {"rifLetra": False, "rifNumero": False},
        "mostrar_categorias": False,
        "mostrar_dependencia": False,
        "mostrar_codigo_mppe": False,
        "mostrar_codigo_infocentro": False,
        "rif_config": {"letra": "J", "fijo": False, "numero_fijo": ""},
    },
    "otra": {
        "hidden_fields": [
            "camposParticular",
            "campoCodigoMPPE",
            "campoCodigoInfocentro",
        ],
        "visible_fields": ["campoRazonSocial", "camposRIF", "categoriasContainer"],
        "required_fields": ["razonSocial", "rifLetra", "rifNumero", "naturaleza"],
        "optional_fields": ["codigoMPPE", "subcategoria"],
        "default_values": {},
        "readonly_fields": {"rifLetra": False, "rifNumero": False},
        "mostrar_categorias": True,
        "mostrar_dependencia": True,
        "mostrar_codigo_mppe": False,
        "mostrar_codigo_infocentro": False,
        "rif_config": {"letra": "", "fijo": False, "numero_fijo": ""},
        "subcategorias": SUBCATEGORIAS_OTRA_PRIVADA,
        "requiere_naturaleza": True,
        "rif_por_naturaleza": {"publica": "G", "privada": "J"},
    },
    "infocentro": {
        "hidden_fields": [
            "camposParticular",
            "categoriasContainer",
            "dependenciaContainer",
            "campoCodigoMPPE",
        ],
        "visible_fields": ["campoRazonSocial", "camposRIF", "campoCodigoInfocentro"],
        "required_fields": ["razonSocial", "codigoInfocentro"],
        "optional_fields": [],
        "default_values": {},
        "readonly_fields": {"rifLetra": True, "rifNumero": True},
        "mostrar_categorias": False,
        "mostrar_dependencia": False,
        "mostrar_codigo_mppe": False,
        "mostrar_codigo_infocentro": True,
        "rif_config": {"letra": "G", "fijo": True, "numero_fijo": "20007728-0"},
    },
}


def get_form_config(tipo_institucion):
    """
    Obtiene la configuración completa de campos para un tipo de institución.

    Args:
        tipo_institucion: str - Tipo de institución (particular, educativa, publica, privada, otra, infocentro)

    Returns:
        dict - Configuración completa de campos o configuración por defecto si no existe
    """
    config_default = {
        "hidden_fields": [],
        "visible_fields": [],
        "required_fields": [],
        "optional_fields": [],
        "default_values": {},
        "readonly_fields": {"rifLetra": False, "rifNumero": False},
        "mostrar_categorias": False,
        "mostrar_dependencia": False,
        "mostrar_codigo_mppe": False,
        "mostrar_codigo_infocentro": False,
        "rif_config": {"letra": "", "fijo": False, "numero_fijo": ""},
        "subcategorias": [],
        "requiere_naturaleza": False,
    }

    config = INSTITUCION_FORM_CONFIG.get(tipo_institucion, config_default)

    # Asegurar que todas las claves existan
    for key in config_default:
        if key not in config:
            config[key] = config_default[key]

    return config


def get_all_configs():
    """
    Devuelve todas las configuraciones de instituciones.
    Útil para debugging o inicialización.

    Returns:
        dict - Todas las configuraciones
    """
    return INSTITUCION_FORM_CONFIG
