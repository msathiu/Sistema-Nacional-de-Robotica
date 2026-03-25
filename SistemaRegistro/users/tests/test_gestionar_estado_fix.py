from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from users.models import UserProfile
from registry.models.evento import Evento, EstadoEvento
from registry.models.institucion import Institucion
from django.utils import timezone
from datetime import date
import json


class GestionarEstadoFixTestCase(TestCase):
    """Tests para verificar el fix del problema con acciones del modal GESTIONAR ESTADO."""

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
        
        # Crear evento de prueba en estado ABIERTO
        self.evento_abierto = Evento.objects.create(
            nombre='Evento Abierto Test',
            tipo='Competencia',
            fecha=date.today() + timezone.timedelta(days=30),
            estado_evento=EstadoEvento.ABIERTO,
            institucion=self.institucion,
            observacion_estado=''
        )
        
        # Crear evento de prueba en estado PAUSADO
        self.evento_pausado = Evento.objects.create(
            nombre='Evento Pausado Test',
            tipo='Taller',
            fecha=date.today() + timezone.timedelta(days=20),
            estado_evento=EstadoEvento.PAUSADO,
            institucion=self.institucion,
            observacion_estado='Pausado por mantenimiento'
        )
        
        # Login del usuario
        self.client.login(username='fed_central', password='test123')

    def test_pausar_evento_abierto(self):
        """Verifica que se pueda pausar un evento abierto correctamente."""
        url = reverse('gestionar_estado_evento', args=[self.evento_abierto.id])
        
        response = self.client.post(url, {
            'estado_evento': 'pausado',  # Valor correcto del estado
            'observacion': 'Pausa por condiciones climáticas'
        })
        
        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)
        
        # Verificar que el estado se actualizó
        self.evento_abierto.refresh_from_db()
        self.assertEqual(self.evento_abierto.estado_evento, EstadoEvento.PAUSADO)
        self.assertEqual(self.evento_abierto.observacion_estado, 'Pausa por condiciones climáticas')

    def test_reabrir_evento_pausado(self):
        """Verifica que se pueda reabrir un evento pausado correctamente."""
        url = reverse('gestionar_estado_evento', args=[self.evento_pausado.id])
        
        response = self.client.post(url, {
            'estado_evento': 'abierto',  # Valor correcto del estado
            'observacion': 'Condiciones normalizadas'
        })
        
        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)
        
        # Verificar que el estado se actualizó
        self.evento_pausado.refresh_from_db()
        self.assertEqual(self.evento_pausado.estado_evento, EstadoEvento.ABIERTO)
        self.assertEqual(self.evento_pausado.observacion_estado, 'Condiciones normalizadas')

    def test_cancelar_evento(self):
        """Verifica que se pueda cancelar un evento correctamente."""
        url = reverse('gestionar_estado_evento', args=[self.evento_abierto.id])
        
        response = self.client.post(url, {
            'estado_evento': 'cancelado',  # Valor correcto del estado
            'observacion': 'Cancelación por falta de participantes'
        })
        
        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)
        
        # Verificar que el estado se actualizó
        self.evento_abierto.refresh_from_db()
        self.assertEqual(self.evento_abierto.estado_evento, EstadoEvento.CANCELADO)
        self.assertEqual(self.evento_abierto.cancelado, True)
        self.assertEqual(self.evento_abierto.observacion_estado, 'Cancelación por falta de participantes')

    def test_finalizar_evento(self):
        """Verifica que se pueda finalizar un evento correctamente."""
        url = reverse('gestionar_estado_evento', args=[self.evento_abierto.id])
        
        response = self.client.post(url, {
            'estado_evento': 'finalizado',  # Valor correcto del estado
            'observacion': 'Evento concluido exitosamente'
        })
        
        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)
        
        # Verificar que el estado se actualizó
        self.evento_abierto.refresh_from_db()
        self.assertEqual(self.evento_abierto.estado_evento, EstadoEvento.FINALIZADO)
        self.assertEqual(self.evento_abierto.observacion_estado, 'Evento concluido exitosamente')

    def test_reprogramar_evento(self):
        """Verifica que se pueda reprogramar un evento correctamente."""
        url = reverse('gestionar_estado_evento', args=[self.evento_abierto.id])
        nueva_fecha = date.today() + timezone.timedelta(days=45)
        
        response = self.client.post(url, {
            'estado_evento': 'reprogramar',  # Acción especial
            'observacion': 'Reprogramado por solicitud de participantes',
            'nueva_fecha': nueva_fecha.strftime('%Y-%m-%d')
        })
        
        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)
        
        # Verificar que las fechas se actualizaron pero el estado se mantuvo
        self.evento_abierto.refresh_from_db()
        self.assertEqual(self.evento_abierto.estado_evento, EstadoEvento.ABIERTO)  # Estado sin cambios
        self.assertEqual(self.evento_abierto.fecha, nueva_fecha)
        self.assertEqual(self.evento_abierto.observacion_estado, 'Reprogramado por solicitud de participantes')

    def test_accion_no_soportada_error_message(self):
        """Verifica que el mensaje de error sea claro para acciones no soportadas."""
        url = reverse('gestionar_estado_evento', args=[self.evento_abierto.id])
        
        # Intentar enviar una acción que no existe
        response = self.client.post(url, {
            'estado_evento': 'accion_inexistente',
            'observacion': 'Test'
        })
        
        # Verificar redirección (el manejo de errores redirige con mensaje)
        self.assertEqual(response.status_code, 302)
        
        # Verificar mensaje de error en la sesión
        messages = list(response.wsgi_request.messages)
        self.assertTrue(any('no soportado para esta acción' in str(msg) for msg in messages))

    def test_valores_correctos_en_template(self):
        """Verifica que el template use los valores correctos para las opciones."""
        response = self.client.get(reverse('admin_eventos'))
        content = response.content.decode('utf-8')
        
        # Verificar que los valores de las opciones sean los estados correctos
        self.assertIn('value="pausado"', content)  # No "pausar"
        self.assertIn('value="abierto"', content)  # No "reabrir"
        self.assertIn('value="cancelado"', content)
        self.assertIn('value="finalizado"', content)
        self.assertIn('value="reprogramar"', content)  # Este sí es una acción

    def test_reprogramar_sin_fecha_error(self):
        """Verifica que reprogramar sin fecha genere error apropiado."""
        url = reverse('gestionar_estado_evento', args=[self.evento_abierto.id])
        
        response = self.client.post(url, {
            'estado_evento': 'reprogramar',
            'observacion': 'Reprogramar sin fecha'
        })
        
        # Verificar redirección con error
        self.assertEqual(response.status_code, 302)
        
        # Verificar mensaje de error
        messages = list(response.wsgi_request.messages)
        self.assertTrue(any('nueva fecha para reprogramar' in str(msg) for msg in messages))

    def test_pausar_sin_observacion_error(self):
        """Verifica que pausar sin observación genere error apropiado."""
        url = reverse('gestionar_estado_evento', args=[self.evento_abierto.id])
        
        response = self.client.post(url, {
            'estado_evento': 'pausado'
            # Sin observación
        })
        
        # Verificar redirección con error
        self.assertEqual(response.status_code, 302)
        
        # Verificar mensaje de error
        messages = list(response.wsgi_request.messages)
        self.assertTrue(any('observación visible al pausar' in str(msg) for msg in messages))


