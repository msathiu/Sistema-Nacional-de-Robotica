# FLUJO DE GESTIÓN DE MEMBRESÍAS - SISTEMA NACIONAL DE ROBÓTICA

## 📋 Resumen Ejecutivo

Se implementó un sistema completo de gestión de membresías para clubes aprobados, permitiendo que instituciones se postulen a clubes y que los propietarios gestionen las solicitudes de manera profesional.

---

## 🎯 Objetivos

1. **Permitir postulación**: Instituciones pueden solicitar membresía a clubes aprobados
2. **Gestión centralizada**: Propietarios de clubes gestionan solicitudes desde un dashboard
3. **Trazabilidad**: Instituciones ven el estado de sus solicitudes
4. **Control de cupos**: Sistema automático de cierre cuando se alcanza el cupo máximo
5. **Transparencia**: Motivos de rechazo visibles para solicitantes

---

## 🔄 Estados de Membresía

```
PENDIENTE → APROBADA
         ↘ RECHAZADA
```

### Estados Disponibles

| Estado | Descripción | Acciones Disponibles |
|--------|-------------|---------------------|
| **pendiente** | Solicitud enviada, esperando revisión | Aprobar / Rechazar |
| **aprobada** | Membresía activa | Ver detalle |
| **rechazada** | Solicitud rechazada con motivo | Re-postular (nuevo flujo) |

---

## 👥 Roles y Permisos

### 1. Institución Propietaria del Club
**Permisos:**
- ✅ Ver todas las membresías de sus clubes
- ✅ Aprobar solicitudes pendientes
- ✅ Rechazar solicitudes con motivo obligatorio
- ✅ Ver detalles de cualquier membresía de sus clubes

**Restricciones:**
- ❌ No puede aprobar si no hay cupos disponibles
- ❌ Solo puede gestionar clubes propios

### 2. Institución Miembro/Solicitante
**Permisos:**
- ✅ Postular a clubes aprobados con cupos disponibles
- ✅ Ver sus propias membresías (activas, pendientes, rechazadas)
- ✅ Ver detalles de sus solicitudes
- ✅ Ver motivos de rechazo

**Restricciones:**
- ❌ No puede tener múltiples solicitudes activas al mismo club
- ❌ Solo puede postular a clubes con estado "aprobado"

### 3. Federación (Admin)
**Permisos:**
- ✅ Ver todas las membresías del sistema
- ✅ Aprobar/Rechazar membresías (vista admin)
- ✅ Acceso a métricas globales

---

## 🛠 Componentes Implementados

### 1. Vistas (views_institucional.py)

#### `gestionar_membresias_club(club_id)`
**Propósito:** Dashboard para propietarios gestionar membresías de su club

**Funcionalidad:**
- Muestra métricas: miembros activos, pendientes, cupos disponibles
- Lista membresías por estado (pendientes, aprobadas, rechazadas)
- Botones de acción para aprobar/rechazar

**Permisos:** Solo propietario del club

**URL:** `/clubes/<club_id>/membresias/gestionar/`

---

#### `mis_membresias()`
**Propósito:** Vista para instituciones vean sus membresías a clubes

**Funcionalidad:**
- Dashboard con métricas (clubes activos, pendientes, rechazadas)
- Grid de clubes activos con información detallada
- Tabla de solicitudes pendientes
- Alertas de solicitudes rechazadas con motivos

**Permisos:** Solo instituciones (user_type='institucional')

**URL:** `/membresias/mis-clubes/`

---

#### `detalle_membresia(membresia_id)`
**Propósito:** Vista detallada de una membresía específica

**Funcionalidad:**
- Información completa del club e institución
- Carta de intención y propuesta técnica
- Observaciones (si existen)
- Botones de acción (si es propietario y está pendiente)

**Permisos:** Propietario del club O institución miembro

**URL:** `/membresias/<membresia_id>/detalle/`

---

#### `aprobar_membresia_club(membresia_id)`
**Propósito:** Aprobar solicitud de membresía

