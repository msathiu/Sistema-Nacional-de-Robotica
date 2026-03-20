# Tarea: Correccion e Implementacion del Modulo de Eventos

Fecha: 2026-03-19
Proyecto: SistemaRegistro
Enfoque: Alinear modelo, vistas, rutas y templates de Eventos con las reglas de negocio reales.

## 1. Objetivo

Corregir e implementar el modulo de Eventos para que:

- El flujo de estados sea consistente en todo el sistema.
- La creacion por institucion comience en `borrador`.
- El envio a `fed_central` pase a `revision`.
- La aprobacion pase a `abierto`.
- El rechazo pase a `rechazado`.
- La cancelacion pase a `cancelado` respetando permisos.
- La pausa pase a `pausado` con observacion visible.
- El evento pase a `en_proceso` cuando coincide con la fecha actual.
- El evento pase a `finalizado` cuando la fecha ya paso.
- La visibilidad de eventos responda a si el evento es publico o exclusivo de club.
- Existan vistas separadas para `Mis Eventos` y `Eventos`.
- Los modales permitan pausar y cambiar la fecha de forma controlada. Respetando los roles donde la `fed_central` podrá modificar o tener acceso a todos los eventos y las institucionale ssolo eventos propios
- En las vistas separadas para `Mis Eventos` y `Eventos` en `Eventos` debe aparecer todos los eventos creados por las instituciones y aprobados por la federacion `fed_central` al cual podrán asignar los grupos creados que participarán en el evento. También debe aparecer los eventos creados por la federación `fed_central` 
- La federación `fed_central` también crear Evento por lo tanto, cuando un evento es creado por la federación también las instituciones podrán registrar sus respectivos grupos que participarán.
- en  `Mis Eventos` se verá solo los eventos propios creados por las instituciones siguiendo la misma dinámica de eventos 
- Cuando es `fed_central` en `Eventos y Actividades` no debería aparecer el boton para asignar grupos o equipos, solo estará disponible para las instituciones.
- Los campos que se debe mostrar para identificar los eventos debe ser: `Evento / Descripción`,	`Tipo Evento`,	`Tipo`,	`Modalidad`,	`Inscritos`,	`Fecha y Sede`,	`Teléfono`,	`Institución`,	`Estatus`,	`Acciones`


## 2. Inventario Tecnico Identificado

### Apps instaladas

En `SistemaRegistro/SistemaRegistro/settings.py` estan configuradas:

- Django core:
  - `jazzmin`
  - `django.contrib.admin`
  - `django.contrib.auth`
  - `django.contrib.contenttypes`
  - `django.contrib.sessions`
  - `django.contrib.messages`
  - `django.contrib.staticfiles`
- Third party:
  - `crispy_forms`
  - `crispy_bootstrap5`
  - `django_extensions`
- Apps locales:
  - `users.apps.UsersConfig`
  - `registry.apps.RegistryConfig`

### Configuracion de base de datos

En `SistemaRegistro/SistemaRegistro/settings.py`:

- Se usa `dj_database_url.config(...)`.
- Por defecto en desarrollo usa SQLite:
  - `sqlite:///{BASE_DIR}/db.sqlite3`
- En produccion usa `DATABASE_URL` desde variables de entorno.
- `TIME_ZONE = "America/Caracas"`
- `USE_TZ = True`

### Rutas principales definidas

#### Proyecto

En `SistemaRegistro/SistemaRegistro/urls.py`:

- `admin/dashboard/`
- `admin/logs/`
- `admin/`
- `'' -> users.urls`
- `registry/ -> registry.urls`
- AJAX de municipios y parroquias

#### Users

En `SistemaRegistro/users/urls.py` hay rutas de:

- autenticacion
- dashboard
- instituciones
- participantes
- eventos
- grupos
- clubes
- perfil
- AJAX

Rutas de eventos relevantes detectadas:

- `eventos/`
- `institucion/eventos/crear/`
- `institucion/gestionar-eventos/`
- `institucion/seguimiento-eventos/`
- `institucion/eventos/enviar-revision/<int:evento_id>/`
- `institucion/eventos/<int:evento_id>/detalle/`
- `eventos/editar/<int:evento_id>/`
- `eventos/cambiar-estado/<int:evento_id>/`
- `eventos/cancelar/<int:evento_id>/`
- `eventos/detalle/<int:evento_id>/`
- `eventos/inscribir/<int:evento_id>/`

