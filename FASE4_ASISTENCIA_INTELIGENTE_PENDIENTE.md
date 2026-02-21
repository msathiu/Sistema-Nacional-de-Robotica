# 🤖 Fase 4: Asistencia Inteligente para Corrección de Clubes (PENDIENTE)

## 🎯 Objetivo

Implementar sistema de asistencia inteligente que guíe a las instituciones en la corrección de clubes rechazados, reduciendo el tiempo de corrección y aumentando la tasa de aprobación en el primer reenvío.

---

## 📋 Estado: ⏳ PENDIENTE DE IMPLEMENTACIÓN

**Prioridad**: Baja-Media  
**Complejidad**: Alta  
**Tiempo Estimado**: 3-4 días  
**Dependencias**: Fase 1, 2 y 3 completadas

---

## 🎯 Funcionalidades a Implementar

### 1. Sugerencias Automáticas Basadas en Rechazos

**Objetivo**: Proporcionar tips contextuales según el motivo de rechazo.

**Funcionamiento**:
```
Club Rechazado → Analizar Motivo → Generar Sugerencias → Mostrar en UI
```

**Ejemplo de Flujo**:
```
Motivo: "Documentación incompleta"
    ↓
Sugerencias:
✓ Adjuntar acta constitutiva del club
✓ Incluir lista de miembros fundadores
✓ Agregar plan de trabajo anual
✓ Subir evidencias de actividades previas
```

**Implementación Sugerida**:
```python
# registry/asistente.py
class AsistenteCorreccion:
    """Sistema de asistencia para corrección de clubes."""
    
    SUGERENCIAS = {
        'documentacion_incompleta': [
            {
                'titulo': 'Acta Constitutiva',
                'descripcion': 'Adjunta el acta de constitución del club firmada',
                'prioridad': 'alta',
                'ejemplo_url': '/media/ejemplos/acta_ejemplo.pdf'
            },
            {
                'titulo': 'Lista de Miembros',
                'descripcion': 'Incluye lista completa con nombres, cédulas y roles',
                'prioridad': 'alta',
                'ejemplo_url': '/media/ejemplos/lista_miembros.xlsx'
            },
            {
                'titulo': 'Plan de Trabajo',
                'descripcion': 'Presenta plan de actividades para el año',
                'prioridad': 'media',
                'ejemplo_url': '/media/ejemplos/plan_trabajo.pdf'
            }
        ],
        'lineas_investigacion_vagas': [
            {
                'titulo': 'Especificar Áreas',
                'descripcion': 'Define áreas concretas: robótica móvil, visión artificial, etc.',
                'prioridad': 'alta',
                'ejemplo': 'En lugar de "robótica en general", especifica "robótica móvil autónoma para agricultura"'
            },
            {
                'titulo': 'Objetivos Medibles',
                'descripcion': 'Establece objetivos SMART (específicos, medibles, alcanzables)',
                'prioridad': 'alta',
                'ejemplo': 'Desarrollar 3 prototipos de robots móviles en 6 meses'
            }
        ],
        'descripcion_insuficiente': [
            {
                'titulo': 'Ampliar Descripción',
                'descripcion': 'Mínimo 200 palabras describiendo el club',
                'prioridad': 'alta',
                'checklist': [
                    '¿Qué hace el club?',
                    '¿Quiénes participan?',
                    '¿Qué proyectos desarrollan?',
                    '¿Qué impacto buscan?'
                ]
            }
        ]
    }
    
    @classmethod
    def obtener_sugerencias(cls, categoria_rechazo):
        """Obtiene sugerencias según categoría de rechazo."""
        return cls.SUGERENCIAS.get(categoria_rechazo, [])
    
    @classmethod
    def generar_checklist_correccion(cls, club):
        """Genera checklist personalizado de corrección."""
        ultimo_rechazo = club.obtener_ultimo_rechazo()
        if not ultimo_rechazo or not ultimo_rechazo.categoria_rechazo:
            return []
        
        sugerencias = cls.obtener_sugerencias(ultimo_rechazo.categoria_rechazo)
        
        checklist = []
        for sug in sugerencias:
            checklist.append({
                'item': sug['titulo'],
                'descripcion': sug['descripcion'],
                'completado': False,
                'prioridad': sug.get('prioridad', 'media')
            })
        
        return checklist
```

---

### 2. Plantillas y Ejemplos de Clubes Exitosos

**Objetivo**: Proporcionar referencias de clubes aprobados como guía.

