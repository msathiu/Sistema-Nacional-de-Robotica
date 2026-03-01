# 🔄 FLUJO DE TRABAJO: Sistema de Clubes

## 📊 Diagrama de Estados del Club

```
┌─────────────┐
│  BORRADOR   │ ◄─── Creación inicial (Institución)
└──────┬──────┘
       │ enviar_a_revision()
       ▼
┌─────────────┐
│  PENDIENTE  │ ◄─── Enviado a revisión (Institución)
└──────┬──────┘
       │ Federación revisa
       ▼
┌─────────────┐
│ EN_REVISION │ ◄─── En proceso de revisión (Federación)
└──────┬──────┘
       │
       ├─────────────┐
       │             │
       ▼             ▼
┌─────────────┐  ┌─────────────┐
│  APROBADO   │  │  RECHAZADO  │
│  (Público)  │  │ (Corregir)  │
└─────────────┘  └──────┬──────┘
                        │ editar()
                        ▼
                 ┌─────────────┐
                 │  BORRADOR   │ ◄─── Puede corregir y reenviar
                 └─────────────┘
```

---

## 👥 Flujo por Tipo de Usuario

### 🏢 INSTITUCIÓN (Usuario Institucional)

#### 1. Crear Club
```
┌──────────────────────────────────────────────────────────┐
│ 1. Institución accede a "Crear Club"                    │
│    URL: /registry/clubes/crear/                         │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 2. Completa formulario:                                  │
│    - Nombre del club                                     │
│    - Descripción                                         │
│    - Líneas de investigación (1-3)                      │
│    - Cupo máximo                                         │
│    - Documento legal                                     │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 3. Club creado en estado BORRADOR                        │
│    - Visible solo para la institución creadora          │
│    - Puede editar libremente                             │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 4. Institución revisa y envía a revisión                │
│    URL: /registry/clubes/{id}/enviar-revision/          │
│    Estado: BORRADOR → PENDIENTE                          │
└──────────────────────────────────────────────────────────┘
```

#### 2. Ver Mis Clubes
```
┌──────────────────────────────────────────────────────────┐
│ Institución accede a "Mis Clubes"                       │
│ URL: /registry/clubes/                                   │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ SECCIÓN 1: Mis Clubes Creados                           │
│ ┌────────────────────────────────────────────────────┐  │
│ │ Club A - BORRADOR      [Editar] [Enviar]          │  │
│ │ Club B - PENDIENTE     [En proceso...]            │  │
│ │ Club C - APROBADO      [✓ Activo]                 │  │
│ │ Club D - RECHAZADO     [Corregir]                 │  │
│ └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ SECCIÓN 2: Mis Clubes Aprobados                         │
│ ┌────────────────────────────────────────────────────┐  │
│ │ Club C - APROBADO                                  │  │
│ │ Cupos: 5/10 disponibles                            │  │
│ │ Fecha aprobación: 15/01/2024                       │  │
│ └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ SECCIÓN 3: Clubes Disponibles (Otras Instituciones)    │
│ ┌────────────────────────────────────────────────────┐  │
│ │ Club X - Institución Y                             │  │
│ │ Líneas: IA, Robótica                               │  │
│ │ Cupos: 3/15 disponibles    [Postular]             │  │
│ └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

#### 3. Postular a Club
```
┌──────────────────────────────────────────────────────────┐
│ 1. Institución ve club aprobado de otra institución     │
│    - Club debe estar APROBADO                            │
│    - Debe tener cupos disponibles                        │
│    - Estado vinculación: ABIERTO o INVITACIÓN           │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 2. Click en "Postular"                                   │
│    URL: /registry/clubes/{id}/postular/                 │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 3. Completa formulario de postulación:                  │
│    - Carta de intención                                  │
│    - Propuesta técnica                                   │
│    - Representante legal                                 │
│    - Tipo de línea (soporte/afines/vinculantes)        │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 4. Membresía creada en estado PENDIENTE                 │
│    - Coordinador del club revisa                         │
│    - Puede aprobar o rechazar                            │
└──────────────────────────────────────────────────────────┘
```

---

### 🏛️ FEDERACIÓN (Staff/Admin)

#### 1. Revisar Clubes Pendientes
```
┌──────────────────────────────────────────────────────────┐
│ 1. Federación accede a "Revisar Clubes"                │
│    URL: /registry/admin/clubes/revisar/                 │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 2. Ve lista de clubes PENDIENTES                        │
│ ┌────────────────────────────────────────────────────┐  │
│ │ Club A - Institución X                             │  │
│ │ Fecha solicitud: 10/01/2024                        │  │
│ │ [Ver Detalles] [Aprobar] [Rechazar]               │  │
│ └────────────────────────────────────────────────────┘  │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ├─────────────┐
                     │             │
                     ▼             ▼
