# ANÁLISIS E IMPLEMENTACIÓN DE FLUJO DE CLUBES EN DJANGO

## CONTEXTO DEL PROYECTO
Soy desarrollador Django y necesito implementar un sistema de gestión de clubes con múltiples roles y aprobaciones. El proyecto ya tiene una base con modelos de usuarios, instituciones y perfiles. Necesito que analices el código existente y me ayudes a implementar las funcionalidades faltantes según el flujo descrito.
ESTRUCTURA ACTUAL DEL PROYECTO (verificar y analizar)
Modelos existentes (deben ser revisados), sobre todo los club o clubes 
(necesito verificar si existe)

ACTORES Y ROLES (según UserProfile.user_type):
Federación Central (fed_central): Usuario administrador central - único que puede aprobar

Institución (participante con perfil institucional): Usuario de instituciones o sedes (matriz/sedes)

REQUERIMIENTOS FUNCIONALES
1. GESTIÓN DE CLUBES (FLUJO COMPLETO)
1.1 Creación de Club por Institución

Las instituciones (sedes/matriz) pueden crear clubes

Al crear, estado inicial: pendiente_aprobacion

Validar que la institución tenga permisos para crear clubes

1.2 Aprobación de Club por Federación Central

Fed Central ve lista de clubes pendientes

Puede aprobar o rechazar club

Al aprobar:

Cambiar estado a activo

La institución creadora se convierte automáticamente en miembro propietario

Notificar a la institución

2. GESTIÓN DE EVENTOS
2.1 Creación de Evento por Institución (para sus clubes)

Institución propietaria puede crear eventos para sus clubes

Evento estado inicial: pendiente_aprobacion

2.2 Aprobación de Evento por Federación Central

Fed Central ve eventos pendientes

Puede aprobar o rechazar

Al aprobar, evento queda activo para el club anfitrión

3. MEMBRESÍAS DE INSTITUCIONES A CLUBES
3.1 Postulación de Otra Institución

Institución no propietaria puede postularse a un club

Crear ticket/postulación con estado pendiente_institucion

3.2 Doble Aprobación

Primera aprobación: Institución propietaria del club

Puede pre-aprobar o rechazar postulación

Si pre-aprueba, pasa a pendiente_federacion

Segunda aprobación: Federación Central

Da visto bueno final

Confirma como miembro del club

Estado final: activo

4. DASHBOARD Y VISUALIZACIONES
4.1 Vista de Federación Central
Debe poder visualizar:

Listado de todos los clubes creados (con filtros)

Clubes por estado (activos, pendientes, rechazados)

Eventos asociados a clubes:

Aprobados

Pendientes por aprobar

Rechazados

Postulaciones pendientes de visto bueno

Estadísticas generales

4.2 Vista de Institución

Mis clubes (donde soy propietario)

Eventos de mis clubes

Postulaciones pendientes de mi aprobación

Clubes donde soy miembro

TAREAS ESPECÍFICAS A REALIZAR
FASE 1: ANÁLISIS DE CÓDIGO EXISTENTE
Verificar si ya existe modelo Club y sus campos

Verificar si ya existe modelo Evento y sus campos

Verificar si ya existe modelo Membresia o Postulacion

Analizar sistema de permisos actual (señales en signals.py)

Revisar servicios existentes en /services/

## COMPROBAR 
Cuando una institucion (Usuario Institucional (Sedes/Matriz) | Usuario de instituciones o sedes) crea un club y este es aprobado por el usuario 
Federación Central (Ente Rector) | Usuario administrador central - único que puede aprobar 
esta institución se convierte automaticamente en miembro propietario y el usuario 
Federación Central (Ente Rector) | Usuario administrador central - único que puede aprobar los clubes creados por las instituciones, las instituciones 
(Usuario Institucional (Sedes/Matriz) | Usuario de instituciones o sedes) son las que administrarán sus propios club pero cuando crean eventos para los club 
estos debe pasar y ser aprobados por el usuario (Federación Central (Ente Rector) | Usuario administrador central) y una vez aprobados los eventos quedan activos para los club de las institución anfitriona
si otra institución quiere ser miembro del club crea un un tiquect de postulación que debe ser aprobado por la institución creadora del club y pueda ser visto por el usuario 
Federación Central (Ente Rector) | Usuario administrador central quien dará el visto bueno o confirma para que sean mienbros del club, el el usuario 
Federación Central (Ente Rector) | Usuario administrador central debe poder visualizar las información del los clubes creados, eventos asociados aprobados, pendientes por aprobar, rezachados 