**Funcionalidades**:
- Biblioteca de ejemplos por categoría
- Plantillas descargables (Word, PDF)
- Casos de éxito anonimizados
- Comparación lado a lado

**Implementación Sugerida**:
```python
# registry/models.py
class PlantillaClub(models.Model):
    """Plantillas de ejemplo para creación de clubes."""
    
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    categoria = models.CharField(max_length=50, choices=[
        ('robotica_educativa', 'Robótica Educativa'),
        ('robotica_competitiva', 'Robótica Competitiva'),
        ('investigacion', 'Investigación y Desarrollo'),
        ('maker', 'Maker y Fabricación Digital')
    ])
    archivo_plantilla = models.FileField(upload_to='plantillas/')
    ejemplo_club = models.ForeignKey(
        'Club',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Club de ejemplo (datos anonimizados)'
    )
    descargas = models.IntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-descargas', '-fecha_creacion']
        verbose_name = 'Plantilla de Club'
        verbose_name_plural = 'Plantillas de Clubes'

# registry/views_institucional.py
def biblioteca_plantillas(request):
    """Biblioteca de plantillas y ejemplos."""
    plantillas = PlantillaClub.objects.all()
    
    context = {
        'plantillas': plantillas,
        'categorias': PlantillaClub._meta.get_field('categoria').choices
    }
    return render(request, 'registry/biblioteca_plantillas.html', context)

def descargar_plantilla(request, plantilla_id):
    """Descarga plantilla y registra estadística."""
    plantilla = get_object_or_404(PlantillaClub, id=plantilla_id)
    plantilla.descargas += 1
    plantilla.save(update_fields=['descargas'])
    
    return FileResponse(
        plantilla.archivo_plantilla.open('rb'),
        as_attachment=True,
        filename=f'plantilla_{plantilla.titulo}.docx'
    )
```

**Template Sugerido**:
```django
<!-- registry/biblioteca_plantillas.html -->
<div class="row">
    {% for plantilla in plantillas %}
    <div class="col-md-6 mb-4">
        <div class="card">
            <div class="card-header bg-primary text-white">
                <h5>{{ plantilla.titulo }}</h5>
                <span class="badge bg-light text-dark">
                    {{ plantilla.get_categoria_display }}
                </span>
            </div>
            <div class="card-body">
                <p>{{ plantilla.descripcion }}</p>
                
                {% if plantilla.ejemplo_club %}
                <div class="alert alert-info">
                    <strong>Basado en club exitoso:</strong>
                    <a href="{% url 'ver_ejemplo_club' plantilla.ejemplo_club.id %}">
                        Ver ejemplo
                    </a>
                </div>
                {% endif %}
                
                <div class="d-flex justify-content-between align-items-center">
                    <small class="text-muted">
                        <i class="bi bi-download"></i> {{ plantilla.descargas }} descargas
                    </small>
                    <a href="{% url 'descargar_plantilla' plantilla.id %}" 
                       class="btn btn-primary btn-sm">
                        <i class="bi bi-download"></i> Descargar
                    </a>
                </div>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
```

---

### 3. Sistema de Chat/Consultas con Federación

**Objetivo**: Canal directo de comunicación para aclarar dudas sobre rechazos.

**Funcionalidades**:
- Chat en tiempo real (opcional)
- Sistema de tickets/consultas
- Historial de conversaciones
- Notificaciones de respuestas