┌─────────────────────────┐  ┌─────────────────────────┐
│ 3a. APROBAR             │  │ 3b. RECHAZAR            │
│ - Estado: APROBADO      │  │ - Estado: RECHAZADO     │
│ - Visible públicamente  │  │ - Agregar observaciones │
│ - Fecha aprobación      │  │ - Institución corrige   │
└─────────────────────────┘  └─────────────────────────┘
```

#### 2. Revisar Membresías
```
┌──────────────────────────────────────────────────────────┐
│ 1. Federación accede a "Revisar Membresías"            │
│    URL: /registry/admin/membresias/revisar/             │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 2. Ve lista de membresías PENDIENTES                    │
│ ┌────────────────────────────────────────────────────┐  │
│ │ Institución X → Club Y                             │  │
│ │ Tipo línea: Vinculantes                            │  │
│ │ [Ver Propuesta] [Aprobar] [Rechazar]              │  │
│ └────────────────────────────────────────────────────┘  │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ├─────────────┐
                     │             │
                     ▼             ▼
┌─────────────────────────┐  ┌─────────────────────────┐
│ 3a. APROBAR             │  │ 3b. RECHAZAR            │
│ - Estado: APROBADA      │  │ - Estado: RECHAZADA     │
│ - Cupos se reducen      │  │ - Agregar observaciones │
│ - Notificar institución │  │ - Notificar institución │
└─────────────────────────┘  └─────────────────────────┘
```

---

## 🔐 Matriz de Permisos

### Vista: clubes_lista
```
┌─────────────────┬──────────────┬──────────────┬──────────────┐
│ Usuario         │ Mis Clubes   │ Mis Aprobados│ Disponibles  │
│                 │ Creados      │              │              │
├─────────────────┼──────────────┼──────────────┼──────────────┤
│ Institucional   │ ✅ Todos     │ ✅ Aprobados │ ✅ Otros     │
│                 │ sus estados  │ propios      │ aprobados    │
├─────────────────┼──────────────┼──────────────┼──────────────┤
│ Federación      │ ✅ TODOS     │ ✅ TODOS     │ ✅ TODOS     │
│                 │ del sistema  │ del sistema  │ del sistema  │
├─────────────────┼──────────────┼──────────────┼──────────────┤
│ Participante    │ ❌ No accede │ ❌ No accede │ ❌ No accede │
└─────────────────┴──────────────┴──────────────┴──────────────┘
```

### Vista: crear_club
```
┌─────────────────┬──────────────┐
│ Usuario         │ Puede Crear  │
├─────────────────┼──────────────┤
│ Institucional   │ ✅ Sí        │
├─────────────────┼──────────────┤
│ Federación      │ ✅ Sí        │
├─────────────────┼──────────────┤
│ Participante    │ ❌ No        │
└─────────────────┴──────────────┘
```

### Vista: editar_club
```
┌─────────────────┬──────────────┬──────────────────────┐
│ Usuario         │ Puede Editar │ Condiciones          │
├─────────────────┼──────────────┼──────────────────────┤
│ Institucional   │ ✅ Sí        │ - Solo sus clubes    │
│                 │              │ - Solo BORRADOR o    │
│                 │              │   RECHAZADO          │
├─────────────────┼──────────────┼──────────────────────┤
│ Federación      │ ✅ Sí        │ - Todos los clubes   │
│                 │              │ - Todos los estados  │
├─────────────────┼──────────────┼──────────────────────┤
│ Participante    │ ❌ No        │ -                    │
└─────────────────┴──────────────┴──────────────────────┘
```

### Vista: aprobar_club / rechazar_club
```
┌─────────────────┬──────────────┐
│ Usuario         │ Puede        │
├─────────────────┼──────────────┤
│ Institucional   │ ❌ No        │
├─────────────────┼──────────────┤
│ Federación      │ ✅ Sí        │
├─────────────────┼──────────────┤
│ Participante    │ ❌ No        │
└─────────────────┴──────────────┘
```

---

## 📊 Flujo de Datos

### Creación de Club
```
┌─────────────┐
│ Formulario  │
│ HTML        │
└──────┬──────┘
       │ POST
       ▼
┌─────────────┐
│ Vista       │
│ crear_club  │
└──────┬──────┘
       │ save()
       ▼
┌─────────────┐
│ Modelo      │
│ Club        │
│ status=     │
│ 'borrador'  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Base de     │
│ Datos       │
└─────────────┘
```

### Envío a Revisión
```
┌─────────────┐
│ Botón       │
│ "Enviar"    │
└──────┬──────┘
       │ POST
       ▼
┌─────────────┐
│ Vista       │
│ enviar_club │
│ _revision   │
└──────┬──────┘
       │ update
       ▼
┌─────────────┐
│ Club.status │
│ = 'pendiente'│
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Notificación│
│ a Federación│
└─────────────┘
```

### Aprobación
```
┌─────────────┐
│ Federación  │
│ revisa      │
└──────┬──────┘
       │ POST
       ▼
┌─────────────┐
│ Vista       │
│ aprobar_club│
└──────┬──────┘
       │ update
       ▼
