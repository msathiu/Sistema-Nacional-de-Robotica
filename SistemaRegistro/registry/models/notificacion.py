from django.db import models
from django.contrib.auth.models import User
from .club import Club


class Notificacion(models.Model):
    """Modelo para sistema de notificaciones internas (buzón de mensajes)."""

    TIPO_CHOICES = [
        ("club_aprobado", "Club Aprobado"),
        ("club_rechazado", "Club Rechazado"),
        ("solicitud_eliminacion", "Solicitud de Eliminación"),
        ("eliminacion_aprobada", "Eliminación Aprobada"),
        ("eliminacion_rechazada", "Eliminación Rechazada"),
        ("membresia_aprobada", "Membresía Aprobada"),
        ("membresia_rechazada", "Membresía Rechazada"),
        ("salida_club", "Salida de Club"),
        ("sistema", "Notificación del Sistema"),
    ]

    destinatario = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notificaciones"
    )
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES, db_index=True)
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False, db_index=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, db_index=True)
    club = models.ForeignKey(Club, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ["-fecha_creacion"]
        indexes = [
            models.Index(fields=["destinatario", "leida"], name="idx_notif_dest_leida"),
        ]

    def __str__(self):
        return f"{self.titulo} - {self.destinatario.username}"

    def marcar_leida(self):
        """Marca la notificación como leída."""
        if not self.leida:
            self.leida = True
            self.save(update_fields=["leida"])