**Implementación Sugerida**:
```python
# registry/models.py
class ConsultaClub(models.Model):
    """Consultas de instituciones sobre clubes rechazados."""
    
    club = models.ForeignKey('Club', on_delete=models.CASCADE, related_name='consultas')
    institucion = models.ForeignKey('Institucion', on_delete=models.CASCADE)
    usuario_consulta = models.ForeignKey(User, on_delete=models.CASCADE, related_name='consultas_realizadas')
    
    asunto = models.CharField(max_length=200)
    mensaje = models.TextField()
    fecha_consulta = models.DateTimeField(auto_now_add=True)
    
    # Respuesta
    respondido_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consultas_respondidas'
    )
    respuesta = models.TextField(blank=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    
    estado = models.CharField(
        max_length=20,
        choices=[
            ('pendiente', 'Pendiente'),
            ('en_proceso', 'En Proceso'),
            ('respondida', 'Respondida'),
            ('cerrada', 'Cerrada')
        ],
        default='pendiente'
    )
    
    class Meta:
        ordering = ['-fecha_consulta']
        verbose_name = 'Consulta de Club'
        verbose_name_plural = 'Consultas de Clubes'
        indexes = [
            models.Index(fields=['estado', '-fecha_consulta']),
            models.Index(fields=['club', '-fecha_consulta']),
        ]

# registry/views_institucional.py
@login_required
def crear_consulta_club(request, club_id):
    """Crear consulta sobre club rechazado."""
    club = get_object_or_404(Club, id=club_id)
    institucion = request.user.perfil.institucion
    
    if club.institucion_creadora != institucion:
        messages.error(request, "No tienes permiso para consultar sobre este club.")
        return redirect('clubes_lista')
    
    if request.method == 'POST':
        asunto = request.POST.get('asunto')
        mensaje = request.POST.get('mensaje')
        
        consulta = ConsultaClub.objects.create(
            club=club,
            institucion=institucion,
            usuario_consulta=request.user,
            asunto=asunto,
            mensaje=mensaje
        )
        
        # Notificar a staff
        notificar_nueva_consulta(consulta)
        
        messages.success(request, "Consulta enviada. Recibirás respuesta pronto.")
        return redirect('ver_consulta', consulta.id)
    
    context = {'club': club}
    return render(request, 'registry/crear_consulta.html', context)

# registry/views_admin.py
@staff_member_required
def responder_consulta(request, consulta_id):
    """Responder consulta de institución."""
    consulta = get_object_or_404(ConsultaClub, id=consulta_id)
    
    if request.method == 'POST':
        respuesta = request.POST.get('respuesta')
        
        consulta.respuesta = respuesta
        consulta.respondido_por = request.user
        consulta.fecha_respuesta = timezone.now()
        consulta.estado = 'respondida'
        consulta.save()
        
        # Notificar a institución
        notificar_respuesta_consulta(consulta)
        
        messages.success(request, "Respuesta enviada correctamente.")
        return redirect('admin_consultas')
    
    context = {'consulta': consulta}
    return render(request, 'registry/responder_consulta.html', context)
```

---

### 4. Validación en Tiempo Real

**Objetivo**: Validar campos mientras la institución edita el club.

**Funcionalidades**:
- Validación de longitud de descripción
- Verificación de documentos requeridos
- Sugerencias de mejora en tiempo real
- Indicador de "completitud" del club

**Implementación Sugerida**:
```javascript
// static/registry/js/validacion_club.js
class ValidadorClub {
    constructor() {
        this.campos = {
            nombre: { min: 10, max: 100 },
            descripcion: { min: 200, max: 2000 },
            lineas_investigacion: { min: 50, max: 500 }
        };
        
        this.inicializar();
    }
    
    inicializar() {
        // Validar en tiempo real
        document.querySelectorAll('[data-validar]').forEach(campo => {
            campo.addEventListener('input', (e) => this.validarCampo(e.target));
        });
        
        // Calcular completitud
        this.actualizarCompletitud();
    }
    
    validarCampo(campo) {
        const nombre = campo.dataset.validar;
        const valor = campo.value.trim();
        const reglas = this.campos[nombre];
        
        if (!reglas) return;
        
        const feedback = campo.nextElementSibling;
        
        if (valor.length < reglas.min) {
            feedback.textContent = `Mínimo ${reglas.min} caracteres (actual: ${valor.length})`;
            feedback.className = 'text-danger';
            campo.classList.add('is-invalid');
            campo.classList.remove('is-valid');
        } else if (valor.length > reglas.max) {
            feedback.textContent = `Máximo ${reglas.max} caracteres (actual: ${valor.length})`;
            feedback.className = 'text-danger';
            campo.classList.add('is-invalid');
            campo.classList.remove('is-valid');
        } else {
            feedback.textContent = `✓ Correcto (${valor.length} caracteres)`;
            feedback.className = 'text-success';
            campo.classList.remove('is-invalid');
            campo.classList.add('is-valid');
        }
        
        this.actualizarCompletitud();
    }
    
    actualizarCompletitud() {
        const total = document.querySelectorAll('[data-validar]').length;
        const validos = document.querySelectorAll('.is-valid').length;
        const porcentaje = Math.round((validos / total) * 100);
        
        const barra = document.getElementById('barra-completitud');
        const texto = document.getElementById('texto-completitud');
        
        barra.style.width = `${porcentaje}%`;
        barra.textContent = `${porcentaje}%`;
        texto.textContent = `${validos} de ${total} campos completos`;
        
        // Cambiar color según porcentaje
        barra.className = 'progress-bar';
        if (porcentaje < 50) {
            barra.classList.add('bg-danger');
        } else if (porcentaje < 80) {
            barra.classList.add('bg-warning');
        } else {
            barra.classList.add('bg-success');
        }
    }
}

// Inicializar
document.addEventListener('DOMContentLoaded', () => {
    new ValidadorClub();
});
```