**Funcionalidad:**
- Verifica cupos disponibles
- Cambia estado a "aprobada"
- Registra fecha de respuesta
- Actualiza cupos del club (cierra automáticamente si se llena)

**Validaciones:**
- ✅ Solo propietario del club
- ✅ Solo si estado es "pendiente"
- ✅ Verifica cupos disponibles

**URL:** `/membresias/<membresia_id>/aprobar/`

---

#### `rechazar_membresia_club(membresia_id)`
**Propósito:** Rechazar solicitud con motivo obligatorio

**Funcionalidad:**
- Formulario con campo de observaciones obligatorio
- Cambia estado a "rechazada"
- Registra fecha de respuesta y motivo
- Motivo visible para la institución solicitante

**Validaciones:**
- ✅ Solo propietario del club
- ✅ Solo si estado es "pendiente"
- ✅ Motivo obligatorio

**URL:** `/membresias/<membresia_id>/rechazar/`

---

### 2. Templates

#### `gestionar_membresias_club.html`
**Características:**
- Dashboard con 4 métricas visuales
- Tabla de solicitudes pendientes con botones aprobar/rechazar
- Grid de miembros activos con cards
- Lista de membresías rechazadas

**Métricas:**
1. Miembros Activos (badge verde)
2. Solicitudes Pendientes (badge amarillo)
3. Cupos Disponibles (badge azul)
4. Cupo Máximo (badge secundario)

---

#### `mis_membresias.html`
**Características:**
- Dashboard con 3 métricas
- Grid de clubes activos (cards con información)
- Tabla de solicitudes pendientes
- Alertas de solicitudes rechazadas con motivos

**Métricas:**
1. Clubes Activos (badge verde)
2. Solicitudes Pendientes (badge amarillo)
3. Solicitudes Rechazadas (badge rojo)

---

#### `detalle_membresia.html`
**Características:**
- Información del club (card azul)
- Información de la institución miembro (card info)
- Detalles de la membresía (estado, tipo de línea, fechas)
- Carta de intención (card expandible)
- Propuesta técnica (card expandible)
- Observaciones (si existen, card amarillo)
- Acciones (solo para propietario si está pendiente)

---

#### `rechazar_membresia_club.html`
**Características:**
- Formulario con información de la solicitud
- Campo de observaciones obligatorio (textarea)
- Validación en frontend y backend
- Botones cancelar/rechazar

---

### 3. URLs Registradas

```python
# Gestión de Membresías - Instituciones
path("clubes/<int:club_id>/membresias/gestionar/", gestionar_membresias_club, name="gestionar_membresias_club"),
path("membresias/mis-clubes/", mis_membresias, name="mis_membresias"),
path("membresias/<int:membresia_id>/detalle/", detalle_membresia, name="detalle_membresia"),
path("membresias/<int:membresia_id>/aprobar/", aprobar_membresia_club, name="aprobar_membresia_club"),
path("membresias/<int:membresia_id>/rechazar/", rechazar_membresia_club, name="rechazar_membresia_club"),
```

---

## 📊 Modelo de Datos

### MembresiaClu

```python
class MembresiaClu(models.Model):
    club = ForeignKey(Club, related_name="membresias")
    institucion = ForeignKey(Institucion)
    carta_intencion = TextField()
    propuesta_tecnica = TextField()
    representante_legal = CharField(max_length=200)
    tipo_linea = CharField(choices=TIPO_LINEA_CHOICES)  # soporte, afines, vinculantes
    estado = CharField(choices=ESTADO_CHOICES)  # pendiente, aprobada, rechazada
    fecha_solicitud = DateTimeField(auto_now_add=True)
    fecha_respuesta = DateTimeField(null=True, blank=True)
    observaciones = TextField(blank=True)
```

**Índices:**
- Índice único parcial: `(club, institucion)` solo para estados activos (pendiente/revision)
- Permite re-postulación después de rechazo

---

## 🔐 Validaciones Implementadas

### Validaciones de Negocio

1. **Postulación:**
   - ✅ Club debe estar aprobado
   - ✅ Club debe tener cupos disponibles
   - ✅ No puede haber solicitud activa previa
   - ✅ Institución no puede postular a su propio club

