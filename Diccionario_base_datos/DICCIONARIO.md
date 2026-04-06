# Diccionario de Datos — RNR-PRO: Sistema Nacional de Robótica

**Versión:** 1.0  
**Fecha:** 2026-04-03  
**Framework:** Django 5.0 / Python 3.12  
**Base de Datos:** SQLite3 / PostgreSQL  

---

## Índice de Tablas

1. [Estado](#1-estado)
2. [Municipio](#2-municipio)
3. [Parroquia](#3-parroquia)
4. [Dependencia](#4-dependencia)
5. [Institucion](#5-institucion)
6. [UserProfile](#6-userprofile)
7. [Participante](#7-participante)
8. [ParticipanteInstitucion](#8-participanteinstitucion)
9. [ParticipanteGrupo](#9-participantegrupo)
10. [AsistenciaEvento](#10-asistenciaevento)
11. [Tutor](#11-tutor)
12. [TutorInstitucion](#12-tutorinstitucion)
13. [LineaInvestigacion](#13-lineainvestigacion)
14. [Club](#14-club)
15. [MembresiaClu](#15-membresiaclu)
16. [ClubLineaInvestigacion](#16-clublineainvestigacion)
17. [ClubTutor](#17-clubtutor)
18. [HistorialClub](#18-historialclub)
19. [ComentarioClub](#19-comentarioclub)
20. [CalificacionClub](#20-calificacionclub)
21. [SolicitudEliminacionClub](#21-solicitudeliminacionclub)
22. [Evento](#22-evento)
23. [Inscripcion](#23-inscripcion)
24. [IntegranteEquipo](#24-integranteequipo)
25. [InscripcionGrupoEvento](#25-inscripciongrupoevento)
26. [ClubEvento](#26-clubevento)
27. [Grupo](#27-grupo)
28. [Notificacion](#28-notificacion)

---

## Catálogos de Valores (Choices)

### Nacionalidad
| Código | Descripción |
|--------|-------------|
| `V` | Venezolano |
| `E` | Extranjero |

### Sexo
| Código | Descripción |
|--------|-------------|
| `M` | Masculino |
| `F` | Femenino |
| `O` | Otro |

### Código de Área Telefónico
`0424`, `0414`, `0422`, `0412`, `0426`, `0416`, `0212`

### Grado Escolar
| Código | Descripción |
|--------|-------------|
| `NO` | No estudia |
| `P1` | Preescolar Nivel 1 |
| `P2` | Preescolar Nivel 2 |
| `PR1`–`PR6` | 1er–6to Grado Primaria |
| `L1`–`L6` | 1er–6to Año Liceo |
| `U` | Estudios Universitarios |
| `OTRO` | Otro/No especificado |

---

## 1. Estado

**Tabla:** `registry_estado`  
**Descripción:** Catálogo de estados (entidades federales) de Venezuela.

| Campo | Tipo | Nulo | Único | Índice | Descripción |
|-------|------|------|-------|--------|-------------|
| `id` | Integer (PK) | No | Sí | Sí | Identificador automático |
| `nombre` | CharField(100) | No | Sí | Sí | Nombre del estado |
| `codigo` | CharField(10) | No | Sí | Sí | Código del estado |

**Índices:** `idx_estado_nombre`, `idx_estado_codigo`

---

## 2. Municipio

**Tabla:** `registry_municipio`  
**Descripción:** Catálogo de municipios, relacionados con su estado.

| Campo | Tipo | Nulo | Único | Índice | Descripción |
|-------|------|------|-------|--------|-------------|
| `id` | Integer (PK) | No | Sí | Sí | Identificador automático |
| `estado_id` | FK → Estado | No | No | Sí | Estado al que pertenece |
| `nombre` | CharField(100) | No | No | Sí | Nombre del municipio |

**Restricciones:** `unique_together = [estado, nombre]`  
**Índices:** `idx_mun_estado_nombre`

---

## 3. Parroquia

**Tabla:** `registry_parroquia`  
**Descripción:** Catálogo de parroquias, relacionadas con su municipio.

| Campo | Tipo | Nulo | Único | Índice | Descripción |
|-------|------|------|-------|--------|-------------|
| `id` | Integer (PK) | No | Sí | Sí | Identificador automático |
| `municipio_id` | FK → Municipio | No | No | Sí | Municipio al que pertenece |
| `nombre` | CharField(100) | No | No | Sí | Nombre de la parroquia |

**Restricciones:** `unique_together = [municipio, nombre]`  
**Índices:** `idx_parr_mun_nombre`

---

## 4. Dependencia

**Tabla:** `registry_dependencia`  
**Descripción:** Catálogo de dependencias institucionales (ej. MPPE, MINCYT).

| Campo | Tipo | Nulo | Único | Índice | Descripción |
|-------|------|------|-------|--------|-------------|
| `id` | Integer (PK) | No | Sí | Sí | Identificador automático |
| `nombre` | CharField(255) | No | Sí | Sí | Nombre de la dependencia |
| `activa` | BooleanField | No | No | Sí | Indica si está activa (default: True) |

**Índices:** `idx_dep_activa_nombre`

---

## 5. Institucion

**Tabla:** `registry_institucion`  
**Descripción:** Entidad central del sistema. Representa instituciones educativas, organizaciones, clubes o particulares registrados en el RNR.

| Campo | Tipo | Nulo | Único | Índice | Descripción |
|-------|------|------|-------|--------|-------------|
| `id` | Integer (PK) | No | Sí | Sí | Identificador automático |
| `usuario_id` | FK → User (OneToOne) | Sí | Sí | No | Usuario Django asociado |
| `nombre` | CharField(255) | No | No | No | Nombre de la institución |
| `rif` | CharField(20) | Sí | No | No | RIF de la institución |
| `particular_nombres` | CharField(100) | Sí | No | No | Nombres (solo para particulares) |
| `particular_apellidos` | CharField(100) | Sí | No | No | Apellidos (solo para particulares) |
| `particular_nacionalidad` | CharField(1) | Sí | No | No | Nacionalidad del particular (V/E) |
| `particular_cedula` | CharField(10) | Sí | No | Sí | Cédula del particular (solo números) |
| `tipo_institucion` | CharField(20) | No | No | Sí | Tipo: `educativa`, `publica`, `privada`, `otra`, `particular` |
| `naturaleza` | CharField(20) | Sí | No | No | Naturaleza: `publica`, `privada` |
| `subcategoria` | CharField(120) | Sí | No | No | Subcategoría institucional |
| `tipo_federado` | CharField(20) | No | No | No | Tipo federado: `institucion`, `organizacion`, `particular` |
| `federado` | BooleanField | No | No | Sí | Indica si está federado (default: False) |
| `categoria` | CharField(50) | Sí | No | No | Categoría adicional |
| `institucion_procedencia` | CharField(120) | Sí | No | No | Institución de procedencia |
| `codigo_mppe` | CharField(30) | Sí | No | No | Código MPPE (instituciones educativas) |
| `estado_id` | FK → Estado | No | No | Sí | Estado de ubicación |
| `municipio_id` | FK → Municipio | No | No | Sí | Municipio de ubicación |
| `parroquia_id` | FK → Parroquia | No | No | No | Parroquia de ubicación |
| `codigo` | CharField(35) | No | Sí | Sí | Código RNR único (auto-generado) |
| `direccion` | TextField | Sí | No | No | Dirección física |
| `telefono_codigo` | CharField(4) | Sí | No | No | Código de área del teléfono |
| `telefono_numero` | CharField(7) | Sí | No | No | Número de teléfono (7 dígitos) |
| `telefono` | CharField(20) | Sí | No | No | Teléfono completo (campo legado) |
| `email` | EmailField | No | No | Sí | Correo electrónico |
| `fecha_registro` | DateTimeField | No | No | No | Fecha de registro (auto) |
| `estatus` | CharField(20) | No | No | Sí | Estado: `pendiente`, `aprobado`, `rechazado` |
| `activa` | BooleanField | No | No | Sí | Indica si la institución está activa |
| `eliminado` | BooleanField | No | No | No | Soft delete |
| `fecha_eliminacion` | DateTimeField | Sí | No | No | Fecha de eliminación lógica |
| `dependencia` | CharField(255) | Sí | No | No | Nombre de dependencia (texto libre) |
| `dependencia_rel_id` | FK → Dependencia | Sí | No | No | Dependencia relacionada (catálogo) |

**Índices:** `idx_inst_codigo`, `idx_inst_email`, `idx_inst_estatus`, `idx_inst_activa`, `idx_inst_ubicacion`, `idx_inst_tipo`, `idx_inst_federado`, `idx_inst_part_cedula`

---

## 6. UserProfile

**Tabla:** `users_userprofile`  
**Descripción:** Perfil extendido del usuario Django. Define el rol y la institución asociada.

| Campo | Tipo | Nulo | Único | Índice | Descripción |
|-------|------|------|-------|--------|-------------|
| `id` | Integer (PK) | No | Sí | Sí | Identificador automático |
| `user_id` | FK → User (OneToOne) | No | Sí | No | Usuario Django |
| `user_type` | CharField(25) | No | No | No | Rol: `participante`, `institucional`, `fed_central`, `fed_regional`, `tecnologico`, `superuser` |
| `institution_id` | FK → Institucion | Sí | No | No | Institución asociada |
| `phone` | CharField(20) | Sí | No | No | Teléfono del usuario |
| `cedula` | CharField(20) | Sí | No | No | Cédula del usuario |
| `estado_id` | FK → Estado | Sí | No | No | Estado (para territorialidad regional) |
| `municipio_id` | FK → Municipio | Sí | No | No | Municipio |
| `parroquia_id` | FK → Parroquia | Sí | No | No | Parroquia |
| `ubicacion` | TextField | Sí | No | No | Descripción de ubicación |
| `created_at` | DateTimeField | No | No | No | Fecha de creación (auto) |
| `updated_at` | DateTimeField | No | No | No | Fecha de actualización (auto) |

**Roles de usuario:**
| Código | Descripción |
|--------|-------------|
| `participante` | Usuario participante |
| `institucional` | Usuario de institución (sedes/matriz) |
| `fed_central` | Federación Central — Ente Rector (aprueba) |
| `fed_regional` | Federación Regional (solo ve su estado) |
| `tecnologico` | Administrador Tecnológico (soporte técnico) |
| `superuser` | Superusuario con acceso total |

---

## 7. Participante

**Tabla:** `registry_participante`  
**Descripción:** Datos personales únicos de cada participante del sistema. Un participante puede estar vinculado a múltiples instituciones.

| Campo | Tipo | Nulo | Único | Índice | Descripción |
|-------|------|------|-------|--------|-------------|
| `id` | UUIDField (PK, uuid7) | No | Sí | Sí | Identificador único universal |
| `nacionalidad` | CharField(1) | No | No | No | Nacionalidad: `V`, `E` |
| `cedula` | CharField(20) | Sí | Sí | Sí | Cédula de identidad (solo números) |
| `cedula_escolar` | CharField(20) | Sí | Sí | Sí | Cédula escolar (solo números, menores de 10 años) |
| `nombres` | CharField(100) | No | No | Sí | Nombres del participante |
| `apellidos` | CharField(100) | No | No | Sí | Apellidos del participante |
| `fecha_nacimiento` | DateField | No | No | Sí | Fecha de nacimiento |
| `sexo` | CharField(1) | No | No | No | Sexo: `M`, `F`, `O` |
| `email` | EmailField | No | No | Sí | Correo electrónico |
| `estado_id` | FK → Estado | No | No | No | Estado de residencia |
| `municipio_id` | FK → Municipio | No | No | No | Municipio de residencia |
| `parroquia_id` | FK → Parroquia | Sí | No | No | Parroquia de residencia |
| `direccion` | TextField | No | No | No | Dirección de residencia |
| `codigo_area` | CharField(4) | No | No | No | Código de área del teléfono |
| `numero_telefono` | CharField(7) | No | No | No | Número de teléfono (7 dígitos) |
| `grado_escolar` | CharField(4) | No | No | No | Nivel educativo (ver catálogo Grado Escolar) |
| `titulo_universitario` | CharField(200) | Sí | No | No | Título universitario (si aplica) |
| `campo1` | TextField | Sí | No | No | Campo adicional para grado/nivel libre |
| `nombre_representante` | CharField(200) | Sí | No | No | Nombre del representante (obligatorio si < 18 años) |
| `nacionalidad_representante` | CharField(1) | No | No | No | Nacionalidad del representante: `V`, `E` |
| `cedula_representante` | CharField(10) | Sí | No | No | Cédula del representante (7–10 dígitos) |
| `codigo_area_representante` | CharField(4) | Sí | No | No | Código de área del representante |
| `numero_telefono_representante` | CharField(7) | Sí | No | No | Teléfono del representante (7 dígitos) |
| `email_representante` | EmailField | Sí | No | No | Correo del representante |
| `condicion_tea` | BooleanField | No | No | No | Condición TEA (default: False) |
| `creado_por_federacion` | BooleanField | No | No | No | Registrado por la federación (default: False) |
| `fecha_registro` | DateTimeField | No | No | No | Fecha de registro (auto) |
| `user_id` | FK → User (OneToOne) | Sí | Sí | No | Usuario Django asociado |

**Restricciones:**  
- `unique_participante_datos_personales`: unicidad por `nombres + apellidos + fecha_nacimiento`  
- Edad mínima: 4 años  
- Representante obligatorio para menores de 18 años  

**Índices:** `idx_part_cedula`, `idx_part_cedula_esc`, `idx_part_email`, `idx_part_nombre`, `idx_part_nombre_fn`

---

## 8. ParticipanteInstitucion

**Tabla:** `registry_participanteinstitucion`  
**Descripción:** Tabla de vinculación entre participantes e instituciones. Permite que un participante esté activo en múltiples instituciones con estados independientes.

| Campo | Tipo | Nulo | Único | Índice | Descripción |
|-------|------|------|-------|--------|-------------|
| `id` | UUIDField (PK, uuid7) | No | Sí | Sí | Identificador único |
| `participante_id` | FK → Participante | No | No | Sí | Participante vinculado |
| `institucion_id` | FK → Institucion | Sí | No | Sí | Institución vinculada |
| `estado_id` | FK → Estado | Sí | No | No | Estado (para vinculación regional) |
| `tipo_vinculacion` | CharField(20) | No | No | No | Tipo: `institucional`, `regional`, `central` |
| `grupo_actual_id` | FK → Grupo | Sí | No | Sí | Grupo actual del participante |
| `status` | CharField(20) | No | No | Sí | Estado: `activo`, `inactivo`, `suspendido`, `egresado` |
| `fecha_vinculacion` | DateTimeField | No | No | Sí | Fecha de vinculación (auto) |
| `fecha_desvinculacion` | DateTimeField | Sí | No | No | Fecha de desvinculación |
| `registrado_por_id` | FK → User | Sí | No | No | Usuario que registró la vinculación |
| `observaciones` | TextField | Sí | No | No | Observaciones adicionales |

**Restricciones únicas:**
- `unique_participante_institucion`: un participante por institución (tipo `institucional`)
- `unique_participante_regional`: un participante por estado (tipo `regional`)
- `unique_participante_central`: un solo registro central por participante

**Índices:** `idx_partinst_part_st`, `idx_partinst_inst_st`, `idx_partinst_st_fecha`, `idx_partinst_grupo`

---

## 9. ParticipanteGrupo

**Tabla:** `registry_participantegrupo`  
**Descripción:** Historial de pertenencia de participantes a grupos.

| Campo | Tipo | Nulo | Único | Índice | Descripción |
|-------|------|------|-------|--------|-------------|
| `id` | UUIDField (PK, uuid7) | No | Sí | Sí | Identificador único |
| `participante_id` | FK → Participante | No | No | Sí | Participante |
| `grupo_id` | FK → Grupo | No | No | Sí | Grupo |
| `fecha_ingreso` | DateTimeField | No | No | No | Fecha de ingreso (auto) |
| `fecha_salida` | DateTimeField | Sí | No | No | Fecha de salida del grupo |
| `activo` | BooleanField | No | No | Sí | Indica si la membresía está activa |

**Restricciones:** `unique_together = [participante, grupo]`  
**Índices:** `idx_partgrp_part_act`, `idx_partgrp_grp_act`

---

## 10. AsistenciaEvento

**Tabla:** `registry_asistenciaevento`  
**Descripción:** Registro de asistencia de participantes a eventos.

| Campo | Tipo | Nulo | Único | Índice | Descripción |
|-------|------|------|-------|--------|-------------|
| `id` | Integer (PK) | No | Sí | Sí | Identificador automático |
| `evento_id` | FK → Evento | No | No | No | Evento |
| `participante_id` | FK → Participante | No | No | No | Participante |
| `grupo_id` | FK → Grupo | Sí | No | No | Grupo del participante |
| `asistencia` | CharField(12) | No | No | Sí | Estado: `asistio`, `ausente`, `pendiente`, `justificado` |
| `observacion` | TextField | Sí | No | No | Observación adicional |
| `fecha_asistencia` | DateTimeField | Sí | No | No | Fecha/hora en que se marcó la asistencia |
| `fecha_creacion` | DateTimeField | No | No | No | Fecha de creación del registro (auto) |

**Restricciones:** `unique_together = [evento, participante]`

---

## 11. Tutor

**Tabla:** `registry_tutor`  
**Descripción:** Tutores o responsables de grupos de robótica. Pueden estar vinculados a múltiples instituciones.

| Campo | Tipo | Nulo | Único | Índice | Descripción |
|-------|------|------|-------|--------|-------------|
| `id` | UUIDField (PK, uuid7) | No | Sí | Sí | Identificador único |
| `nacionalidad` | CharField(1) | No | No | No | Nacionalidad: `V`, `E` |
| `nombres` | CharField(100) | No | No | No | Nombres del tutor |
| `apellidos` | CharField(100) | No | No | No | Apellidos del tutor |
| `sexo` | CharField(1) | No | No | No | Sexo: `M`, `F`, `O` |
| `cedula` | CharField(12) | No | No | Sí | Cédula (solo números) |
| `telefono_codigo` | CharField(4) | Sí | No | No | Código de área del teléfono |
| `telefono` | CharField(7) | Sí | No | No | Número de teléfono (7 dígitos) |
| `email` | EmailField | No | No | No | Correo electrónico |
| `profesion` | CharField(100) | Sí | No | No | Profesión |
| `experiencia` | TextField | Sí | No | No | Experiencia en robótica |
| `creado_por_federacion` | BooleanField | No | No | No | Registrado por la federación (default: False) |
| `created_at` | DateTimeField | No | No | No | Fecha de creación (auto) |

**Índices:** `idx_tutor_cedula`

---

## 12. TutorInstitucion

**Tabla:** `registry_tutorinstitucion`  
**Descripción:** Vinculación entre tutores e instituciones con rol y estado independiente por institución.

| Campo | Tipo | Nulo | Único | Índice | Descripción |
|-------|------|------|-------|--------|-------------|
| `id` | UUIDField (PK, uuid7) | No | Sí | Sí | Identificador único |
| `tutor_id` | FK → Tutor | No | No | Sí | Tutor vinculado |
| `institucion_id` | FK → Institucion | Sí | No | Sí | Institución vinculada |
| `estado_id` | FK → Estado | Sí | No | No | Estado (para vinculación regional) |
| `tipo_vinculacion` | CharField(20) | No | No | No | Tipo: `institucional`, `regional`, `central` |
| `rol` | CharField(20) | No | No | No | Rol: `asistente`, `entrenador`, `instructor`, `coordinador`, `delegado`, `representante`, `colaborador` |
| `status` | CharField(20) | No | No | Sí | Estado: `activo`, `inactivo`, `suspendido` |
| `fecha_vinculacion` | DateTimeField | No | No | Sí | Fecha de vinculación (auto) |
| `fecha_desvinculacion` | DateTimeField | Sí | No | No | Fecha de desvinculación |
| `observaciones` | TextField | Sí | No | No | Observaciones |

**Restricciones únicas:**
- `unique_tutor_institucion`: un tutor por institución (tipo `institucional`)
- `unique_tutor_regional`: un tutor por estado (tipo `regional`)
- `unique_tutor_central`: un solo registro central por tutor

**Índices:** `idx_tutinst_tutor_st`, `idx_tutinst_inst_st`, `idx_tutinst_st_fecha`

---

## 13. LineaInvestigacion

**Tabla:** `registry_lineainvestigacion`  
**Descripción:** Catálogo de líneas de investigación gestionado por el Ente Rector.

| Campo | Tipo | Nulo | Único | Índice | Descripción |
|-------|------|------|-------|--------|-------------|
| `id` | Integer (PK) | No | Sí | Sí | Identificador automático |
| `codigo` | CharField(50) | No | Sí | Sí | Código único de la línea |
| `nombre` | CharField(200) | No | No | No | Nombre de la línea |
| `descripcion` | TextField | Sí | No | No | Descripción detallada |
| `activa` | BooleanField | No | No | Sí | Indica si está activa (default: True) |
| `orden` | IntegerField | No | No | Sí | Orden de visualización (default: 0) |
| `fecha_creacion` | DateTimeField | No | No | No | Fecha de creación (auto) |
| `fecha_actualizacion` | DateTimeField | No | No | No | Fecha de actualización (auto) |

**Índices:** `idx_linea_activa_orden`

---

## 14. Club

**Tabla:** `registry_club`  
**Descripción:** Clubes de robótica que agrupan múltiples instituciones. Requieren aprobación de la federación.

| Campo | Tipo | Nulo | Único | Índice | Descripción |
|-------|------|------|-------|--------|-------------|
| `id` | Integer (PK) | No | Sí | Sí | Identificador automático |
| `nombre` | CharField(200) | No | No | Sí | Nombre del club |
| `logo` | ImageField | Sí | No | No | Logo del club (upload: `clubes/logos/`) |
| `siglas` | CharField(10) | Sí | No | No | Siglas del club |
| `descripcion` | TextField | No | No | No | Descripción del club |
| `ubicacion` | CharField(255) | No | No | No | Ubicación del club |
| `fecha_fundacion` | DateField | Sí | No | No | Fecha de fundación |
| `institucion_creadora_id` | FK → Institucion | Sí | No | No | Institución que creó el club |
| `tipo_creador` | CharField(20) | No | No | No | Tipo de creador: `institucion`, `fed_central`, `fed_regional` |
| `coordinador_id` | FK → User | Sí | No | No | Coordinador del club |
| `documento_legal` | CharField(255) | Sí | No | No | Documento legal / aval institucional |
| `estado_vinculacion` | CharField(20) | No | No | No | Estado de vinculación: `abierto`, `cerrado`, `invitacion` |
| `cupo_maximo` | IntegerField | No | No | No | Cupo máximo de instituciones (default: 10) |
| `requisitos` | TextField | Sí | No | No | Requisitos para unirse |
| `status` | CharField(20) | No | No | Sí | Estado: `borrador`, `pendiente`, `en_revision`, `aprobado`, `rechazado` |
| `fecha_creacion` | DateTimeField | No | No | No | Fecha de creación (default: now) |
| `fecha_aprobacion` | DateTimeField | Sí | No | No | Fecha de aprobación |
| `activo` | BooleanField | No | No | Sí | Indica si está activo (default: True) |
| `eliminado` | BooleanField | No | No | Sí | Soft delete (default: False) |
| `fecha_eliminacion` | DateTimeField | Sí | No | No | Fecha de eliminación lógica |
| `motivo_eliminacion` | TextField | Sí | No | No | Motivo de eliminación |
| `eliminado_por_id` | FK → User | Sí | No | No | Usuario que eliminó el club |

**Índices:** `idx_club_activo_status`, `idx_club_status_nombre`

---

## 15. MembresiaClu

**Tabla:** `registry_membresiaclu`  
**Descripción:** Solicitudes y membresías de instituciones a clubes. Flujo de aprobación en dos etapas: fundadora + ente rector.

| Campo | Tipo | Nulo | Único | Índice | Descripción |
|-------|------|------|-------|--------|-------------|
| `id` | Integer (PK) | No | Sí | Sí | Identificador automático |
| `club_id` | FK → Club | No | No | Sí | Club al que se solicita membresía |
| `institucion_id` | FK → Institucion | No | No | No | Institución solicitante |
| `carta_intencion` | TextField | No | No | No | Carta de intención |
| `propuesta_tecnica` | TextField | No | No | No | Propuesta técnica |
| `representante_legal` | CharField(200) | No | No | No | Nombre del representante legal |
| `representante_tutor_id` | FK → Tutor | Sí | No | No | Tutor representante legal |
| `tipo_linea` | CharField(20) | No | No | No | Tipo de línea: `soporte`, `afines`, `vinculantes` |
| `estado` | CharField(25) | No | No | Sí | Estado: `pendiente_filtro`, `visto_bueno_fundadora`, `miembro_activo`, `rechazada` |
| `fecha_solicitud` | DateTimeField | No | No | No | Fecha de solicitud (auto) |
| `fecha_respuesta` | DateTimeField | Sí | No | No | Fecha de respuesta |
| `observaciones` | TextField | Sí | No | No | Observaciones generales |
| `visto_bueno_fundadora` | BooleanField | No | No | No | Visto bueno de la institución fundadora |
| `visto_bueno_fundadora_por_id` | FK → User | Sí | No | No | Usuario que dio el visto bueno |
| `visto_bueno_fundadora_fecha` | DateTimeField | Sí | No | No | Fecha del visto bueno |
| `observaciones_fundadora` | TextField | Sí | No | No | Observaciones de la fundadora |
| `aprobacion_ente_rector` | BooleanField | No | No | No | Aprobación del ente rector |
| `aprobacion_ente_rector_por_id` | FK → User | Sí | No | No | Usuario del ente rector que aprobó |
| `aprobacion_ente_rector_fecha` | DateTimeField | Sí | No | No | Fecha de aprobación del ente rector |
| `observaciones_rector` | TextField | Sí | No | No | Observaciones del ente rector |

**Índices:** `idx_memb_club_inst_active` (parcial: estados pendientes)

---

## 16. ClubLineaInvestigacion

**Tabla:** `registry_clublineainvestigacion`  
**Descripción:** Relación entre clubes y líneas de investigación con tipo y orden.

| Campo | Tipo | Nulo | Único | Índice | Descripción |
|-------|------|------|-------|--------|-------------|
| `id` | Integer (PK) | No | Sí | Sí | Identificador automático |
| `club_id` | FK → Club | No | No | Sí | Club |
| `linea_id` | FK → LineaInvestigacion | No | No | No | Línea de investigación |
| `tipo_linea` | CharField(20) | No | No | No | Tipo: `principal`, `soporte`, `afines` |
| `orden` | IntegerField | No | No | Sí | Orden de visualización (default: 0) |
| `fecha_vinculacion` | DateTimeField | No | No | No | Fecha de vinculación (auto) |

**Restricciones:** `unique_together = [club, linea]`  
**Índices:** `idx_clublinea_club_orden`

---

## 17. ClubTutor

**Tabla:** `registry_clubtutor`  
**Descripción:** Asignación de tutores a clubes con rol específico.

| Campo | Tipo | Nulo | Único | Índice | Descripción |
|-------|------|------|-------|--------|-------------|
| `id` | Integer (PK) | No | Sí | Sí | Identificador automático |
| `club_id` | FK → Club | No | No | No | Club |
| `tutor_id` | FK → Tutor | No | No | No | Tutor |
| `rol` | CharField(20) | No | No | No | Rol: `responsable`, `coordinador`, `entrenador`, `instructor`, `colaborador`, `representante`, `director`, `delegado`, `asistente`, `logistico` |
| `status` | CharField(20) | No | No | No | Estado: `activo`, `inactivo` |
| `fecha_asignacion` | DateTimeField | No | No | No | Fecha de asignación (auto) |

**Restricciones:** `unique_together = [club, tutor]`

---

## 18. HistorialClub

**Tabla:** `registry_historialclub`  
**Descripción:** Registro de cambios de estado de los clubes para trazabilidad.

| Campo | Tipo | Nulo | Único | Índice | Descripción |
|-------|------|------|-------|--------|-------------|
| `id` | Integer (PK) | No | Sí | Sí | Identificador automático |
| `club_id` | FK → Club | No | No | Sí | Club |
| `usuario_id` | FK → User | Sí | No | No | Usuario que realizó el cambio |
| `estado_anterior` | CharField(20) | No | No | No | Estado anterior del club |
| `estado_nuevo` | CharField(20) | No | No | No | Nuevo estado del club |
| `observaciones` | TextField | Sí | No | No | Observaciones del cambio |
| `fecha` | DateTimeField | No | No | Sí | Fecha del cambio (auto) |

**Índices:** `idx_hist_club_fecha`

---

## 19. ComentarioClub

**Tabla:** `registry_comentarioclub`  
**Descripción:** Comentarios de usuarios sobre clubes (instituciones y federación).

| Campo | Tipo | Nulo | Único | Índice | Descripción |
|-------|------|------|-------|--------|-------------|
| `id` | Integer (PK) | No | Sí | Sí | Identificador automático |
| `club_id` | FK → Club | No | No | Sí | Club comentado |
| `usuario_id` | FK → User | No | No | No | Usuario que comenta |
| `comentario` | TextField | No | No | No | Contenido del comentario |
| `es_federacion` | BooleanField | No | No | No | Indica si el comentario es de la federación |
| `fecha` | DateTimeField | No | No | Sí | Fecha del comentario (auto) |

**Índices:** `idx_com_club_fecha`

---

## 20. CalificacionClub

**Tabla:** `registry_calificacionclub`  
**Descripción:** Calificaciones de instituciones a clubes (1–5 estrellas).

| Campo | Tipo | Nulo | Único | Índice | Descripción |
|-------|------|------|-------|--------|-------------|
| `id` | Integer (PK) | No | Sí | Sí | Identificador automático |
| `club_id` | FK → Club | No | No | Sí | Club calificado |
| `institucion_id` | FK → Institucion | No | No | No | Institución que califica |
| `puntuacion` | IntegerField | No | No | No | Puntuación: 1 (Muy Malo) a 5 (Excelente) |
| `resena` | TextField | Sí | No | No | Reseña textual |
| `fecha` | DateTimeField | No | No | Sí | Fecha de la calificación (auto) |

**Restricciones:** `unique_together = [club, institucion]`  
**Índices:** `idx_calif_club_fecha`

---

## 21. SolicitudEliminacionClub

**Tabla:** `registry_solicitudeliminacionclub`  
**Descripción:** Solicitudes de eliminación de clubes iniciadas por instituciones, revisadas por la federación.

| Campo | Tipo | Nulo | Único | Índice | Descripción |
|-------|------|------|-------|--------|-------------|
| `id` | Integer (PK) | No | Sí | Sí | Identificador automático |
| `club_id` | FK → Club | No | No | No | Club cuya eliminación se solicita |
| `institucion_solicitante_id` | FK → Institucion | No | No | No | Institución que solicita la eliminación |
| `motivo` | TextField | No | No | No | Motivo de la solicitud |
| `estado` | CharField(20) | No | No | Sí | Estado: `pendiente`, `aprobada`, `rechazada` |
| `fecha_solicitud` | DateTimeField | No | No | No | Fecha de solicitud (auto) |
| `fecha_respuesta` | DateTimeField | Sí | No | No | Fecha de respuesta |
| `observaciones_federacion` | TextField | Sí | No | No | Observaciones de la federación |
| `revisado_por_id` | FK → User | Sí | No | No | Usuario que revisó la solicitud |

**Índices:** `idx_sol_elim_estado`

---

## 22. Evento

**Tabla:** `registry_evento`  
**Descripción:** Eventos del sistema (competencias, talleres, seminarios, etc.). Puede ser institucional o de club, con flujo de aprobación y máquina de estados.

| Campo | Tipo | Nulo | Único | Índice | Descripción |
|-------|------|------|-------|--------|-------------|
| `id` | Integer (PK) | No | Sí | Sí | Identificador automático |
| `nombre` | CharField(255) | No | No | Sí | Nombre del evento |
| `tipo` | CharField(100) | No | No | Sí | Tipo: `Competencia`, `Taller`, `Seminario`, `Conferencia`, `Exhibición`, `Hackathon`, `Feria`, `Encuentro`, `Capacitación`, `Otro` |
| `categoria` | CharField(100) | Sí | No | No | Categoría del evento |
| `fecha` | DateField | No | No | Sí | Fecha de inicio |
| `fecha_hasta` | DateField | Sí | No | Sí | Fecha de fin |
| `descripcion` | TextField | Sí | No | No | Descripción del evento |
| `modalidad` | CharField(20) | No | No | No | Modalidad: `presencial`, `virtual`, `hibrido` |
| `ubicacion` | CharField(255) | Sí | No | No | Ubicación del evento |
| `estado_evento` | CharField(20) | No | No | Sí | Estado (ver máquina de estados) |
| `observacion_estado` | TextField | Sí | No | No | Motivo de pausa, rechazo o cancelación |
| `estado_id` | FK → Estado | Sí | No | No | Estado geográfico del evento |
| `municipio_id` | FK → Municipio | Sí | No | No | Municipio del evento |
| `parroquia_id` | FK → Parroquia | Sí | No | No | Parroquia del evento |
| `direccion` | CharField(300) | Sí | No | No | Dirección del evento |
| `capacidad_maxima` | PositiveIntegerField | Sí | No | No | Capacidad máxima de inscripciones |
| `requisitos` | TextField | Sí | No | No | Requisitos para participar |
| `telefono_codigo` | CharField(4) | Sí | No | No | Código de área del teléfono de contacto |
| `telefono_numero` | CharField(7) | Sí | No | No | Número de teléfono de contacto |
| `email_contacto` | EmailField | Sí | No | No | Correo de contacto |
| `tipo_evento` | CharField(20) | No | No | Sí | Tipo: `institucional`, `club` |
| `es_publico` | BooleanField | No | No | Sí | Visible para todas las instituciones |
| `audiencia` | CharField(25) | No | No | Sí | Audiencia: `publica`, `club_exclusivo`, `institucional_privado` |
| `institucion_id` | FK → Institucion | Sí | No | Sí | Institución organizadora (eventos institucionales) |
| `club_organizador_id` | FK → Club | Sí | No | Sí | Club organizador (eventos de club) |
| `fecha_aprobacion` | DateTimeField | Sí | No | No | Fecha de aprobación |
| `aprobado_por_id` | FK → User | Sí | No | No | Usuario que aprobó el evento |
| `observaciones_aprobacion` | TextField | Sí | No | No | Observaciones de aprobación |
| `fecha_creacion` | DateTimeField | No | No | No | Fecha de creación (default: now) |
| `creado_por_id` | FK → User | Sí | No | No | Usuario que creó el evento |
| `activo` | BooleanField | No | No | Sí | Indica si está activo |
| `cancelado` | BooleanField | No | No | No | Indica si fue cancelado |
| `motivo_cancelacion` | TextField | Sí | No | No | Motivo de cancelación |
| `fecha_actualizacion` | DateTimeField | No | No | No | Fecha de última actualización (auto) |

**Máquina de estados del evento:**
| Estado | Descripción | Transiciones posibles |
|--------|-------------|----------------------|
| `borrador` | Recién creado, editable | → `revision`, `cancelado` |
| `revision` | Enviado para aprobación | → `abierto`, `rechazado`, `cancelado` |
| `abierto` | Abierto para inscripciones | → `pausado`, `cancelado`, `en_proceso` |
| `rechazado` | Rechazado por el ente rector | → `revision`, `cancelado` |
| `pausado` | Temporalmente suspendido | → `abierto`, `cancelado` |
| `en_proceso` | Evento en curso | → `finalizado`, `cancelado`, `pausado` |
| `finalizado` | Evento concluido (terminal) | — |
| `cancelado` | Cancelado definitivamente (terminal) | — |

**Índices:** `idx_evt_fecha_activo`, `idx_evt_institucion`, `idx_evt_tipo_estado`, `idx_evt_club_estado`, `idx_evt_audiencia_estado`

---

## 23. Inscripcion

**Tabla:** `registry_inscripcion`  
**Descripción:** Inscripciones individuales o de equipo a eventos (modelo legado).

| Campo | Tipo | Nulo | Único | Índice | Descripción |
|-------|------|------|-------|--------|-------------|
| `id` | Integer (PK) | No | Sí | Sí | Identificador automático |
| `evento_id` | FK → Evento | No | No | No | Evento al que se inscribe |
| `lider_id` | FK → User | No | No | No | Usuario líder de la inscripción |
| `modalidad` | CharField(20) | No | No | No | Modalidad: `individual`, `equipo` |
| `nombre_proyecto` | CharField(150) | No | No | No | Nombre del proyecto |
| `descripcion_proyecto` | TextField | No | No | No | Descripción del proyecto |
| `fecha_inscripcion` | DateTimeField | No | No | No | Fecha de inscripción (auto) |

---

## 24. IntegranteEquipo

**Tabla:** `registry_integranteequipo`  
**Descripción:** Integrantes de una inscripción de equipo.

| Campo | Tipo | Nulo | Único | Índice | Descripción |
|-------|------|------|-------|--------|-------------|
| `id` | Integer (PK) | No | Sí | Sí | Identificador automático |
| `inscripcion_id` | FK → Inscripcion | No | No | No | Inscripción de equipo |
| `usuario_id` | FK → User | No | No | No | Usuario integrante |

---

## 25. InscripcionGrupoEvento

**Tabla:** `registry_inscripciongrupoevento`  
**Descripción:** Inscripción de grupos (equipos) a eventos. Modelo principal para el flujo de participación.

| Campo | Tipo | Nulo | Único | Índice | Descripción |
|-------|------|------|-------|--------|-------------|
| `id` | Integer (PK) | No | Sí | Sí | Identificador automático |
| `evento_id` | FK → Evento | No | No | No | Evento |
| `grupo_id` | FK → Grupo | No | No | No | Grupo inscrito |
| `rol_participacion` | CharField(20) | No | No | No | Rol: `participante`, `expositor`, `competidor` |
| `fecha_inscripcion` | DateTimeField | No | No | No | Fecha de inscripción (auto) |
| `activo` | BooleanField | No | No | No | Indica si la inscripción está activa |

**Restricciones:** `unique_together = [evento, grupo]`

---

## 26. ClubEvento

**Tabla:** `registry_clubevento`  
**Descripción:** Vinculación de clubes a eventos con rol específico.

| Campo | Tipo | Nulo | Único | Índice | Descripción |
|-------|------|------|-------|--------|-------------|
| `id` | Integer (PK) | No | Sí | Sí | Identificador automático |
| `club_id` | FK → Club | No | No | No | Club |
| `evento_id` | FK → Evento | No | No | Sí | Evento |
| `rol` | CharField(20) | No | No | No | Rol: `organizador`, `colaborador`, `participante` |
| `fecha_vinculacion` | DateTimeField | No | No | No | Fecha de vinculación (auto) |
| `activo` | BooleanField | No | No | Sí | Indica si la vinculación está activa |

**Restricciones:** `unique_together = [club, evento]`  
**Índices:** `idx_clubevt_evt_act`

---

## 27. Grupo

**Tabla:** `registry_grupo`  
**Descripción:** Grupos (equipos) de participantes que se inscriben a eventos. Cada grupo pertenece a una institución y puede tener tutores y participantes asignados.

| Campo | Tipo | Nulo | Único | Índice | Descripción |
|-------|------|------|-------|--------|-------------|
| `id` | Integer (PK) | No | Sí | Sí | Identificador automático |
| `nombre` | CharField(150) | No | No | Sí | Nombre del grupo |
| `codigo` | CharField(20) | No | Sí | No | Código único auto-generado (formato: `EQP-DDMMYY-XXXXXXXX`) |
| `criterio` | CharField(20) | No | No | Sí | Criterio de agrupación: `edad`, `nivel`, `proyecto` |
| `edad_desde` | PositiveIntegerField | Sí | No | No | Edad mínima (criterio `edad`) |
| `edad_hasta` | PositiveIntegerField | Sí | No | No | Edad máxima (criterio `edad`) |
| `nivel_educativo` | CharField(4) | Sí | No | No | Nivel educativo (criterio `nivel`) |
| `nombre_proyecto` | CharField(200) | Sí | No | No | Nombre del proyecto (criterio `proyecto`) |
| `estado_grupo` | CharField(20) | No | No | Sí | Estado: `editable`, `inscrito`, `bloqueado` |
| `usuario_creador_id` | FK → User | No | No | No | Usuario que creó el grupo |
| `institucion_id` | FK → Institucion | Sí | No | Sí | Institución del grupo |
| `tutores` | ManyToMany → Tutor | — | — | — | Tutores asignados al grupo |
| `participantes` | ManyToMany → Participante | — | — | — | Participantes del grupo |
| `evento_id` | FK → Evento | Sí | No | No | Evento al que está inscrito |
| `fecha_registro` | DateTimeField | No | No | No | Fecha de registro (auto) |
| `activo` | BooleanField | No | No | Sí | Indica si el grupo está activo |

**Restricciones:** `unique_nombre_evento_case_insensitive` (nombre + evento, insensible a mayúsculas)  
**Índices:** `idx_grupo_criterio`, `idx_grupo_institucion`

---

## 28. Notificacion

**Tabla:** `registry_notificacion`  
**Descripción:** Sistema de notificaciones internas (buzón de mensajes) para usuarios del sistema.

| Campo | Tipo | Nulo | Único | Índice | Descripción |
|-------|------|------|-------|--------|-------------|
| `id` | Integer (PK) | No | Sí | Sí | Identificador automático |
| `destinatario_id` | FK → User | No | No | Sí | Usuario destinatario |
| `tipo` | CharField(30) | No | No | Sí | Tipo de notificación (ver catálogo) |
| `titulo` | CharField(200) | No | No | No | Título de la notificación |
| `mensaje` | TextField | No | No | No | Contenido del mensaje |
| `leida` | BooleanField | No | No | Sí | Indica si fue leída (default: False) |
| `fecha_creacion` | DateTimeField | No | No | Sí | Fecha de creación (auto) |
| `club_id` | FK → Club | Sí | No | No | Club relacionado (si aplica) |

**Tipos de notificación:**
| Código | Descripción |
|--------|-------------|
| `club_aprobado` | Club Aprobado |
| `club_rechazado` | Club Rechazado |
| `solicitud_eliminacion` | Solicitud de Eliminación |
| `eliminacion_aprobada` | Eliminación Aprobada |
| `eliminacion_rechazada` | Eliminación Rechazada |
| `membresia_aprobada` | Membresía Aprobada |
| `membresia_rechazada` | Membresía Rechazada |
| `salida_club` | Salida de Club |
| `sistema` | Notificación del Sistema |

**Índices:** `idx_notif_dest_leida`

---

## Diagrama de Relaciones Principales

```
User (Django)
 └── UserProfile ──────────────────────── Institucion
                                              │
                    ┌─────────────────────────┤
                    │                         │
               Participante            Club ──┤── MembresiaClu
                    │                    │    │
         ParticipanteInstitucion    ClubTutor │
                    │                    │    │
                  Grupo ◄───────── Tutor ─────┘
                    │         TutorInstitucion
                    │
              Evento ◄── InscripcionGrupoEvento
                    │
              AsistenciaEvento
```

---

*Diccionario generado automáticamente a partir de los modelos Django del proyecto RNR-PRO.*
