# Plan Seguro de Rename de Metadata de Eventos

Fecha: 2026-03-19
Objetivo: renombrar metadata tecnica legacy de aprobacion en `Evento` sin mezclarla con cambios funcionales.

## 1. Problema actual

El flujo canonico del modulo ya no es:

- `pendiente -> aprobado`

Ahora el flujo correcto es:

- `borrador -> revision -> abierto`
- `revision -> rechazado`

Pero el modelo `Evento` todavia conserva:

- `aprobado_por`
- `fecha_aprobacion`
- `observaciones_aprobacion`

Eso ya no representa bien la semantica del dominio.

## 2. Naming recomendado

La opcion mas neutra y consistente es:

- `revisado_por`
- `fecha_revision`
- `observaciones_revision`

Justificacion:

- sirve para una revision que abre el evento
- sirve para una revision que rechaza el evento
- evita acoplar el nombre del campo a un resultado exitoso

## 3. Estrategia segura

Hacer este refactor en una tarea separada de los cambios funcionales.

Orden recomendado:

1. Renombrar campos en el modelo `Evento`
2. Generar migracion con `RenameField`
3. Actualizar vistas
4. Actualizar templates
5. Actualizar tests
6. Ejecutar migraciones y pruebas

## 4. Cambios concretos propuestos

### Modelo

- `aprobado_por` -> `revisado_por`
- `fecha_aprobacion` -> `fecha_revision`
- `observaciones_aprobacion` -> `observaciones_revision`

### Related name

Actualmente:

- `related_name="eventos_club_aprobados"`

Propuesto:

- `related_name="eventos_revisados"`

## 5. Riesgos a cubrir

- `update_fields=[...]` en vistas
- admin de Django
- templates que aun digan "Aprobado"
- tests legacy del modulo

## 6. Criterio de cierre

El rename queda cerrado cuando:

- no existan referencias activas a `aprobado_por`, `fecha_aprobacion` ni `observaciones_aprobacion` en el flujo de eventos
- las migraciones apliquen sin perdida de datos
- los tests del modulo de eventos pasen