2. **Aprobación:**
   - ✅ Solo propietario del club
   - ✅ Solo si estado es "pendiente"
   - ✅ Verifica cupos disponibles antes de aprobar
   - ✅ Cierra club automáticamente si se llena

3. **Rechazo:**
   - ✅ Solo propietario del club
   - ✅ Solo si estado es "pendiente"
   - ✅ Motivo obligatorio (validación frontend y backend)

4. **Acceso a Detalles:**
   - ✅ Solo propietario del club O institución miembro
   - ✅ Validación de permisos en cada vista

---

## 🎨 Interfaz de Usuario

### Diseño Visual

**Colores por Estado:**
- 🟢 Verde: Aprobada / Activa
- 🟡 Amarillo: Pendiente
- 🔴 Rojo: Rechazada
- 🔵 Azul: Información / Cupos

**Componentes Bootstrap:**
- Cards con sombras
- Badges para estados
- Tablas responsivas
- Botones con iconos Bootstrap Icons
- Alerts para mensajes importantes

---

## 📈 Métricas y KPIs

### Dashboard Propietario
1. **Miembros Activos:** Count de membresías aprobadas
2. **Solicitudes Pendientes:** Count de membresías pendientes
3. **Cupos Disponibles:** `cupo_maximo - miembros_activos`
4. **Cupo Máximo:** Configurado en el club

### Dashboard Institución
1. **Clubes Activos:** Count de membresías aprobadas
2. **Solicitudes Pendientes:** Count de membresías pendientes
3. **Solicitudes Rechazadas:** Count de membresías rechazadas

---

## 🔄 Flujo de Uso Completo

### Caso 1: Postulación Exitosa

```
1. Institución A ve directorio de clubes aprobados
2. Selecciona Club X con cupos disponibles
3. Completa formulario de postulación:
   - Carta de intención
   - Propuesta técnica
   - Representante legal
   - Tipo de línea (soporte/afines/vinculantes)
4. Sistema crea MembresiaClu con estado="pendiente"
5. Institución A ve solicitud en "Mis Membresías" → Pendientes
6. Propietario de Club X ve solicitud en "Gestionar Membresías"
7. Propietario revisa y aprueba
8. Sistema actualiza estado="aprobada", fecha_respuesta=now()
9. Sistema verifica cupos y cierra club si es necesario
10. Institución A ve membresía en "Mis Membresías" → Activas
```

### Caso 2: Postulación Rechazada

```
1-6. [Igual que Caso 1]
7. Propietario revisa y rechaza con motivo
8. Sistema actualiza estado="rechazada", observaciones="motivo", fecha_respuesta=now()
9. Institución A ve membresía en "Mis Membresías" → Rechazadas
10. Institución A puede ver motivo de rechazo
11. [Futuro] Institución A puede re-postular después de correcciones
```

### Caso 3: Sin Cupos Disponibles

```
1. Institución A intenta postular a Club X
2. Sistema verifica: cupos_disponibles = 0
3. Sistema muestra mensaje: "Este club no acepta postulaciones"
4. Botón "Postular" deshabilitado
5. Club X aparece con badge "Cerrado" en directorio
```

---

## 🚀 Mejoras Futuras (Roadmap)

### Fase 2: Notificaciones
- [ ] Notificar propietario cuando recibe nueva solicitud
- [ ] Notificar institución cuando su solicitud es aprobada/rechazada
- [ ] Email automático con resultado de solicitud

### Fase 3: Re-postulación
- [ ] Permitir re-postular después de rechazo
- [ ] Mostrar historial de postulaciones previas
- [ ] Límite de intentos de postulación

### Fase 4: Gestión Avanzada
- [ ] Revocar membresías aprobadas
- [ ] Suspender membresías temporalmente
- [ ] Historial de cambios de estado
- [ ] Exportar lista de miembros (CSV/PDF)