Nota: `users/urls.py` tiene duplicidad de rutas de eventos y nombres repetidos (`crear_evento`, `eventos_disponibles`, `editar_evento`, `inscribir_grupo_evento`).

#### Registry

En `SistemaRegistro/registry/urls.py` hay rutas de:

- registro publico
- grupos
- clubes
- membresias
- notificaciones
- reportes
- eventos institucionales disponibles
- eventos de club
- administracion de eventos
- tutores

Rutas de eventos relevantes detectadas:

- `eventos/disponibles/`
- `eventos/<int:evento_id>/inscribir/`
- `clubes/<int:club_id>/eventos/`
- `eventos-club/<int:evento_id>/detalle/`
- `eventos-club/<int:evento_id>/enviar-revision/`
- `eventos-club/<int:evento_id>/inscribir-grupo/`
- `admin/eventos/todos/`
- `admin/eventos/<int:evento_id>/aprobar/`
- `admin/eventos/<int:evento_id>/rechazar/`

### Modelos principales

#### App `users`

En `SistemaRegistro/users/models.py`:

- `UserProfile`
- `Estados`
- `Municipios`

#### App `registry`

La app usa paquete `registry/models/`, no un `models.py` unico.

Modelos principales exportados desde `registry/models/__init__.py`:

- Base geograficos:
  - `Estado`
  - `Municipio`
  - `Parroquia`
  - `Dependencia`
- Dominio institucional:
  - `Institucion`
- Participantes:
  - `Participante`
  - `ParticipanteInstitucion`
  - `ParticipanteGrupo`
  - `AsistenciaEvento`
- Tutores:
  - `Tutor`
  - `TutorInstitucion`
- Eventos:
  - `Evento`
  - `Inscripcion`
  - `InscripcionGrupoEvento`
  - `IntegranteEquipo`
  - `ClubEvento`
- Clubes:
  - `Club`
  - `MembresiaClu`
  - `SolicitudEliminacionClub`
  - `HistorialClub`
  - `ComentarioClub`
  - `CalificacionClub`
  - `ClubLineaInvestigacion`
- Grupos:
  - `Grupo`
- Notificaciones:
  - `Notificacion`

### Archivos Markdown identificados

En la raiz del proyecto:

- `README.md`
- `GEMINI.md`

En la carpeta `doc/` existen 134 archivos `.md`. Entre los mas relevantes para eventos:

- `doc/EVENTO.md`
- `doc/ARQUITECTURA_EVENTOS_MEJORADA.md`
- `doc/CHECKLIST_IMPLEMENTACION_EVENTOS.md`
- `doc/INDICE_DOCUMENTACION_EVENTOS.md`
- `doc/RESUMEN_EJECUTIVO_EVENTOS.md`
- `doc/FASE5_LOGICA_VISIBILIDAD_COMPLETADA.md`

Nota: parte de esa documentacion esta desalineada con el modelo actual y usa estados legacy como `pendiente`, `aprobado` y `publicado`.

## 3. Estado Actual del Dominio Evento

En `SistemaRegistro/registry/models/evento.py` el modelo real ya define:

- Estados:
  - `borrador`
  - `revision`
  - `abierto`
  - `rechazado`
  - `cancelado`
  - `pausado`
  - `en_proceso`
  - `finalizado`
- Audiencias:
  - `publica`
  - `club_exclusivo`
  - `institucional_privado`
- Permisos de dominio:
  - `puede_cancelar(usuario)`
  - `puede_pausar(usuario)`
  - `solicitar_revision()`
  - `aprobar(usuario, observaciones="")`
  - `rechazar(observaciones)`
  - `pausar(observaciones)`
  - `cancelar(observaciones)`
- Actualizacion automatica por fecha:
  - `abierto -> en_proceso` si `fecha == hoy`
  - `abierto/en_proceso -> finalizado` si `fecha < hoy`

## 4. Hallazgos Criticos

### 4.1 Inconsistencia de estados entre modelo y vistas

El modelo usa:

- `revision`
- `abierto`

Pero varias vistas/templates usan:

- `pendiente`
- `aprobado`
- `publicado`
- `cerrado`
- `en_revision`

Esto rompe la coherencia entre capa de dominio, UI y consultas.