**Template con Validación**:
```django
<!-- registry/editar_club.html -->
<div class="card mb-3">
    <div class="card-header">
        <h5>Completitud del Club</h5>
    </div>
    <div class="card-body">
        <div class="progress" style="height: 30px;">
            <div id="barra-completitud" class="progress-bar" role="progressbar">
                0%
            </div>
        </div>
        <small id="texto-completitud" class="text-muted">0 de 0 campos completos</small>
    </div>
</div>

<div class="mb-3">
    <label>Descripción del Club</label>
    <textarea 
        name="descripcion" 
        class="form-control" 
        data-validar="descripcion"
        rows="5">{{ club.descripcion }}</textarea>
    <div class="form-text"></div>
</div>

<script src="{% static 'registry/js/validacion_club.js' %}"></script>
```

---

### 5. Asistente de Mejora con IA (Opcional - Avanzado)

**Objetivo**: Usar IA para sugerir mejoras en descripciones y contenido.

**Funcionalidades**:
- Análisis de texto con NLP
- Sugerencias de mejora de redacción
- Detección de información faltante
- Comparación con clubes exitosos

**Implementación Sugerida** (requiere API externa):
```python
# registry/asistente_ia.py
import openai  # o cualquier API de IA

class AsistenteIA:
    """Asistente con IA para mejorar clubes."""
    
    @staticmethod
    def analizar_descripcion(descripcion):
        """Analiza descripción y sugiere mejoras."""
        prompt = f"""
        Analiza la siguiente descripción de un club de robótica y sugiere mejoras:
        
        Descripción: {descripcion}
        
        Proporciona:
        1. Puntos fuertes
        2. Áreas de mejora
        3. Sugerencias específicas
        4. Puntuación de claridad (1-10)
        """
        
        # Llamada a API (ejemplo con OpenAI)
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.choices[0].message.content
    
    @staticmethod
    def comparar_con_exitosos(club):
        """Compara club con clubes aprobados similares."""
        clubes_exitosos = Club.objects.filter(
            status='aprobado',
            categoria=club.categoria
        )[:5]
        
        # Análisis comparativo
        analisis = {
            'longitud_descripcion_promedio': clubes_exitosos.aggregate(
                Avg(Length('descripcion'))
            ),
            'num_lineas_promedio': clubes_exitosos.aggregate(
                Avg('lineas_investigacion__count')
            ),
            'recomendaciones': []
        }
        
        return analisis
```

---

## 📁 Archivos a Crear/Modificar

### Nuevos Archivos

```
registry/
├── asistente.py                    # Lógica de asistencia (nuevo)
├── asistente_ia.py                 # Asistente con IA (opcional)
├── models.py                       # Agregar PlantillaClub, ConsultaClub
├── views_asistente.py              # Vistas de asistencia (nuevo)
├── notificaciones.py               # Agregar notificaciones de consultas
├── templates/registry/
│   ├── biblioteca_plantillas.html  # Biblioteca de plantillas
│   ├── crear_consulta.html         # Formulario de consulta
│   ├── ver_consulta.html           # Ver consulta y respuesta
│   ├── responder_consulta.html     # Admin responde consulta
│   └── asistente_correccion.html   # Panel de asistencia
└── static/registry/
    ├── js/
    │   ├── validacion_club.js      # Validación en tiempo real
    │   └── asistente.js            # Interacción con asistente
    └── ejemplos/                   # Archivos de ejemplo
        ├── acta_ejemplo.pdf
        ├── lista_miembros.xlsx
        └── plan_trabajo.pdf
```

### Archivos a Modificar

```
registry/
├── models.py                       # Agregar modelos nuevos
├── urls.py                         # Rutas de asistente y consultas
├── views_institucional.py          # Integrar asistente en edición
└── templates/registry/
    └── editar_club.html            # Agregar panel de asistencia
```

---

## 🛠 Dependencias Técnicas

### Backend

```bash
# requirements.txt
openai==1.3.0           # API de IA (opcional)
nltk==3.8.1             # Procesamiento de lenguaje natural
textblob==0.17.1        # Análisis de sentimientos
```

### Frontend

```html
<!-- Librerías JavaScript -->
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>  <!-- Markdown -->
<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>        <!-- Alertas bonitas -->
```

---

## 📊 Flujo de Usuario

