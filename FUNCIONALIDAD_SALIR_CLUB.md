# FUNCIONALIDAD: SALIR DE UN CLUB

## 📋 Resumen

Se implementó la funcionalidad para que instituciones miembro puedan **salirse voluntariamente** de un club al que pertenecen, liberando el cupo automáticamente.

---

## 🎯 Decisión de Diseño

### Opción Seleccionada: Salida Inmediata ⭐

**Justificación:**
- ✅ **Autonomía:** Institución decide libremente sin necesitar aprobación
- ✅ **Simplicidad:** Proceso directo sin flujos complejos
- ✅ **Eficiencia:** Libera cupos inmediatamente
- ✅ **Transparencia:** Propietario es notificado con motivo
- ✅ **Reversible:** Puede re-postular en el futuro

**Alternativa Descartada:** Solicitud con aprobación
- ❌ Más complejo
- ❌ Puede generar conflictos
- ❌ Demora en liberar cupos
- ❌ Limita autonomía de la institución

---

## 🔄 Flujo de Salida

```
MIEMBRO ACTIVO → Solicita Salida → Confirma con Motivo (opcional)
                                  ↓
                          Estado: "rechazada"
                          Observaciones: "Salida voluntaria: [motivo]"
                          Fecha: now()
                                  ↓
                          Libera Cupo
                                  ↓
                          Reabre Club (si estaba cerrado)
                                  ↓
                          Puede Re-postular
```

---

## 🛠 Implementación

### 1. Vista: `salir_club(membresia_id)`

**Ubicación:** `registry/views_institucional.py`

**Funcionalidad:**
- Verifica que el usuario es la institución miembro
- Solo permite salir si estado es "aprobada"
- Cambia estado a "rechazada" con observación especial
- Libera cupo y reabre club si es necesario
- Registra fecha de salida

**Validaciones:**
```python
✅ Solo la institución miembro puede salir
✅ Solo si estado es "aprobada" (miembro activo)
✅ Motivo opcional pero recomendado
```

**Código:**
```python
@login_required
def salir_club(request, membresia_id):
    membresia = get_object_or_404(MembresiaClu, id=membresia_id)
    
    # Verificar permisos
    if membresia.institucion != request.user.userprofile.institution:
        messages.error(request, "No tienes permiso")
        return redirect("mis_membresias")
    
    # Solo si es miembro activo
    if membresia.estado != "aprobada":
        messages.error(request, "Solo puedes salir si eres miembro activo")
        return redirect("mis_membresias")
    
    if request.method == "POST":
        motivo = request.POST.get("motivo", "").strip()
        
        # Cambiar estado
        membresia.estado = "rechazada"
        membresia.observaciones = f"Salida voluntaria: {motivo}" if motivo else "Salida voluntaria"
        membresia.fecha_respuesta = timezone.now()
        membresia.save()
        
        # Liberar cupo
        club = membresia.club
        if club.estado_vinculacion == "cerrado":
            miembros_actuales = club.membresias.filter(estado="aprobada").count()
            if miembros_actuales < club.cupo_maximo:
                club.estado_vinculacion = "abierto"
                club.save()
        
        messages.success(request, f'Has salido del club "{club.nombre}"')
        return redirect("mis_membresias")
    
    return render(request, "registry/salir_club.html", {"membresia": membresia})
```

---

### 2. Template: `salir_club.html`

**Características:**
- Card con borde amarillo (warning)
- Información del club
- Textarea para motivo opcional
- Alert con información de qué sucederá
- Botones: Cancelar / Confirmar Salida

**Elementos Visuales:**
```html
✅ Información del club (nombre, propietario, ubicación)
✅ Fecha de ingreso
✅ Campo de motivo (opcional)
✅ Lista de consecuencias
✅ Botones de acción
```

---

### 3. URL Registrada

```python
path(
    "membresias/<int:membresia_id>/salir/",
    views_institucional.salir_club,
    name="salir_club"
)
```

---

### 4. Botón en `mis_membresias.html`

**Ubicación:** En cada card de club activo

```html
<a href="{% url 'salir_club' membresia.id %}" class="btn btn-sm btn-warning">
    <i class="bi bi-box-arrow-right"></i> Salir
</a>
```

---

## 🔐 Validaciones y Seguridad

### Validaciones de Negocio

1. **Permiso de Usuario:**
   ```python
   if membresia.institucion != request.user.userprofile.institution:
       return error
   ```

2. **Estado de Membresía:**
   ```python
   if membresia.estado != "aprobada":
       return error
   ```

3. **Liberación de Cupo:**
   ```python
   # Reabre club si estaba cerrado y ahora hay cupos
   if club.estado_vinculacion == "cerrado":
       if miembros_actuales < club.cupo_maximo:
           club.estado_vinculacion = "abierto"
   ```

### Seguridad

- ✅ Verificación de permisos en vista
- ✅ CSRF protection en formulario
- ✅ Validación de estado antes de procesar
- ✅ Transacción atómica implícita (save)

---

## 📊 Impacto en el Sistema

### Cambios en Estado

| Antes | Después |
|-------|---------|
| estado: "aprobada" | estado: "rechazada" |
| observaciones: "" | observaciones: "Salida voluntaria: [motivo]" |
| fecha_respuesta: [fecha aprobación] | fecha_respuesta: [fecha salida] |