### 4.2 Aprobacion administrativa fuera del dominio real

`registry/views_admin_eventos.py` y varias vistas en `users/views.py` siguen aprobando o listando eventos con estados legacy:

- aprueban a `aprobado`
- filtran por `pendiente`
- inscriben con `aprobado/publicado/abierto`

Debe centralizarse en:

- `borrador -> revision -> abierto`
- `revision -> rechazado`

### 4.3 Visibilidad incompleta

Hoy hay mezcla de reglas:

- algunas vistas muestran todos los eventos activos
- otras filtran por audiencia
- otras usan reglas de club

Debe existir una unica politica de visibilidad para:

- `fed_central`
- institucion creadora
- instituciones ajenas
- miembros del club

### 4.4 Mis Eventos no esta claramente separado de Eventos

El requerimiento exige:

- `Eventos y Actividades -> Mis Eventos`
  - solo eventos creados por la institucion autenticada
- `Eventos y Actividades -> Eventos`
  - eventos aprobados de otras instituciones
  - eventos creados por `fed_central`

Hoy la estructura existe parcialmente entre `gestionar_eventos_institucion`, `seguimiento_eventos_institucion` y `eventos_disponibles`, pero no esta unificada con la nueva logica.

### 4.5 Templates referencian rutas o estados inconsistentes

Se detecto que templates de eventos usan:

- estados legacy
- badges que no coinciden con `EstadoEvento`
- acciones de aprobar/rechazar con flujo antiguo
- botones a rutas de gestion que requieren revisarse

### 4.6 Los modales de pausa y cambio de fecha no estan implementados de forma consistente

Debe existir un flujo explicito para:

- pausar evento
- capturar observacion obligatoria
- permitir cambio de fecha
- registrar nueva fecha
- opcionalmente reabrir el evento
- notificar la razon a las instituciones inscritas

## 5. Requerimientos Funcionales Definitivos

### 5.1 Flujo institucional publico

Cuando una institucion crea un evento:

- si el evento es publico:
  - tipo de evento visible: `Evento Institucional Abierto - Cualquier Institucion puede participar`
  - visibilidad: `Publica`
- se crea en `borrador`
- la institucion puede editarlo mientras este en `borrador` o `rechazado`
- al enviar a `fed_central`, pasa a `revision`
- si `fed_central` aprueba, pasa a `abierto`
- desde `abierto` queda visible para todas las instituciones
- otras instituciones pueden inscribir sus grupos

### 5.2 Flujo institucional exclusivo para club

Si el evento es para un club particular:

- tambien requiere aprobacion de `fed_central`
- una vez aprobado, solo deben verlo:
  - instituciones que pertenezcan al club
  - `fed_central`
- no debe aparecer como publico para instituciones ajenas

### 5.3 Reglas de cancelacion

- Institucion:
  - solo puede cancelar eventos creados por su propia institucion
- `fed_central`:
  - puede cancelar eventos de cualquier institucion

### 5.4 Regla de pausa

- solo `fed_central` pausa
- estado destino: `pausado`
- `observacion_estado` obligatoria
- la observacion debe ser visible a instituciones ya inscritas
- el modal debe permitir:
  - observacion
  - nueva fecha opcional/obligatoria segun politica acordada

### 5.5 Reglas por fecha

- `abierto -> en_proceso` si `fecha == hoy`
- `en_proceso/abierto/pausado` deben evaluarse para cierre segun politica de negocio
- si la fecha ya paso, el evento pasa a `finalizado`

Nota de arquitectura:
El modelo actual finaliza solo desde `abierto` y `en_proceso`. Debe definirse si `pausado` con fecha vencida tambien se finaliza o si requiere una accion manual.

## 6. Arquitectura Objetivo

## 6.1 Estado unico de negocio

Mantener solo estos estados como canonicos:

- `borrador`
- `revision`
- `abierto`
- `rechazado`
- `cancelado`
- `pausado`
- `en_proceso`
- `finalizado`

Eliminar uso de estados legacy en vistas, queries, forms y templates:

- `pendiente`
- `aprobado`
- `publicado`
- `cerrado`
- `en_revision`

## 6.2 Matriz de visibilidad

### `Mis Eventos`

Visible para usuario institucional:

- todos los eventos cuya `institucion` sea la misma que `request.user.userprofile.institution`