```
1. CLUB RECHAZADO
   ↓
2. Institución accede a "Corregir"
   ↓
3. Sistema muestra:
   - Motivo de rechazo
   - Sugerencias automáticas
   - Checklist de corrección
   - Ejemplos de clubes exitosos
   ↓
4. Institución edita club con:
   - Validación en tiempo real
   - Indicador de completitud
   - Tips contextuales
   ↓
5. ¿Tiene dudas?
   ├─ SÍ → Crear consulta a federación
   │         ↓
   │      Esperar respuesta
   │         ↓
   │      Continuar corrección
   │
   └─ NO → Continuar
   ↓
6. Reenviar a revisión
```

---

## ✅ Checklist de Implementación

### Fase 4.1: Sugerencias Automáticas
- [ ] Crear clase `AsistenteCorreccion`
- [ ] Definir diccionario de sugerencias por categoría
- [ ] Implementar método `obtener_sugerencias()`
- [ ] Implementar método `generar_checklist_correccion()`
- [ ] Crear template con sugerencias
- [ ] Integrar en vista de edición

### Fase 4.2: Plantillas y Ejemplos
- [ ] Crear modelo `PlantillaClub`
- [ ] Migración de base de datos
- [ ] Vista de biblioteca de plantillas
- [ ] Vista de descarga de plantillas
- [ ] Crear plantillas de ejemplo (Word/PDF)
- [ ] Anonimizar clubes de ejemplo
- [ ] Template de biblioteca

### Fase 4.3: Sistema de Consultas
- [ ] Crear modelo `ConsultaClub`
- [ ] Migración de base de datos
- [ ] Vista para crear consulta (institución)
- [ ] Vista para responder consulta (admin)
- [ ] Vista para ver consultas (ambos)
- [ ] Notificaciones de nueva consulta
- [ ] Notificaciones de respuesta
- [ ] Templates de consultas

### Fase 4.4: Validación en Tiempo Real
- [ ] Crear archivo `validacion_club.js`
- [ ] Implementar clase `ValidadorClub`
- [ ] Validación de longitud de campos
- [ ] Indicador de completitud
- [ ] Feedback visual (colores)
- [ ] Integrar en template de edición

### Fase 4.5: Asistente IA (Opcional)
- [ ] Configurar API de IA
- [ ] Crear clase `AsistenteIA`
- [ ] Implementar análisis de descripción
- [ ] Implementar comparación con exitosos
- [ ] Vista de análisis IA
- [ ] Template de resultados IA

### Testing
- [ ] Test de generación de sugerencias
- [ ] Test de descarga de plantillas
- [ ] Test de creación de consultas
- [ ] Test de respuesta de consultas
- [ ] Test de validación JavaScript
- [ ] Test de permisos

### Documentación
- [ ] Documentar clase AsistenteCorreccion
- [ ] Guía de uso para instituciones
- [ ] Guía de respuesta para federación
- [ ] Actualizar README.md

---

## 🎯 Beneficios Esperados

1. **Reducción de Tiempo**: -50% en tiempo de corrección
2. **Mayor Tasa de Aprobación**: +30% en primer reenvío
3. **Mejor Calidad**: Clubes más completos y claros
4. **Menos Consultas**: Sugerencias automáticas reducen dudas
5. **Experiencia Mejorada**: Institución guiada paso a paso
6. **Eficiencia Federación**: Menos tiempo respondiendo consultas básicas

---

## 📈 Métricas de Éxito

- ✅ 80% de instituciones usan sugerencias automáticas
- ✅ 50% de plantillas descargadas antes de reenvío
- ✅ Tiempo de corrección reducido de 7 a 3 días promedio
- ✅ Tasa de aprobación en 1er reenvío aumenta de 45% a 75%
- ✅ 90% de consultas respondidas en < 24 horas
- ✅ Satisfacción de instituciones > 4.5/5

---

## 🚀 Roadmap de Implementación

### Sprint 1 (1 semana)
- Sugerencias automáticas
- Checklist de corrección

### Sprint 2 (1 semana)
- Plantillas y ejemplos
- Biblioteca descargable

### Sprint 3 (1 semana)
- Sistema de consultas
- Notificaciones

### Sprint 4 (1 semana)
- Validación en tiempo real
- Indicador de completitud

### Sprint 5 (Opcional - 1 semana)
- Asistente con IA
- Análisis avanzado

---

**Prioridad**: Baja-Media  
**Estado**: ⏳ Pendiente  
**Próximo Paso**: Evaluar ROI y priorizar con equipo
