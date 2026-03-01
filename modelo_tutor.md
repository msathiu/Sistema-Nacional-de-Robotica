@workspace Analiza los modelos existentes de Evento y Grupo. Necesito implementar el Registro de Tutores y conectarlo al flujo de trabajo actual siguiendo estas especificaciones:

1. Creación del Modelo:
Crea la entidad Tutor en models.py con los campos: id (UUID), institucion (FK), nombres, apellidos, cedula (Unique), telefono, email, profesion, experiencia (Text), status (Enum: activo/inactivo) y created_at.

2. Relación y Flujo de Negocio:

Un Evento se asocia a un Grupo.

Modifica o extiende el modelo Grupo para que tenga una relación Many-to-Many con Tutor y con Participante (asumiendo que este último ya existe).

Regla de integridad: Un Grupo no puede estar vinculado a un Evento si no tiene al menos un Tutor asignado.

3. Implementación de Funcionalidad (Capa de Servicio):
Crea un servicio en services.py para:

Registrar el Tutor validando que la cedula no esté duplicada.

Asignar tutores a un grupo específico.

4. Interfaz de Usuario (Vista y Botón):

Crea/Actualiza la vista de gestión de tutores.

Implementa un botón "Registrar Tutor" que abra un formulario con los campos especificados.

Asegúrate de que en la vista de creación de Evento o Grupo, exista un selector para buscar y añadir estos tutores recién creados.

Requerimientos Técnicos:

Usa transaction.atomic para la creación del tutor y su asignación al grupo.

Aplica los estándares de mi archivo @PROMPT_GUIDELINES.md (Type hints, PostgreSQL Index en cedula, y select_related).

Documenta el cambio en docs/workflow_ingreso.md si es necesario."

En la tabla de Grupos, añade un botón de acceso rápido para 'Agregar Tutor' directamente desde los grupos