### Fase 5: Métricas Avanzadas
- [ ] Dashboard de métricas globales (federación)
- [ ] Gráficos de postulaciones por mes
- [ ] Tasa de aprobación/rechazo por club
- [ ] Clubes más populares

---

## 🧪 Casos de Prueba

### Test 1: Postulación Básica
```
DADO que soy una institución aprobada
CUANDO postulo a un club con cupos disponibles
ENTONCES mi solicitud se crea con estado "pendiente"
Y aparece en "Mis Membresías" → Pendientes
```

### Test 2: Aprobación con Cupos
```
DADO que soy propietario de un club con 2 cupos disponibles
CUANDO apruebo una solicitud pendiente
ENTONCES la membresía cambia a "aprobada"
Y los cupos disponibles se reducen a 1
Y el club permanece "abierto"
```

### Test 3: Aprobación Sin Cupos
```
DADO que soy propietario de un club con 1 cupo disponible
CUANDO apruebo la última solicitud pendiente
ENTONCES la membresía cambia a "aprobada"
Y los cupos disponibles se reducen a 0
Y el club cambia automáticamente a "cerrado"
```

### Test 4: Rechazo Sin Motivo
```
DADO que soy propietario de un club
CUANDO intento rechazar una solicitud sin motivo
ENTONCES el sistema muestra error "Debes proporcionar un motivo"
Y la solicitud permanece en estado "pendiente"
```

### Test 5: Acceso No Autorizado
```
DADO que soy Institución A
CUANDO intento acceder a membresía de Institución B
ENTONCES el sistema muestra error "No tienes permiso"
Y me redirige a "Mis Membresías"
```

---

## 📝 Notas Técnicas

### Optimizaciones Implementadas
1. **Select Related:** Uso de `select_related()` para reducir queries
2. **Validación Temprana:** Verificaciones antes de operaciones costosas
3. **Índices de BD:** Índice parcial para búsquedas eficientes
4. **Cierre Automático:** Actualización de estado del club en el save()

### Consideraciones de Seguridad
1. **Validación de Permisos:** En cada vista antes de cualquier operación
2. **CSRF Protection:** Tokens en todos los formularios POST
3. **SQL Injection:** Uso de ORM de Django (protección automática)
4. **XSS Protection:** Templates con auto-escape activado

### Mantenibilidad
1. **Código Documentado:** Docstrings en todas las funciones
2. **Nombres Descriptivos:** Variables y funciones auto-explicativas
3. **Separación de Responsabilidades:** Vistas, templates y lógica separadas
4. **Reutilización:** Templates base y componentes reutilizables

---

## 📚 Referencias

- **Modelo:** `registry/models.py` → `MembresiaClu`
- **Vistas:** `registry/views_institucional.py` → Sección "GESTIÓN DE MEMBRESÍAS"
- **URLs:** `registry/urls.py` → Sección "Gestión de Membresías - Instituciones"
- **Templates:** `registry/templates/registry/`
  - `gestionar_membresias_club.html`
  - `mis_membresias.html`
  - `detalle_membresia.html`
  - `rechazar_membresia_club.html`

---

## ✅ Checklist de Implementación

- [x] Modelo `MembresiaClu` con campos necesarios
- [x] Vista `gestionar_membresias_club` para propietarios
- [x] Vista `mis_membresias` para instituciones
- [x] Vista `detalle_membresia` con permisos
- [x] Vista `aprobar_membresia_club` con validaciones
- [x] Vista `rechazar_membresia_club` con motivo obligatorio
- [x] Template `gestionar_membresias_club.html` con dashboard
- [x] Template `mis_membresias.html` con métricas
- [x] Template `detalle_membresia.html` completo
- [x] Template `rechazar_membresia_club.html` con formulario
- [x] URLs registradas en `urls.py`
- [x] Validaciones de permisos en todas las vistas
- [x] Validaciones de negocio (cupos, estados)
- [x] Cierre automático de club al llenar cupos
- [x] Mensajes de éxito/error apropiados
- [x] Documentación completa del flujo

---

**Fecha de Implementación:** 2024
**Versión:** 1.0
**Estado:** ✅ Completado y Funcional
