"""
Configuración de campos del formulario de registro de institución.
Centraliza la lógica de qué campos mostrar/ocultar según el tipo de institución.
"""

INSTITUCION_FORM_CONFIG = {
    "particular": {
        "hidden_fields": [
            "campoRazonSocial",
            "camposRIF",
        ],
        "visible_fields": [
            "camposParticular",
        ],
        "required_fields": [
            "particularNombres",
            "particularApellidos",
            "particularNacionalidad",
            "particularCedula",
        ],
        "optional_fields": [
            "razonSocial",
            "rifLetra",
            "rifNumero",
            "codigoMPPE",
        ],
        "default_values": {
            "particularNacionalidad": "V",
        },
    },
    "educativa": {
        "hidden_fields": [
            "camposParticular",
        ],
        "visible_fields": [
            "campoRazonSocial",
            "camposRIF",
            "categoriasContainer",
        ],
        "required_fields": [
            "razonSocial",
            "rifNumero",
            "naturaleza",
            "subcategoria",
        ],
        "optional_fields": [
            "codigoMPPE",
        ],
        "default_values": {},
    },
    "publica": {
        "hidden_fields": [
            "camposParticular",
            "categoriasContainer",
            "dependenciaContainer",
        ],
        "visible_fields": [
            "campoRazonSocial",
            "camposRIF",
        ],
        "required_fields": [
            "razonSocial",
            "rifNumero",
        ],
        "optional_fields": [
            "codigoMPPE",
        ],
        "default_values": {},
    },
    "privada": {
        "hidden_fields": [
            "camposParticular",
            "categoriasContainer",
            "dependenciaContainer",
        ],
        "visible_fields": [
            "campoRazonSocial",
            "camposRIF",
        ],
        "required_fields": [
            "razonSocial",
            "rifNumero",
        ],
        "optional_fields": [
            "codigoMPPE",
        ],
        "default_values": {},
    },
    "otra": {
        "hidden_fields": [
            "camposParticular",
        ],
        "visible_fields": [
            "campoRazonSocial",
            "camposRIF",
            "categoriasContainer",
        ],
        "required_fields": [
            "razonSocial",
            "rifNumero",
            "naturaleza",
        ],
        "optional_fields": [
            "codigoMPPE",
            "subcategoria",
        ],
        "default_values": {},
    },
}


def get_form_config(tipo_institucion):
    """
    Obtiene la configuración de campos para un tipo de institución.

    Args:
        tipo_institucion: str - Tipo de institución (particular, educativa, publica, privada, otra)

    Returns:
        dict - Configuración de campos o configuración vacía si no existe
    """
    return INSTITUCION_FORM_CONFIG.get(
        tipo_institucion,
        {
            "hidden_fields": [],
            "visible_fields": [],
            "required_fields": [],
            "optional_fields": [],
            "default_values": {},
        },
    )
