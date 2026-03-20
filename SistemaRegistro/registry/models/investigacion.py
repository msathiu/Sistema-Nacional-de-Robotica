from django.db import models

class LineaInvestigacion(models.Model):
    """Catálogo dinámico de líneas de investigación gestionado por el Ente Rector."""

    codigo = models.CharField(
        max_length=50, unique=True, db_index=True, verbose_name="Código"
    )
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    activa = models.BooleanField(default=True, db_index=True, verbose_name="Activa")
    orden = models.IntegerField(default=0, verbose_name="Orden de visualización")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Línea de Investigación"
        verbose_name_plural = "Líneas de Investigación"
        ordering = ["orden", "nombre"]
        indexes = [
            models.Index(fields=["activa", "orden"], name="idx_linea_activa_orden"),
        ]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