┌─────────────┐
│ Club.status │
│ = 'aprobado'│
│ fecha_aprob │
│ = now()     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Notificación│
│ a Institución│
└─────────────┘
```

---

## 🎨 Interfaz de Usuario

### Dashboard Institucional
```
┌────────────────────────────────────────────────────────┐
│ Dashboard Institucional                                │
├────────────────────────────────────────────────────────┤
│                                                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ Mis      │  │ Clubes   │  │ Grupos   │           │
│  │ Clubes   │  │ Aprobados│  │          │           │
│  │    5     │  │    3     │  │    12    │           │
│  └──────────┘  └──────────┘  └──────────┘           │
│                                                        │
│  ┌────────────────────────────────────────────────┐  │
│  │ Mis Clubes Recientes                           │  │
│  ├────────────────────────────────────────────────┤  │
│  │ • Club A - BORRADOR      [Editar] [Enviar]    │  │
│  │ • Club B - PENDIENTE     [En revisión...]     │  │
│  │ • Club C - APROBADO      [✓ Activo]           │  │
│  └────────────────────────────────────────────────┘  │
│                                                        │
│  [Ver Todos los Clubes]  [Crear Nuevo Club]          │
└────────────────────────────────────────────────────────┘
```

### Lista de Clubes
```
┌────────────────────────────────────────────────────────┐
│ Gestión de Clubes                    [+ Crear Club]   │
├────────────────────────────────────────────────────────┤
│                                                        │
│ ┌────────────────────────────────────────────────┐   │
│ │ 📁 Mis Clubes Creados (5)                      │   │
│ ├────────────────────────────────────────────────┤   │
│ │ Nombre      Estado      Cupos    Acciones      │   │
│ │ Club A      BORRADOR    10/10    [Editar]      │   │
│ │ Club B      PENDIENTE   8/10     [...]         │   │
│ │ Club C      APROBADO    5/10     [✓]           │   │
│ └────────────────────────────────────────────────┘   │
│                                                        │
│ ┌────────────────────────────────────────────────┐   │
│ │ ✅ Mis Clubes Aprobados (3)                    │   │
│ ├────────────────────────────────────────────────┤   │
│ │ [Card Club C]  [Card Club E]  [Card Club F]   │   │
│ └────────────────────────────────────────────────┘   │
│                                                        │
│ ┌────────────────────────────────────────────────┐   │
│ │ 🌐 Clubes Disponibles (12)                     │   │
│ ├────────────────────────────────────────────────┤   │
│ │ [Card Club X]  [Card Club Y]  [Card Club Z]   │   │
│ │ [Postular]     [Postular]     [Postular]      │   │
│ └────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────┘
```

---

## 🔄 Ciclo de Vida Completo

```
DÍA 1: Institución A crea Club
┌─────────────────────────────────────────────────────────┐
│ 09:00 - Institución A crea "Club de Robótica"          │
│         Estado: BORRADOR                                 │
│ 10:00 - Completa información y envía a revisión         │
│         Estado: BORRADOR → PENDIENTE                     │
└─────────────────────────────────────────────────────────┘

DÍA 2: Federación revisa
┌─────────────────────────────────────────────────────────┐
│ 14:00 - Federación recibe notificación                  │
│ 15:00 - Revisa documentación                            │
│         Estado: PENDIENTE → EN_REVISION                  │
│ 16:00 - Aprueba el club                                 │
│         Estado: EN_REVISION → APROBADO                   │
└─────────────────────────────────────────────────────────┘

DÍA 3: Club visible públicamente
┌─────────────────────────────────────────────────────────┐
│ 09:00 - Institución A recibe notificación de aprobación│
│ 10:00 - Club aparece en "Clubes Disponibles" para      │
│         otras instituciones                              │
│ 11:00 - Institución B ve el club y postula             │
│         Membresía creada: PENDIENTE                      │
└─────────────────────────────────────────────────────────┘

DÍA 4: Gestión de membresías
┌─────────────────────────────────────────────────────────┐
│ 09:00 - Coordinador del Club revisa postulación        │
│ 10:00 - Aprueba membresía de Institución B             │
│         Membresía: PENDIENTE → APROBADA                 │
│ 10:01 - Cupos se actualizan: 10/10 → 9/10              │
└─────────────────────────────────────────────────────────┘
```

---

## 📝 Notas Importantes

1. **Estados Inmutables**: Una vez APROBADO, un club no puede volver a BORRADOR
2. **Cupos Automáticos**: Al aprobar membresía, los cupos se reducen automáticamente
3. **Cierre Automático**: Si cupos = 0, estado_vinculación cambia a CERRADO
4. **Notificaciones**: Cada cambio de estado debe notificar a la institución
5. **Auditoría**: Todos los cambios de estado deben quedar registrados

---

Este flujo garantiza:
- ✅ Control de calidad (revisión por federación)
- ✅ Transparencia (estados claros)
- ✅ Seguridad (permisos estrictos)
- ✅ Escalabilidad (sistema robusto)