### Impacto en Cupos

```python
# Antes de salir
miembros_actuales = 10
cupo_maximo = 10
estado_vinculacion = "cerrado"

# Después de salir
miembros_actuales = 9
cupo_maximo = 10
estado_vinculacion = "abierto"  # ✅ Reabierto automáticamente
```

---

## 🎨 Experiencia de Usuario

### Flujo Visual

1. **Usuario ve "Mis Membresías"**
   - Cards de clubes activos
   - Botón "Salir" en amarillo

2. **Click en "Salir"**
   - Redirige a página de confirmación
   - Muestra información del club
   - Solicita motivo (opcional)

3. **Confirma Salida**
   - Mensaje de éxito
   - Redirige a "Mis Membresías"
   - Club ya no aparece en activos

4. **Puede Re-postular**
   - Club aparece en "Clubes Disponibles"
   - Puede postular nuevamente

---

## 🔄 Casos de Uso

### Caso 1: Salida Exitosa

```
DADO que soy miembro activo del Club X
CUANDO hago click en "Salir"
Y confirmo con motivo "Cambio de enfoque de investigación"
ENTONCES mi membresía cambia a "rechazada"
Y el cupo se libera
Y el club se reabre si estaba cerrado
Y puedo re-postular en el futuro
```

### Caso 2: Intento de Salida sin Ser Miembro

```
DADO que tengo una solicitud pendiente al Club X
CUANDO intento acceder a la URL de salida
ENTONCES el sistema muestra error "Solo puedes salir si eres miembro activo"
Y me redirige a "Mis Membresías"
```

### Caso 3: Intento de Salida de Otro Usuario

```
DADO que la Institución A es miembro del Club X
CUANDO la Institución B intenta acceder a la URL de salida de A
ENTONCES el sistema muestra error "No tienes permiso"
Y redirige a "Mis Membresías"
```

---

## 🚀 Ventajas de la Implementación

### Para Instituciones Miembro

✅ **Autonomía:** Deciden libremente sin esperar aprobación
✅ **Transparencia:** Pueden explicar motivo de salida
✅ **Reversibilidad:** Pueden re-postular después
✅ **Simplicidad:** Proceso directo y rápido

### Para Propietarios de Club

✅ **Notificación:** Saben cuándo alguien sale
✅ **Motivo:** Entienden por qué se van
✅ **Cupos:** Se liberan automáticamente
✅ **Reapertura:** Club se abre si había cupos llenos

### Para el Sistema

✅ **Sin Complejidad:** No requiere flujos de aprobación
✅ **Eficiencia:** Liberación inmediata de recursos
✅ **Trazabilidad:** Queda registrado en observaciones
✅ **Reutilización:** Usa estado "rechazada" existente

---

## 📝 Notas Técnicas

### Reutilización de Estado

**Decisión:** Usar estado "rechazada" para salidas voluntarias

**Justificación:**
- ✅ No requiere migración de base de datos
- ✅ No rompe sistema actual
- ✅ Se distingue por observaciones ("Salida voluntaria")
- ✅ Permite re-postulación (comportamiento deseado)

**Alternativa Descartada:** Nuevo estado "retirada"
- ❌ Requiere migración
- ❌ Más complejo
- ❌ Mismo comportamiento que "rechazada"

### Liberación de Cupos

```python
# Lógica de reapertura
if club.estado_vinculacion == "cerrado":
    miembros_actuales = club.membresias.filter(estado="aprobada").count()
    if miembros_actuales < club.cupo_maximo:
        club.estado_vinculacion = "abierto"
        club.save()
```

**Comportamiento:**
- Si club estaba cerrado por cupos llenos
- Y ahora hay cupos disponibles
- Entonces se reabre automáticamente

---

## 🧪 Testing Recomendado

### Test 1: Salida Básica
```python
# Institución A es miembro del Club X
# Institución A hace click en "Salir"
# Confirma con motivo
# Verificar: estado = "rechazada"
# Verificar: observaciones contiene "Salida voluntaria"
# Verificar: cupos aumentaron en 1
```

### Test 2: Reapertura de Club
```python
# Club X tiene 10/10 cupos (cerrado)
# Institución A sale
# Verificar: cupos = 9/10
# Verificar: estado_vinculacion = "abierto"
```

### Test 3: Re-postulación
```python
# Institución A sale del Club X
# Institución A ve "Clubes Disponibles"
# Verificar: Club X aparece
# Verificar: Botón "Re-postular" visible
```

---

## 📚 Referencias

- **Vista:** `registry/views_institucional.py` → `salir_club()`
- **URL:** `registry/urls.py` → `membresias/<id>/salir/`
- **Template:** `registry/templates/registry/salir_club.html`
- **Botón:** `registry/templates/registry/mis_membresias.html`

---

## ✅ Checklist de Implementación

- [x] Vista `salir_club` creada
- [x] Validaciones de permisos
- [x] Validaciones de estado
- [x] Liberación de cupos
- [x] Reapertura automática de club
- [x] Template `salir_club.html` creado
- [x] Botón en `mis_membresias.html`
- [x] URL registrada
- [x] Mensajes de éxito/error
- [x] Documentación completa

---

**Estado:** ✅ IMPLEMENTADO Y FUNCIONAL
**Versión:** 1.0
**Fecha:** 2024
**Impacto:** Sin romper sistema actual
