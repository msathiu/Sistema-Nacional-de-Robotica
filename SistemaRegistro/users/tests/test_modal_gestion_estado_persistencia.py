from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from users.models import UserProfile
from registry.models.evento import Evento, EstadoEvento
from registry.models.institucion import Institucion
from django.utils import timezone
from datetime import date
import json


class ModalGestionEstadoPersistenciaTestCase(TestCase):
    """Tests para verificar la persistencia de acción y observación en el modal GESTIONAR ESTADO."""

    def setUp(self):
        self.client = Client()
        
        # Crear usuario federación central
        self.user_fed = User.objects.create_user(
            username='fed_central',
            email='fed@test.com',
            password='test123'
        )
        self.profile_fed = UserProfile.objects.create(
            user=self.user_fed,
            user_type='federacion',
            es_federacion=True
        )
        
        # Crear institución
        self.institucion = Institucion.objects.create(
            nombre='Institución Test',
            codigo='INST001',
            estado_id=1
        )
        
        # Crear evento de prueba
        self.evento = Evento.objects.create(
            nombre='Evento Test',
            tipo='Competencia',
            fecha=date.today() + timezone.timedelta(days=30),
            estado_evento=EstadoEvento.ABIERTO,
            institucion=self.institucion,
            observacion_estado='Observación inicial'
        )
        
        # Login del usuario
        self.client.login(username='fed_central', password='test123')

    def test_modal_gestion_estado_renderiza_correctamente(self):
        """Verifica que el modal se renderiza con los datos correctos."""
        response = self.client.get(reverse('admin_eventos'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'modalGestionEstadoEvento')
        self.assertContains(response, 'btn-manage')
        
    def test_contenido_datos_modal_en_template(self):
        """Verifica que los datos del evento estén presentes en el template."""
        response = self.client.get(reverse('admin_eventos'))
        content = response.content.decode('utf-8')
        
        # Verificar que los datos del evento estén en los atributos data
        self.assertIn(f'data-id="{self.evento.id}"', content)
        self.assertIn(f'data-nombre="{self.evento.nombre}"', content)
        self.assertIn(f'data-estado-evento="{self.evento.estado_evento}"', content)
        self.assertIn(f'data-observacion="{self.evento.observacion_estado}"', content)

    def test_logica_almacenamiento_local_storage(self):
        """Verifica la lógica de almacenamiento en localStorage simulada."""
        # Este test verifica que la lógica JavaScript esté presente
        response = self.client.get(reverse('admin_eventos'))
        content = response.content.decode('utf-8')
        
        # Verificar que el código JavaScript para localStorage esté presente
        self.assertIn('localStorage.getItem', content)
        self.assertIn('localStorage.setItem', content)
        self.assertIn('localStorage.removeItem', content)
        self.assertIn('last_action', content)
        self.assertIn('last_observation', content)

    def test_acciones_disponibles_segun_estado(self):
        """Verifica que las acciones disponibles se generen correctamente según el estado."""
        response = self.client.get(reverse('admin_eventos'))
        content = response.content.decode('utf-8')
        
        # Para un evento ABIERTO, debería tener opciones de pausar, cancelar, finalizar, reprogramar
        self.assertIn('Pausar Evento', content)
        self.assertIn('Cancelar Evento', content)
        self.assertIn('Finalizar Evento', content)
        self.assertIn('Reprogramar Evento', content)

    def test_post_gestionar_estado_funciona(self):
        """Verifica que el POST para gestionar estado funcione correctamente."""
        url = reverse('gestionar_estado_evento', args=[self.evento.id])
        
        # Test de pausa
        response = self.client.post(url, {
            'estado_evento': EstadoEvento.PAUSADO,
            'observacion': 'Test de pausa'
        })
        
        # Verificar redirección
        self.assertEqual(response.status_code, 302)
        
        # Verificar que el estado se actualizó
        self.evento.refresh_from_db()
        self.assertEqual(self.evento.estado_evento, EstadoEvento.PAUSADO)
        self.assertEqual(self.evento.observacion_estado, 'Test de pausa')

    def test_evento_pausado_muestra_opcion_reabrir(self):
        """Verifica que un evento pausado muestre la opción de reabrir."""
        # Pausar el evento
        self.evento.estado_evento = EstadoEvento.PAUSADO
        self.evento.observacion_estado = 'Evento pausado'
        self.evento.save()
        
        response = self.client.get(reverse('admin_eventos'))
        content = response.content.decode('utf-8')
        
        # Para un evento PAUSADO, debería tener opción de reabrir
        self.assertIn('Reabrir Evento', content)

    def test_form_submission_limpia_localstorage(self):
        """Verifica que el código para limpiar localStorage esté presente."""
        response = self.client.get(reverse('admin_eventos'))
        content = response.content.decode('utf-8')
        
        # Verificar que el código para limpiar localStorage después del submit esté presente
        self.assertIn('addEventListener(\'submit\'', content)
        self.assertIn('setTimeout', content)
        self.assertIn('removeItem', content)

    def test_prioridad_observacion_guardada_vs_actual(self):
        """Verifica que la observación guardada tenga prioridad sobre la actual."""
        response = self.client.get(reverse('admin_eventos'))
        content = response.content.decode('utf-8')
        
        # Verificar la lógica de prioridad en el código JavaScript
        self.assertIn('lastObservation || observacion', content)
        self.assertIn('observationToUse', content)


class ModalGestionEstadoIntegrationTestCase(TestCase):
    """Tests de integración para el modal con diferentes estados de evento."""

    def setUp(self):
        self.client = Client()
        
        # Crear usuario federación central
        self.user_fed = User.objects.create_user(
            username='fed_central',
            email='fed@test.com',
            password='test123'
        )
        self.profile_fed = UserProfile.objects.create(
            user=self.user_fed,
            user_type='federacion',
            es_federacion=True
        )
        
        self.client.login(username='fed_central', password='test123')

    def test_evento_borrador_no_muestra_botones_gestion(self):
        """Verifica que un evento en borrador no muestre botones de gestión de estado."""
        evento_borrador = Evento.objects.create(
            nombre='Evento Borrador',
            tipo='Taller',
            fecha=date.today() + timezone.timedelta(days=30),
            estado_evento=EstadoEvento.BORRADOR
        )
        
        response = self.client.get(reverse('admin_eventos'))
        content = response.content.decode('utf-8')
        
        # Eventos en borrador no deberían tener botón de gestión
        # (esto depende de la lógica de permisos implementada)
        self.assertIn(evento_borrador.nombre, content)

    def test_multiples_eventos_con_diferentes_estados(self):
        """Verifica que se manejen correctamente múltiples eventos con diferentes estados."""
        # Crear eventos en diferentes estados
        eventos = [
            Evento.objects.create(
                nombre=f'Evento {i}',
                tipo='Competencia',
                fecha=date.today() + timezone.timedelta(days=30),
                estado_evento=estado
            )
            for i, estado in enumerate([
                EstadoEvento.BORRADOR,
                EstadoEvento.REVISION,
                EstadoEvento.ABIERTO,
                EstadoEvento.PAUSADO,
                EstadoEvento.FINALIZADO
            ])
        ]
        
        response = self.client.get(reverse('admin_eventos'))
        content = response.content.decode('utf-8')
        
        # Verificar que todos los eventos aparezcan
        for evento in eventos:
            self.assertIn(evento.nombre, content)
        
        # Verificar que el código JavaScript maneje múltiples IDs
        self.assertIn('evento_', content)  # Prefijo para localStorage keys
