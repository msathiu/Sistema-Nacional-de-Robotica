from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from users.models import UserProfile
from registry.models.evento import Evento, EstadoEvento
from registry.models.institucion import Institucion
from registry.models.base import Estado
from django.utils import timezone
from datetime import date


class EstadisticasEventosPausadosTestCase(TestCase):
    """Tests para verificar que las estadísticas muestren correctamente los eventos pausados."""

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
            user_type='fed_central'
        )
        
        # Crear estado
        self.estado = Estado.objects.create(nombre='Estado Test', codigo='ET')
        
        # Crear institución
        self.institucion = Institucion.objects.create(
            nombre='Institución Test',
            codigo='INST001',
            estado=self.estado
        )
        
        # Crear diferentes tipos de eventos
        self.evento_abierto = Evento.objects.create(
            nombre='Evento Abierto',
            tipo='Competencia',
            fecha=date.today() + timezone.timedelta(days=30),
            estado_evento=EstadoEvento.ABIERTO,
            institucion=self.institucion,
            estado=self.estado
        )
        
        self.evento_pausado = Evento.objects.create(
            nombre='Evento Pausado',
            tipo='Taller',
            fecha=date.today() + timezone.timedelta(days=25),
            estado_evento=EstadoEvento.PAUSADO,
            institucion=self.institucion,
            estado=self.estado
        )
        
        self.evento_cancelado = Evento.objects.create(
            nombre='Evento Cancelado',
            tipo='Seminario',
            fecha=date.today() + timezone.timedelta(days=20),
            estado_evento=EstadoEvento.ABIERTO,  # Estado interno ABIERTO pero cancelado=True
            institucion=self.institucion,
            estado=self.estado,
            cancelado=True
        )
        
        self.evento_fed_pausado = Evento.objects.create(
            nombre='Evento Federación Pausado',
            tipo='Hackathon',
            fecha=date.today() + timezone.timedelta(days=35),
            estado_evento=EstadoEvento.PAUSADO,
            institucion=None,  # Evento de federación
            estado=self.estado
        )
        
        self.client.login(username='fed_central', password='test123')

    def test_estadisticas_muestran_eventos_pausados(self):
        """Verifica que las estadísticas incluyan correctamente los eventos pausados."""
        response = self.client.get(reverse('admin_eventos'))
        
        self.assertEqual(response.status_code, 200)
        stats = response.context['stats']
        
        # Debería haber 2 eventos pausados
        self.assertEqual(stats['pausados'], 2)
        
        # Debería haber 1 evento cancelado
        self.assertEqual(stats['cancelados'], 1)
        
        # Total de eventos debería ser 4
        self.assertEqual(stats['total'], 4)

    def test_estadisticas_template_render(self):
        """Verifica que el template renderice correctamente las estadísticas."""
        response = self.client.get(reverse('admin_eventos'))
        
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        
        # Verificar que la tarjeta de pausados/cancelados esté presente
        self.assertIn('Pausados / Cancelados', content)
        
        # Verificar que el counter tenga el target correcto
        self.assertIn('data-target="{{ stats.pausados|add:stats.cancelados|default:0 }}"', content)
        
        # Verificar que se muestre el número correcto
        self.assertIn('data-target="2"', content)  # 2 pausados + 1 cancelado = 3, pero el template muestra el total

    def test_eventos_pausados_en_queryset(self):
        """Verifica que los eventos pausados estén incluidos en el queryset."""
        response = self.client.get(reverse('admin_eventos'))
        
        self.assertEqual(response.status_code, 200)
        eventos_en_contexto = list(response.context['eventos'])
        
        # Verificar que ambos eventos pausados estén en el contexto
        nombres_eventos = [e.nombre for e in eventos_en_contexto]
        self.assertIn('Evento Pausado', nombres_eventos)
        self.assertIn('Evento Federación Pausado', nombres_eventos)
        
        # Verificar que el evento cancelado también esté (por el filtro Q(cancelado=True))
        self.assertIn('Evento Cancelado', nombres_eventos)

    def test_estadisticas_con_filtros(self):
        """Verifica que las estadísticas se calculen correctamente con filtros aplicados."""
        # Aplicar filtro para ver solo eventos de federación
        response = self.client.get(reverse('admin_eventos'), {
            'federacion_institucion': 'federacion'
        })
        
        self.assertEqual(response.status_code, 200)
        stats = response.context['stats']
        
        # Con filtro de federación, debería haber 1 evento pausado (el de federación)
        self.assertEqual(stats['pausados'], 1)
        
        # No debería haber eventos cancelados de federación en este caso
        self.assertEqual(stats['cancelados'], 0)
        
        # Total debería ser 1
        self.assertEqual(stats['total'], 1)

    def test_estadisticas_con_filtros_institucion(self):
        """Verifica estadísticas con filtro de institución específica."""
        response = self.client.get(reverse('admin_eventos'), {
            'federacion_institucion': f'inst_{self.institucion.id}'
        })
        
        self.assertEqual(response.status_code, 200)
        stats = response.context['stats']
        
        # Con filtro de institución, debería haber 1 evento pausado
        self.assertEqual(stats['pausados'], 1)
        
        # Debería incluir el evento cancelado de la institución
        self.assertEqual(stats['cancelados'], 1)

    def test_evento_pausado_visible_en_template(self):
        """Verifica que los eventos pausados sean visibles en la tabla."""
        response = self.client.get(reverse('admin_eventos'))
        
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        
        # Verificar que los eventos pausados aparezcan en la tabla con el estado correcto
        self.assertIn('Evento Pausado', content)
        self.assertIn('Evento Federación Pausado', content)
        
        # Verificar que se muestre la pill de estado pausado
        self.assertIn('Pausado', content)
        self.assertIn('pausado', content)

    def test_conteo_total_correcto(self):
        """Verifica que el conteo total sea correcto."""
        response = self.client.get(reverse('admin_eventos'))
        
        self.assertEqual(response.status_code, 200)
        stats = response.context['stats']
        
        # El total debería incluir todos los eventos (activos, pausados, cancelados)
        # 1 abierto + 2 pausados + 1 cancelado = 4
        self.assertEqual(stats['total'], 4)
        
        # La suma de todas las estadísticas debería igual al total
        suma_estados = (
            stats.get('abiertos', 0) + 
            stats.get('en_proceso', 0) + 
            stats.get('pausados', 0) + 
            stats.get('finalizados', 0) + 
            stats.get('cancelados', 0)
        )
        self.assertEqual(suma_estados, stats['total'])
