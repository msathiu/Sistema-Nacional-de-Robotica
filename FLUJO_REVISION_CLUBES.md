# 🔄 Flujo Completo de Revisión de Clubes

## 📋 Resumen del Flujo Implementado

```
BORRADOR → PENDIENTE → EN_REVISION → APROBADO/RECHAZADO
    ↓           ↓            ↓              ↓
(Institución) (Federación) (Federación) (Federación)
              Comentario   Comentario    Comentario + Notificación
```

---

## 🎯 Estados del Club

| Estado | Descripción | Quién lo establece |
|--------|-------------|-------------------|
| **BORRADOR** | Club creado pero no enviado | Institución |
| **PENDIENTE** | Esperando revisión de federación | Institución (al enviar) |
| **EN_REVISION** | Federación está revisando activamente | Federación |
| **APROBADO** | Club validado y habilitado | Federación |
| **RECHAZADO** | Club no cumple requisitos | Federación |

---

## 👥 Flujo por Rol

### 🏢 Usuario Institucional

#### 1. Crear Club
- **Acción**: Crear nuevo club desde panel institucional
- **Estado inicial**: `BORRADOR`
- **URL**: `/registry/clubes/crear/`
- **Botones disponibles**: Editar, Enviar, Eliminar

#### 2. Enviar a Revisión
- **Acción**: Enviar club a federación
- **Cambio de estado**: `BORRADOR` → `PENDIENTE`
- **URL**: `/registry/clubes/<id>/enviar-revision/`
- **Resultado**: Club aparece en panel de federación

#### 3. Ver Estado
- **Ubicación**: Lista de clubes institucionales
- **Estados visibles**:
  - `PENDIENTE`: "En proceso..."
  - `EN_REVISION`: "En proceso..."
  - `APROBADO`: Badge verde + "Activo"
  - `RECHAZADO`: Botón "Corregir" + ver motivo

#### 4. Si es Rechazado
- **Acción**: Corregir y reenviar
- **Flujo**: Editar club → Enviar nuevamente
- **Cambio**: `RECHAZADO` → `PENDIENTE`

---

### 🏛️ Federación (Central/Regional)

#### 1. Ver Clubes Pendientes
- **URL**: `/registry/admin/clubes/revisar/`
- **Tabs**:
  - **Pendientes**: Clubes con `status=pendiente`
  - **En Revisión**: Clubes con `status=en_revision`

#### 2. Ver Detalles del Club
- **Botón**: 👁️ (ícono ojo)
- **URL**: `/registry/clubes/<id>/detalle/`
- **Muestra**:
  - Información completa del club
  - Líneas de investigación
  - Documentación
  - Institución creadora

#### 3. Tomar en Revisión (Opcional)
- **Botón**: 📋 "Revisar" (azul)
- **URL**: `/registry/admin/clubes/<id>/tomar-revision/`
- **Cambio de estado**: `PENDIENTE` → `EN_REVISION`
- **Comentario**: Opcional
- **Ejemplo**: "Revisando documentación y líneas de investigación..."
- **Resultado**: 
  - Club pasa al tab "En Revisión"
  - Se registra en historial

#### 4. Aprobar Club
- **Botón**: ✅ "Aprobar" (verde)
- **URL**: `/registry/admin/clubes/<id>/aprobar/`
- **Cambio de estado**: `PENDIENTE/EN_REVISION` → `APROBADO`
- **Comentario**: **OBLIGATORIO**
- **Ejemplo**: "Club aprobado. Cumple con todos los requisitos establecidos."
- **Resultado**:
  - Club habilitado en el sistema
  - Institución puede ver el club en "Mis Clubes Aprobados"
  - Se registra fecha de aprobación

#### 5. Rechazar Club
- **Botón**: ❌ "Rechazar" (rojo)
- **URL**: `/registry/admin/clubes/<id>/rechazar/`
- **Cambio de estado**: `PENDIENTE/EN_REVISION` → `RECHAZADO`
- **Motivo**: **OBLIGATORIO**
- **Ejemplo**: "Líneas de investigación no están claramente definidas. Falta documento legal."
- **Resultado**:
  - Institución puede ver el motivo
  - Institución puede corregir y reenviar

---

## 🔔 Sistema de Notificaciones (Implementado en Historial)

Cada cambio de estado se registra en `HistorialClub` con:

```python
HistorialClub.objects.create(
    club=club,
    usuario=request.user,  # Quién hizo el cambio
    estado_anterior="pendiente",
    estado_nuevo="en_revision",
    observaciones="Comentario del revisor"
)
```

### Campos del Historial:
- `club`: Referencia al club
- `usuario`: Usuario que realizó la acción
- `estado_anterior`: Estado previo
- `estado_nuevo`: Nuevo estado
- `observaciones`: Comentario/motivo
- `fecha`: Timestamp automático

---

## 📊 Vistas Implementadas

### Vistas de Federación

