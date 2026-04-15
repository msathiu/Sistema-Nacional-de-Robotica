#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SistemaRegistro.settings")
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from users.models import UserProfile
from registry.models.evento import Evento, EstadoEvento
from registry.models.institucion import Institucion
from registry.models.base import Estado
from django.utils import timezone
from datetime import date
from django.urls import reverse


def verificar_estadisticas():
    print("🔍 Verificando estadísticas de eventos pausados...")

    # Crear usuario federación central
    user_fed = User.objects.create_user(
        username="fed_test", email="fed@test.com", password="test123"
    )

    profile_fed = UserProfile.objects.create(user=user_fed, user_type="fed_central")

    # Crear estado
    estado = Estado.objects.create(nombre="Estado Test", codigo="ET")

    # Crear institución
    institucion = Institucion.objects.create(
        nombre="Institución Test", codigo="INST001", estado=estado
    )

    # Crear evento pausado
    evento_pausado = Evento.objects.create(
        nombre="Evento Pausado Test",
        tipo="Taller",
        fecha=date.today() + timezone.timedelta(days=25),
        estado_evento=EstadoEvento.PAUSADO,
        institucion=institucion,
        estado=estado,
    )

    # Crear evento cancelado
    evento_cancelado = Evento.objects.create(
        nombre="Evento Cancelado Test",
        tipo="Seminario",
        fecha=date.today() + timezone.timedelta(days=20),
        estado_evento=EstadoEvento.ABIERTO,  # Estado interno ABIERTO pero cancelado=True
        institucion=institucion,
        estado=estado,
        cancelado=True,
    )

    print(f"✅ Evento pausado creado: {evento_pausado.nombre} (ID: {evento_pausado.id})")
    print(
        f"✅ Evento cancelado creado: {evento_cancelado.nombre} (ID: {evento_cancelado.id})"
    )

    # Verificar vista administrativa
    client = Client()
    client.login(username="fed_test", password="test123")

    response = client.get(reverse("admin_eventos"))

    if response.status_code == 200:
        stats = response.context["stats"]
        eventos = response.context["eventos"]

        print(f"\n📊 Estadísticas obtenidas:")
        print(f"   - Total: {stats['total']}")
        print(f"   - Pausados: {stats['pausados']}")
        print(f"   - Cancelados: {stats['cancelados']}")
        print(f"   - Abiertos: {stats['abiertos']}")

        print(f"\n📋 Eventos en queryset ({len(eventos)}):")
        for evento in eventos:
            print(f"   - {evento.nombre} ({evento.estado_evento})")

        # Verificar conteo esperado
        esperado_pausados = 1
        esperado_cancelados = 1
        esperado_total = 2

        print(f"\n🎯 Verificación:")
        print(
            f"   - Pausados esperados: {esperado_pausados}, obtenidos: {stats['pausados']} {'✅' if stats['pausados'] == esperado_pausados else '❌'}"
        )
        print(
            f"   - Cancelados esperados: {esperado_cancelados}, obtenidos: {stats['cancelados']} {'✅' if stats['cancelados'] == esperado_cancelados else '❌'}"
        )
        print(
            f"   - Total esperados: {esperado_total}, obtenidos: {stats['total']} {'✅' if stats['total'] == esperado_total else '❌'}"
        )

        # Verificar template
        content = response.content.decode("utf-8")
        if 'data-target="' in content:
            import re

            target_match = re.search(r'data-target="([^"]*)"', content)
            if target_match:
                target_value = target_match.group(1)
                print(f"   - Template target value: {target_value}")
                print(
                    f"   - Template renderizado correctamente: {'✅' if '2' in target_value else '❌'}"
                )

    else:
        print(f"❌ Error al acceder a vista: {response.status_code}")


if __name__ == "__main__":
    verificar_estadisticas()
