# Actuar como Arquitecto de software Senior y experto en programación con Django y HTML para Analizar, evaluar,  e implementar comprendiendo que es un sistema en desarrollo y aplicando el modelo MVT
##  Prioridad de no romper el sistema actual ##
**ENTIDAD: PARTICIPANTE (Tabla: participantes)** 
1. analizar si la tabla o modelo Participante tiene las siguientes campos:
Campo	Tipo	Descripción
grupo_id	FK	Grupo al que pertenece por defecto null
cedula_personal	VARCHAR(20)	Cédula de identidad (nullable)
cedula_escolar	VARCHAR(20)	Cédula escolar (nullable)
condicion_tea	BOOLEAN	¿Posee condición en espectro autista?
status	ENUM	activo | inactivo
estado id Estado al que pertenece modelo Estado
municipio id Municipio al que pertenece modelo municipio
Parroquia id al que pertenece modelo Parroquia
campo1 tipo text

2. Agregar a la Tabla participante los campos anteriores si no los tiene y verificar con formulario form.py
Campo	Tipo	Descripción
grupo_id	FK	Grupo al que pertenece por defecto null
cedula_personal	VARCHAR(20)	Cédula de identidad (nullable)
cedula_escolar	VARCHAR(20)	Cédula escolar (nullable)
condicion_tea	BOOLEAN	¿Posee condición en espectro autista?
status	ENUM	activo | inactivo
status	ENUM	activo | inactivo
estado id Estado al que pertenece modelo Estado
municipio id Municipio al que pertenece modelo municipio
Parroquia id al que pertenece modelo Parroquia
campo1 tipo text
3. Chequear el html en URL(participantes/crear) y verificar y mejorar en el registro que el formulario para Registro de Nuevo Participante tenga los siguientes campos:
- Nombres
- Apellidos
Correo Electrónico
Cédula 
Cédula escolar
Fecha de Nacimiento
Edad
Sexo
Teléfono
Estado (Asignado)
Municipio
Parroquia
Dirección de Vivienda
Grado / Nivel
Nombre del Plantel / Universidad
Especifique Título / Estudios (este campo solo se muestra si se cumple la condición de seleccionar en el campo "Grado / Nivel ->  Estudios Universitarios )
Cuando en Grado / Nivel se seleccione ->  Otro/no especificado se habilite un campo que pida el grado o nivel y se guarde en campo1 de la tabla participante
- REGLAS DE PARTICIPANTES:
•	Al menos una cédula es obligatoria (personal O escolar)
•	Si cédula existe → autocompletar datos
•	Si cambia cedula escolar ↔ personal → comparar por: Nombre, Apellido, Fecha nacimiento
•	Si coincide → alerta de confirmación
•	Si no coincide → nuevo registro
•	Edad se calcula automáticamente desde fecha_nacimiento

**REGLAS DE PARTICIPANTES: en el formulario se debe validar los siguientes campos**
•	Al menos una cédula es obligatoria (personal O escolar)
•	Si cédula existe → autocompletar datos
•	Si cambia escolar ↔ personal → comparar por: Nombre, Apellido, Fecha nacimiento
•	Si coincide → alerta de confirmación
•	Si no coincide → nuevo registro
•	Edad se calcula automáticamente desde fecha_nacimiento
•   Si es menor de edad mostrar los campos para registrar al Representante Legal

3.  Verificar si existe el modelos AsistenciaEvento para llevar registro de si asistió o no un participante a un evento particular.
 campos que considero debe tener: 
 id evento, 
 id grupo,
 id participante
 asistencia[pendiente|asistió|ausente]
 observación
 fecha de asistencia
 fecha de creación de la asistencia

4. Verificar que todos los campos en en la vista participantes/crear de html Registro de Nuevo Participante coincidan con el modelo participante y
en el formulario form.py 