class GestionarEstadoIntegrationTestCase(TestCase):
    """Tests de integración para verificar el flujo completo."""

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

    def test_flujo_completo_evento(self):
        """Verifica el flujo completo: abrir -> pausar -> reabrir -> finalizar."""
        # Crear evento
        evento = Evento.objects.create(
            nombre='Evento Flujo Completo',
            tipo='Competencia',
            fecha=date.today() + timezone.timedelta(days=30),
            estado_evento=EstadoEvento.ABIERTO
        )
        
        url = reverse('gestionar_estado_evento', args=[evento.id])
        
        # 1. Pausar evento
        response = self.client.post(url, {
            'estado_evento': 'pausado',
            'observacion': 'Pausa temporal'
        })
        self.assertEqual(response.status_code, 302)
        
        evento.refresh_from_db()
        self.assertEqual(evento.estado_evento, EstadoEvento.PAUSADO)
        
        # 2. Reabrir evento
        response = self.client.post(url, {
            'estado_evento': 'abierto',
            'observacion': 'Reapertura'
        })
        self.assertEqual(response.status_code, 302)
        
        evento.refresh_from_db()
        self.assertEqual(evento.estado_evento, EstadoEvento.ABIERTO)
        
        # 3. Finalizar evento
        response = self.client.post(url, {
            'estado_evento': 'finalizado',
            'observacion': 'Evento concluido'
        })
        self.assertEqual(response.status_code, 302)
        
        evento.refresh_from_db()
        self.assertEqual(evento.estado_evento, EstadoEvento.FINALIZADO)
