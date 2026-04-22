import logging
import re
from typing import Optional

from django.core.validators import RegexValidator
from django.db import models

logger = logging.getLogger(__name__)

# === UTILS ===


def normalizar_texto_titulo(texto: Optional[str]) -> Optional[str]:
    """
    Normaliza texto para títulos en español de manera profesional y robusta.
    """
    if not texto or not isinstance(texto, str):
        return texto

    texto = texto.strip()
    if not texto:
        return texto

    PARTICULAS_MINUSCULAS = {
        "el",
        "la",
        "los",
        "las",
        "un",
        "una",
        "unos",
        "unas",
        "a",
        "ante",
        "bajo",
        "cabe",
        "con",
        "contra",
        "de",
        "desde",
        "durante",
        "en",
        "entre",
        "hacia",
        "hasta",
        "mediante",
        "para",
        "por",
        "según",
        "sin",
        "so",
        "sobre",
        "tras",
        "versus",
        "vía",
        "al",
        "del",
        "y",
        "e",
        "ni",
        "que",
        "o",
        "u",
        "pero",
        "mas",
        "sino",
        "aunque",
        "me",
        "te",
        "se",
        "nos",
        "os",
        "lo",
        "la",
        "le",
        "los",
        "las",
        "les",
        "mi",
    }

    SIGLAS = {
        "MPPE",
        "RNR",
        "CII",
        "ONU",
        "UNESCO",
        "IVSS",
        "SENIAT",
        "RIF",
        "CI",
        "ONG",
        "IVA",
        "ISLR",
        "CNE",
        "TSJ",
        "FAO",
        "OEA",
        "FMI",
        "BM",
        "BCV",
    }

    NOMBRES_PROPIOS = {
        "Venezuela",
        "Bolívar",
        "Chávez",
        "Miranda",
        "Caracas",
        "Federación",
        "Andrés",
        "José",
        "María",
        "Simón",
        "Antonio",
        "Juan",
        "Carlos",
    }

    EXCEPCIONES_INICIO_FIN = {"a", "y", "o", "e", "u", "con", "sin"}
    RE_APOSTROFE = re.compile(r"^([dD]'|[lL]'|[oO]'|[mM]c)(\w+)")

    def capitalizar_palabra(palabra: str, posicion: int, total: int) -> str:
        # Preservar palabras ya escritas en mayúscula (siglas de 1 o más chars: "A", "C", "ONG")
        if palabra.isupper():
            return palabra

        palabra_lower = palabra.lower()
        if palabra_lower.upper() in SIGLAS:
            return palabra_lower.upper()

        match = RE_APOSTROFE.match(palabra)
        if match:
            prefijo, resto = match.groups()
            return f"{prefijo.capitalize()}{resto.capitalize()}"

        es_primera = posicion == 0
        es_ultima = posicion == total - 1
        es_nombre_propio = palabra_lower in {p.lower() for p in NOMBRES_PROPIOS}

        # La primera y última palabra de un nombre institucional SIEMPRE van en mayúscula,
        # sin importar si son partículas o artículos (ej. "A C Colegio", "Colegio Y Más")
        if es_primera or es_ultima:
            return palabra_lower.capitalize()

        if es_nombre_propio:
            return next(p for p in NOMBRES_PROPIOS if p.lower() == palabra_lower)

        if palabra_lower in PARTICULAS_MINUSCULAS:
            return palabra_lower

        return palabra_lower.capitalize()

    palabras = texto.split()
    total = len(palabras)

    # Si la mayoría de palabras significativas (>1 char) están en mayúsculas,
    # normalizar a minúsculas primero antes de aplicar la capitalización por regla.
    palabras_significativas = [p for p in palabras if len(p) > 1]
    if (
        palabras_significativas
        and sum(1 for p in palabras_significativas if p.isupper())
        > len(palabras_significativas) / 2
    ):
        palabras = [p.lower() for p in palabras]

    resultado = [
        capitalizar_palabra(palabra, i, total) for i, palabra in enumerate(palabras)
    ]

    texto_normalizado = " ".join(resultado)
    texto_normalizado = re.sub(r"\s+([,;.:!?])", r"\1", texto_normalizado)
    return texto_normalizado