Estados visibles:

- `borrador`
- `revision`
- `abierto`
- `rechazado`
- `pausado`
- `cancelado`
- `en_proceso`
- `finalizado`

### `Eventos`

Visible para usuario institucional:

- eventos `abierto`, `pausado`, `en_proceso` o `finalizado` segun regla de visualizacion del catalogo
- creados por otras instituciones y ya aprobados
- creados por `fed_central`
- si `audiencia = publica`, visible para todas las instituciones
- si `audiencia = club_exclusivo`, visible solo si la institucion tiene membresia activa en el club
- no mostrar en esta vista los eventos propios de la institucion salvo que negocio quiera verlos repetidos

### `fed_central`

Ve todos los eventos en cualquier estado.

## 6.3 Servicios sugeridos

Crear o consolidar un servicio de dominio, por ejemplo:

- `registry/services/evento_service.py`

Con responsabilidades:

- validar transiciones
- evaluar permisos de usuario
- enviar a revision
- aprobar
- rechazar
- cancelar
- pausar y reprogramar
- recalcular estados por fecha
- obtener eventos visibles por usuario

## 7. Backlog de Implementacion

### Fase 1. Normalizacion de estados y rutas

Archivos objetivo:

- `SistemaRegistro/registry/models/evento.py`
- `SistemaRegistro/registry/views_admin_eventos.py`
- `SistemaRegistro/registry/views_eventos.py`
- `SistemaRegistro/registry/views_institucional.py`
- `SistemaRegistro/users/views.py`
- `SistemaRegistro/users/urls.py`
- `SistemaRegistro/registry/urls.py`

Tareas:

- Unificar todas las vistas al enum `EstadoEvento`.
- Sustituir filtros legacy por estados reales.
- Eliminar duplicidades y conflicto de nombres en `users/urls.py`.
- Revisar nombres de ruta para que:
  - crear
  - mis eventos
  - eventos
  - detalle
  - enviar revision
  - aprobar
  - rechazar
  - pausar
  - cancelar
  - reprogramar
  sean explicitos y sin ambiguedad.

### Fase 2. Crear vistas separadas de Mis Eventos y Eventos

Archivos objetivo:

- `SistemaRegistro/users/views.py`
- templates de `users/`
- menu lateral o tarjetas de navegacion

Tareas:

- `mis_eventos_institucion`
  - solo eventos creados por mi institucion
- `eventos_disponibles`
  - solo eventos visibles para mi institucion segun audiencia y estado
- excluir eventos propios de la vista general si ese es el comportamiento requerido
- mantener `fed_central` con vista total administrativa

### Fase 3. Ajustar flujo de creacion institucional

Archivos objetivo:

- `SistemaRegistro/users/views.py`
- form/template de crear evento

Tareas:

- al crear como institucion:
  - guardar `estado_evento = borrador`
  - guardar `institucion` del usuario autenticado
  - guardar `tipo_evento` y `audiencia` correctos
- si es publico:
  - setear copy funcional y badge correcto
- si es de club:
  - validar membresia o relacion organizadora
- exponer boton `Enviar a revision` solo desde estados permitidos

### Fase 4. Corregir aprobacion por `fed_central`

Archivos objetivo:

- `SistemaRegistro/registry/views_admin_eventos.py`
- template `registry/admin_todos_eventos.html`

Tareas:

- cambiar flujo real a:
  - `revision -> abierto`
  - `revision -> rechazado`
- registrar:
  - `aprobado_por`
  - `fecha_aprobacion`
  - `observaciones_aprobacion`
- para evento institucional publico:
  - `audiencia = publica`
  - visible a todas las instituciones
- para evento exclusivo de club:
  - mantener `audiencia = club_exclusivo`

### Fase 5. Pausa, reprogramacion y modales

Archivos objetivo:

- vistas de detalle/gestion de evento
- templates de detalle y gestion
- modales bootstrap relacionados

Tareas:

- crear accion `pausar_evento`
- exigir observacion obligatoria
- permitir cambio de fecha desde el modal o un modal separado de `reprogramar_evento`
- persistir:
  - `estado_evento = pausado`
  - `observacion_estado`
  - `fecha` nueva cuando aplique
