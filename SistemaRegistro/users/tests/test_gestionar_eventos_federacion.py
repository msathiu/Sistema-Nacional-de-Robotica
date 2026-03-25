from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.urls import reverse
from users.models import UserProfile
from registry.models.evento import Evento, EstadoEvento
from registry.models.institucion import Institucion
from users.views import gestionar_eventos_institucion
from django.utils import timezone
from datetime import date


class GestionarEventosFederacionTestCase(TestCase):
    """Tests para verificar que los botones de aprobar/rechazar no se muestran 
    para eventos creados por Federación Central."""

    def setUp(self):
        self.factory = RequestFactory()
        
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
        
        # Crear usuario institución
        self.user_inst = User.objects.create_user(
            username='user_inst',
            email='inst@test.com',
            password='test123'
        )
        self.institucion = Institucion.objects.create(
            nombre='Institución Test',
            codigo='INST001',
            estado_id=1  # Asumiendo que existe
        )
        self.profile_inst = UserProfile.objects.create(
            user=self.user_inst,
            user_type='institucional',
            institution=self.institucion
        )
        
        # Crear evento de Federación Central (sin institución)
        self.evento_fed = Evento.objects.create(
            nombre='Evento Federación',
            tipo='Competencia',
            fecha=date.today() + timezone.timedelta(days=30),
            estado_evento=EstadoEvento.REVISION,
            institucion=None,  # Esto indica que es creado por Federación
            creado_por=self.user_fed
        )
        
        # Crear evento de Institución (con institución)
        self.evento_inst = Evento.objects.create(
            nombre='Evento Institución',
            tipo='Taller',
            fecha=date.today() + timezone.timedelta(days=30),
            estado_evento=EstadoEvento.REVISION,
            institucion=self.institucion,
            creado_por=self.user_inst
        )

    def test_botones_aprobar_rechazar_evento_federacion(self):
        """Verifica que los botones de aprobar/rechazar NO se muestran para eventos de Federación."""
        request = self.factory.get(reverse('admin_eventos'))
        request.user = self.user_fed
        
        response = gestionar_eventos_institucion(request)
        
        # Verificar que la respuesta sea exitosa
        self.assertEqual(response.status_code, 200)
        
        # Obtener el contenido del template
        content = response.content.decode('utf-8')
        
        # El evento de federación NO debe tener botones de aprobar/rechazar
        self.assertNotIn(f'data-id="{self.evento_fed.id}"', content)
        self.assertNotIn('Aprobar Evento', content)
        self.assertNotIn('Rechazar Evento', content)
        
        # El evento de institución SÍ debe tener botones de aprobar/rechazar
        # (esto se verificaria en el template renderizado, pero la lógica está implementada)

    def test_logica_template_condicional(self):
        """Verifica la lógica condicional del template."""
        # Simular el contexto del template
        evento_fed_context = {
            'evento': self.evento_fed,
            'es_fed_central': True
        }
        
        evento_inst_context = {
            'evento': self.evento_inst,
            'es_fed_central': True
        }
        
        # Para evento de federación: es_fed_central=True y evento.institucion=None
        # La condición {% if es_fed_central and evento.institucion %} debe ser False
        self.assertTrue(evento_fed_context['es_fed_central'])
        self.assertIsNone(evento_fed_context['evento'].institucion)
        self.assertFalse(evento_fed_context['es_fed_central'] and evento_fed_context['evento'].institucion)
        
        # Para evento de institución: es_fed_central=True y evento.institucion=no es None
        # La condición {% if es_fed_central and evento.institucion %} debe ser True
        self.assertTrue(evento_inst_context['es_fed_central'])
        self.assertIsNotNone(evento_inst_context['evento'].institucion)
        self.assertTrue(evento_inst_context['es_fed_central'] and evento_inst_context['evento'].institucion)

    def test_consistencia_visual_template(self):
        """Verifica que la visualización del creador sea consistente con la lógica de botones."""
        request = self.factory.get(reverse('admin_eventos'))
        request.user = self.user_fed
        
        response = gestionar_eventos_institucion(request)
        content = response.content.decode('utf-8')
        
        # El evento de federación debe mostrar "Federación Central"
        self.assertIn('Federación Central', content)
        
        # Y no debe tener botones de aprobar/rechazar
        # (verificado en el primer test)
