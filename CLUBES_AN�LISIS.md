📘 Módulo: Gestión de Clubes
1. Objetivo del Módulo

El módulo de Clubes tiene como finalidad permitir a las instituciones crear, gestionar y vincular clubes académicos basados en líneas de investigación, garantizando control por parte del Ente Rector y trazabilidad para fines estadísticos.

El club se define como una entidad de agrupamiento interno institucional, distinta de eventos o grupos operativos.

2. Alcance Funcional
2.1 Responsabilidades por Rol

Administrador / Ente Rector

Gestiona el catálogo dinámico de líneas de investigación.

Revisa y aprueba/rechaza clubes.

Aprueba/rechaza eventos asociados a clubes.

Consulta estadísticas y resultados.

❌ No crea clubes.

❌ No crea prácticas estudiantiles.

Usuario Institucional

Representa a una institución.

Crea y gestiona clubes.

Solicita vinculación a clubes externos.

Gestiona eventos del club (previa aprobación del ente rector).

3. Catálogos Dinámicos
3.1 LINEA_INVESTIGACION

Catálogo administrado exclusivamente por el Ente Rector.

Características:

Gestionable (CRUD) por administrador.

Utilizado para clasificación de clubes.

Escalable.

Reglas:

Cada club debe tener mínimo 1 línea.

Máximo 3 líneas por club.

4. Modelo de Dominio
4.1 Entidad: Club

Representa una agrupación institucional basada en líneas de investigación.

Relaciones

Un Club pertenece a una Institución.

Un Club puede vincularse a múltiples Eventos.

Relación N:M con líneas de investigación.

4.2 Campos de la Entidad Club
Campo	Descripción
id	Identificador único
institucion_id	Institución propietaria
nombre	Nombre del club
descripcion	Descripción
ubicacion	Ubicación física
fecha_fundacion	Fecha de creación (uso estadístico)
estado_vinculacion	Abierto / Cerrado / Bajo_Invitacion
cupo_maximo_instituciones	Máximo de instituciones externas
cupos_disponibles	Cupos restantes
requisitos_ingreso	Términos de membresía
documento_legal	RUT/NIT o aval
logo	Imagen
siglas	Abreviatura
coordinador_id	Usuario responsable
status	BORRADOR / PENDIENTE / EN_REVISION / APROBADA / RECHAZADA
created_at	Fecha de registro
4.3 Tabla Relacional: CLUB_LINEA_INVESTIGACION

Tabla: clubes_lineas

Relación N:M entre clubes y líneas.

Campo	Descripción
club_id	Referencia al club
linea_investigacion_id	Referencia a la línea
tipo_linea	Soporte / Afines / Vinculantes
5. Reglas de Negocio — Clubes

Mínimo 1 línea de investigación por club.

Máximo 3 líneas por club.

Las líneas son administrables por el Ente Rector.

Una institución no puede tener más de una solicitud pendiente al mismo club.

Cuando cupos_disponibles == 0:

El estado de vinculación cambia automáticamente a Cerrado.

La fecha de fundación es solo informativa (estadística).

6. Flujo de Creación de Club
6.1 Proceso

Usuario Institucional crea club → estado BORRADOR.

Envía a revisión.

Ente Rector evalúa:

Validación de líneas (1–3).

Validación documental.

Decisión:

Si NO cumple

status = RECHAZADA

Se notifica a la institución.

Si cumple

status = APROBADA

Club habilitado.

7. Flujo de Vinculación de Clubes
7.1 Estado del Club

El club anfitrión debe estar en estado:

Abierto

7.2 Proceso de Membresía

Paso 1 — Solicitud

Institución B busca clubes por líneas de investigación.

Envía solicitud con carta de intención.

Registro creado en estado PENDIENTE.

Validaciones automáticas

No debe existir otra solicitud pendiente de la misma institución al club.

club.cupos_disponibles > 0.

Paso 2 — Evaluación

El coordinador del Club A:

Recibe notificación.

Evalúa alineación.

Si APRUEBA

status = APROBADA

Se crea registro en MEMBRESIA_CLUB.

cupos_disponibles -= 1.

Si cupos llega a 0 → club pasa a Cerrado.

Si RECHAZA

status = RECHAZADA

Se envía retroalimentación.

8. Gestión de Eventos del Club

Los clubes pueden tener eventos propios dirigidos exclusivamente a:

miembros del club

grupos del club

participantes del club

8.1 Flujo de Creación de Evento

Institución crea evento del club.

Estado inicial: EN_REVISION.

Ente Rector evalúa.

Si aprueba

estado_aprobacion = APROBADO_PARA_PUBLICAR

luego → PUBLICADO

Si rechaza

Se notifica con motivo.

8.2 Estados Operativos del Evento

ABIERTO

PAUSADO

CERRADO

8.3 Estados de Aprobación (Federación)

EN_REVISION

APROBADO_PARA_PUBLICAR

PUBLICADO

EN_PROCESO

CONCLUIDO

9. Reglas de Eventos

Administrador puede crear:

Competiciones

Conferencias/Foros

Cursos/Talleres

Ferias

Administrador NO puede crear:

Clubes

Prácticas estudiantiles

Un grupo solo puede pertenecer a un evento.

Participantes de distintos grupos pueden coincidir en un evento.

No permitir participantes en eventos de distintos territorios.

Permitir múltiples categorías en la misma fecha.

No permitir misma categoría en la misma fecha.

Clubes solo manejan fecha de fundación (no fechas operativas).

10. Consideraciones Técnicas Recomendadas
Validaciones críticas

Constraint para máximo 3 líneas por club.

Índice único parcial para evitar solicitudes duplicadas pendientes.

Trigger o lógica de dominio para cierre automático por cupos.

Auditoría de cambios de estado.

Escalabilidad

Catálogos dinámicos parametrizables.

Estados manejados por enums.

Separación clara entre:

estado operativo

estado de aprobación

estado de vinculación

11. Extensiones Futuras Sugeridas

Métricas de participación por club.

Ranking de clubes por actividad.

Historial de membresías.

Versionado de documentos legales.