- decidir si reabrir automaticamente a `abierto` tras guardar nueva fecha o dejar accion manual
- mostrar observacion a:
  - instituciones inscritas
  - propietario
  - `fed_central`

### Fase 6. Permisos de cancelacion

Archivos objetivo:

- `SistemaRegistro/registry/models/evento.py`
- vistas que ejecutan cancelacion

Tareas:

- reutilizar `puede_cancelar(usuario)`
- impedir cancelacion por instituciones ajenas
- permitir cancelacion por `fed_central`
- hacer visible `motivo_cancelacion`

### Fase 7. Reglas de fecha

Archivos objetivo:

- `SistemaRegistro/registry/models/evento.py`
- servicio o comando programado

Tareas:

- ejecutar actualizacion automatica por fecha
- evaluar si debe existir:
  - comando `manage.py actualizar_estados_eventos`
  - cron / scheduler
- cubrir:
  - `abierto -> en_proceso`
  - `abierto/en_proceso -> finalizado`
- definir comportamiento de `pausado` con fecha vencida

### Fase 8. Templates y UX

Archivos objetivo:

- `SistemaRegistro/registry/templates/registry/admin_todos_eventos.html`
- `SistemaRegistro/registry/templates/registry/eventos_disponibles.html`
- `SistemaRegistro/registry/templates/registry/evento_club_lista.html`
- templates en `users/templates/users/` de gestion institucional

Tareas:

- reemplazar badges y textos de estados legacy
- agregar badges correctos para:
  - publico
  - exclusivo club
  - privado institucional
- mostrar observacion de pausa y rechazo
- mostrar origen:
  - mi institucion
  - otra institucion
  - `fed_central`
- agregar acciones visibles segun permiso y estado

## 8. Criterios de Aceptacion

- Un evento institucional creado por una institucion nace en `borrador`.
- Desde `borrador` el usuario institucional puede enviarlo a `revision`.
- `fed_central` puede aprobar y el evento pasa a `abierto`.
- `fed_central` puede rechazar y el evento pasa a `rechazado`.
- Una institucion solo puede cancelar eventos de su propia institucion.
- `fed_central` puede cancelar cualquier evento.
- `fed_central` puede pausar un evento y dejar observacion visible.
- El modal de pausa permite reprogramar fecha.
- La vista `Mis Eventos` muestra solo eventos propios.
- La vista `Eventos` muestra eventos aprobados de otras instituciones y los de `fed_central`.
- Si el evento es exclusivo de club, solo lo ven instituciones miembros del club y `fed_central`.
- No deben quedar referencias activas a estados legacy en vistas, rutas o templates.

## 9. Riesgos a Corregir Antes de Implementar

- `users/urls.py` tiene rutas duplicadas de eventos; eso puede generar comportamiento ambiguo.
- `registry/views_admin_eventos.py` todavia consulta `pendiente/aprobado`.
- `registry/views_eventos.py` todavia consulta `pendiente/aprobado`.
- `registry/views_institucional.py` y `users/views.py` mezclan `abierto/aprobado/publicado`.
- varios templates usan badges y acciones de estados obsoletos.
- la documentacion previa de eventos no puede usarse como fuente unica de verdad.

## 10. Recomendacion de Implementacion

Orden sugerido:

1. Normalizar estados y rutas.
2. Corregir vistas administrativas de aprobacion.
3. Corregir creacion institucional y envio a revision.
4. Separar `Mis Eventos` de `Eventos`.
5. Implementar visibilidad por audiencia.
6. Implementar pausa y reprogramacion con modales.
7. Agregar pruebas de dominio, permisos y vistas.

## 11. Pruebas Minimas Requeridas

- test de transiciones validas de `Evento`
- test de `puede_cancelar`
- test de `puede_pausar`
- test de visibilidad publica
- test de visibilidad por club
- test de `Mis Eventos`
- test de aprobacion por `fed_central`
- test de rechazo con observacion
- test de pausa con observacion y cambio de fecha
- test de actualizacion automatica por fecha

## 12. Resultado Esperado

Al finalizar, el modulo de Eventos debe comportarse como un flujo de negocio estable y unico, donde el modelo `Evento` sea la fuente real de verdad, las vistas respeten sus transiciones y permisos, y la interfaz muestre correctamente que eventos son propios, cuales estan abiertos a otras instituciones y cuales son exclusivos para miembros de club.
