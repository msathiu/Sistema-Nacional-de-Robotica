#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SistemaRegistro.settings")
django.setup()

from django.contrib.auth.models import User
from users.models import UserProfile
from registry.models.evento import Evento, EstadoEvento
from registry.models.institucion import Institucion
from registry.models.base import Estado
from django.utils import timezone
from datetime import date


def crear_evento_pausado():
    print("🔍 Creando evento pausado para verificar estadísticas...")

    # Buscar usuario federación central existente
    try:
        user_fed = User.objects.get(username="fed_central")
        print(f"✅ Usuario encontrado: {user_fed.username}")
    except User.DoesNotExist:
        print("❌ Usuario fed_central no encontrado")
        return

    # Crear estado si no existe
    estado, created = Estado.objects.get_or_create(
        nombre="Estado Test", codigo="ET", defaults={}
    )
    if created:
        print(f"✅ Estado creado: {estado.nombre}")

    # Crear institución si no existe
    institucion, created = Institucion.objects.get_or_create(
        nombre="Institución Test", codigo="INST001", defaults={"estado": estado}
    )
    if created:
        print(f"✅ Institución creada: {institucion.nombre}")

    # Crear evento pausado
    evento_pausado = Evento.objects.create(
        nombre="Evento Pausado Verificación",
        tipo="Taller",
        fecha=date.today() + timezone.timedelta(days=25),
        estado_evento=EstadoEvento.PAUSADO,
        institucion=institucion,
        estado=estado,
    )

    print(f"✅ Evento pausado creado: {evento_pausado.nombre} (ID: {evento_pausado.id})")
    print(f"   - Estado: {evento_pausado.estado_evento}")
    print(f"   - Activo: {evento_pausado.activo}")
    print(f"   - Cancelado: {evento_pausado.cancelado}")

    # Verificar conteo total
    total_pausados = Evento.objects.filter(estado_evento=EstadoEvento.PAUSADO).count()
    total_cancelados = Evento.objects.filter(cancelado=True).count()
    total_eventos = Evento.objects.filter(Q(activo=True) | Q(cancelado=True)).count()

    print(f"\n📊 Verificación en base de datos:")
    print(f"   - Total eventos (activos o cancelados): {total_eventos}")
    print(f"   - Eventos pausados: {total_pausados}")
    print(f"   - Eventos cancelados: {total_cancelados}")
    print(f"   - Suma esperada en tarjeta: {total_pausados + total_cancelados}")

    print(f"\n🌐 Para verificar en la interfaz:")
    print(f"   1. Iniciar sesión como fed_central")
    print(f"   2. Ir a: /eventos/administracion/")
    print(
        f"   3. Verificar tarjeta 'Pausados / Cancelados' muestre: {total_pausados + total_cancelados}"
    )
    print(
        f"   4. Verificar que el evento '{evento_pausado.nombre}' aparezca en la tabla con estado 'Pausado'"
    )


if __name__ == "__main__":
    from django.db.models import Q

    crear_evento_pausado()