# === CONSTANTS ===

NACIONALIDAD_CHOICES = [
    ("V", "Venezolano"),
    ("E", "Extranjero"),
]

SEXO_CHOICES = [
    ("M", "Masculino"),
    ("F", "Femenino"),
    ("O", "Otro"),
]

CODIGO_AREA_CHOICES = [
    ("0424", "0424"),
    ("0414", "0414"),
    ("0422", "0422"),
    ("0412", "0412"),
    ("0426", "0426"),
    ("0416", "0416"),
    ("0212", "0212"),
]

GRADO_CHOICES = [
    ("NO", "No estudia"),
    ("P1", "Preescolar Nivel 1"),
    ("P2", "Preescolar Nivel 2"),
    ("PR1", "1er Grado Primaria"),
    ("PR2", "2do Grado Primaria"),
    ("PR3", "3er Grado Primaria"),
    ("PR4", "4to Grado Primaria"),
    ("PR5", "5to Grado Primaria"),
    ("PR6", "6to Grado Primaria"),
    ("L1", "1er Año Liceo"),
    ("L2", "2do Año Liceo"),
    ("L3", "3er Año Liceo"),
    ("L4", "4to Año Liceo"),
    ("L5", "5to Año Liceo"),
    ("L6", "6to Año Liceo"),
    ("U", "Estudios Universitarios"),
    ("OTRO", "Otro/No especificado"),
]

NUMERO_VALIDATOR = RegexValidator(
    regex="^[0-9]{7}$", message="El número debe ser de 7 dígitos numéricos."
)


# === BASE MODELS ===
class BaseModel(models.Model):
    """Modelo abstracto con campos comunes"""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True, db_index=True)

    class Meta:
        abstract = True


class Estado(models.Model):
    nombre = models.CharField(max_length=100, unique=True, db_index=True)
    codigo = models.CharField(max_length=10, unique=True, db_index=True)

    class Meta:
        verbose_name = "Estado"
        verbose_name_plural = "Estados"
        ordering = ["nombre"]
        indexes = [
            models.Index(fields=["nombre"], name="idx_estado_nombre"),
            models.Index(fields=["codigo"], name="idx_estado_codigo"),
        ]

    def __str__(self):
        return self.nombre


class Municipio(models.Model):
    estado = models.ForeignKey(
        Estado,
        on_delete=models.PROTECT,
        related_name="municipios",
    )
    nombre = models.CharField(max_length=100, db_index=True)

    class Meta:
        verbose_name = "Municipio"
        verbose_name_plural = "Municipios"
        constraints = [
            models.UniqueConstraint(
                fields=["estado", "nombre"],
                name="unique_municipio_estado_nombre",
            )
        ]
        ordering = ["estado", "nombre"]
        indexes = [
            models.Index(fields=["estado", "nombre"], name="idx_mun_estado_nombre"),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.estado.nombre})"


class Parroquia(models.Model):
    municipio = models.ForeignKey(
        Municipio, on_delete=models.PROTECT, related_name="parroquias"
    )
    nombre = models.CharField(max_length=100, db_index=True)

    class Meta:
        verbose_name = "Parroquia"
        verbose_name_plural = "Parroquias"
        constraints = [
            models.UniqueConstraint(
                fields=["municipio", "nombre"],
                name="unique_parroquia_municipio_nombre",
            )
        ]
        ordering = ["nombre"]
        indexes = [
            models.Index(fields=["municipio", "nombre"], name="idx_parr_mun_nombre"),
        ]

    def __str__(self):
        return f"{self.nombre} (Mun. {self.municipio.nombre})"


class Dependencia(models.Model):
    nombre = models.CharField(max_length=255, unique=True, db_index=True)
    activa = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Dependencia"
        verbose_name_plural = "Dependencias"
        ordering = ["nombre"]
        indexes = [
            models.Index(fields=["activa", "nombre"], name="idx_dep_activa_nombre"),
        ]

    def __str__(self):
        return self.nombre