| Vista | URL | Método | Descripción |
|-------|-----|--------|-------------|
| `revisar_clubes` | `/registry/admin/clubes/revisar/` | GET | Lista clubes pendientes y en revisión |
| `detalle_club` | `/registry/clubes/<id>/detalle/` | GET | Detalles completos del club |
| `tomar_en_revision_club` | `/registry/admin/clubes/<id>/tomar-revision/` | GET/POST | Toma club en revisión con comentario |
| `aprobar_club` | `/registry/admin/clubes/<id>/aprobar/` | GET/POST | Aprueba club con comentario obligatorio |
| `rechazar_club` | `/registry/admin/clubes/<id>/rechazar/` | GET/POST | Rechaza club con motivo obligatorio |

### Vistas de Institución

| Vista | URL | Método | Descripción |
|-------|-----|--------|-------------|
| `clubes_lista` | `/registry/clubes/` | GET | Lista clubes creados, aprobados y disponibles |
| `crear_club` | `/registry/clubes/crear/` | GET/POST | Crear nuevo club |
| `editar_club` | `/registry/clubes/<id>/editar/` | GET/POST | Editar club en borrador o rechazado |
| `enviar_club_revision` | `/registry/clubes/<id>/enviar-revision/` | GET/POST | Enviar club a revisión |

---

## 🎨 Templates Creados/Modificados

### Nuevos Templates

1. **`tomar_revision_club.html`**
   - Formulario para tomar club en revisión
   - Comentario opcional
   - Información del club

2. **`aprobar_club.html`**
   - Formulario de aprobación
   - Comentario obligatorio
   - Confirmación visual

3. **`rechazar_club.html`** (ya existía, mejorado)
   - Formulario de rechazo
   - Motivo obligatorio
   - Información del club

### Templates Modificados

1. **`revisar_clubes.html`**
   - Agregado botón "Revisar" (azul)
   - Botones: Ver Detalles, Revisar, Aprobar, Rechazar
   - Tabs: Pendientes y En Revisión

---

## 🔒 Permisos y Seguridad

### Acceso a Vistas

| Vista | Permisos Requeridos |
|-------|-------------------|
| `revisar_clubes` | `@staff_member_required` |
| `tomar_en_revision_club` | `@staff_member_required` |
| `aprobar_club` | `@staff_member_required` |
| `rechazar_club` | `@staff_member_required` |
| `detalle_club` | `@login_required` + validación por rol |

### Validaciones Implementadas

1. **Tomar en Revisión**: Solo clubes en `PENDIENTE`
2. **Aprobar**: Solo clubes en `PENDIENTE` o `EN_REVISION`
3. **Rechazar**: Cualquier estado excepto `APROBADO`
4. **Comentarios**: Obligatorios en aprobar/rechazar

---

## 📈 Ventajas del Flujo Implementado

✅ **Trazabilidad Completa**: Cada acción queda registrada con usuario, fecha y comentario

✅ **Comunicación Clara**: La institución sabe exactamente por qué fue aprobado/rechazado

✅ **Auditoría**: Historial completo de cambios de estado

✅ **Transparencia**: La institución puede ver el progreso de su solicitud

✅ **Flexibilidad**: Federación puede aprobar/rechazar directamente o tomar en revisión primero

✅ **Mejora Continua**: Comentarios detallados ayudan a las instituciones a mejorar

---

## 🔄 Ejemplo de Flujo Completo

### Caso 1: Aprobación Directa

```
1. Institución crea club → BORRADOR
2. Institución envía → PENDIENTE
3. Federación revisa detalles → (Ver Detalles)
4. Federación aprueba con comentario → APROBADO
   Comentario: "Club aprobado. Excelente propuesta."
5. Institución ve club en "Mis Clubes Aprobados"
```

### Caso 2: Con Revisión Intermedia

```
1. Institución crea club → BORRADOR
2. Institución envía → PENDIENTE
3. Federación toma en revisión → EN_REVISION
   Comentario: "Revisando documentación..."
4. Federación aprueba → APROBADO
   Comentario: "Aprobado tras verificar documentos."
```

### Caso 3: Rechazo y Corrección

```
1. Institución crea club → BORRADOR
2. Institución envía → PENDIENTE
3. Federación rechaza → RECHAZADO
   Motivo: "Falta documento legal y líneas no claras."
4. Institución corrige y reenvía → PENDIENTE
5. Federación aprueba → APROBADO
```

---

## 🎯 Próximos Pasos Sugeridos

1. **Sistema de Notificaciones Email**: Enviar correos cuando cambia el estado
2. **Dashboard de Métricas**: Tiempo promedio de revisión, tasa de aprobación
3. **Notificaciones en Tiempo Real**: WebSockets para notificaciones instantáneas
4. **Exportar Historial**: PDF con historial completo del club

---

**Fecha de Implementación**: 2024  
**Relacionado con**: `CLUBES_ANÁLISIS.md`, `CORRECCION_CONTEO_CLUBES.md`
