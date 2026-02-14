# users/validators.py

import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


# Validador para requerir al menos una Mayúscula
class UppercaseValidator:
    def validate(self, password, user=None):
        if not re.findall("[A-Z]", password):
            raise ValidationError(
                _("La contraseña debe contener al menos una letra mayúscula."),
                code="password_no_uppercase",
            )

    def get_help_text(self):
        return _("Tu contraseña debe contener al menos una letra mayúscula.")


# Validador para requerir al menos una Minúscula
class LowercaseValidator:
    def validate(self, password, user=None):
        if not re.findall("[a-z]", password):
            raise ValidationError(
                _("La contraseña debe contener al menos una letra minúscula."),
                code="password_no_lowercase",
            )

    def get_help_text(self):
        return _("Tu contraseña debe contener al menos una letra minúscula.")


# Validador para requerir al menos un Símbolo/Caracter Especial
class SymbolValidator:
    def validate(self, password, user=None):
        # El patrón incluye guiones, puntos y otros caracteres comunes de símbolos
        if not re.findall(r'[()\[\]{}|\\`~!@#$%^&*_\-+=;:"\'<>,./?]', password):
            raise ValidationError(
                _(
                    "La contraseña debe contener al menos un caracter especial o un guión."
                ),
                code="password_no_symbol",
            )

    def get_help_text(self):
        return _(
            "Tu contraseña debe contener al menos un caracter especial o un guión (ej: !@#$-)."
        )


# Nota: El validador numérico ya existe en Django (django.contrib.auth.password_validation.NumericPasswordValidator)
