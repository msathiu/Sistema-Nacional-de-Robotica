# Especificación Técnica: Flujo de Aprobación Federado

## Contexto
El sistema gestiona la relación entre tres entidades:
1. **Ente Rector:** Supervisor global.
2. **Institución creadora:** Creadora y administradora operativa de un Club.
3. **Institución Solicitante:** Institución que desea unirse a un Club existente.

## Modelo de Datos (Sugerido)
- `Club`: Posee un `owner` (Institución Fundadora).
- `MembresiaClub`: Tabla intermedia entre `Institucion` y `Club`.
- `EstadoMembresia`: [PENDIENTE_FUNDADOR, PENDIENTE_RECTOR, APROBADO, RECHAZADO].

## Lógica del Workflow de Unión al Club
1. **Solicitud:** Una `Institucion` crea un registro en `MembresiaClub` con estado `PENDIENTE_FUNDADOR`.
2. **Validación Operativa (Filtro 1):** 
   - Solo la **Institución Fundadora** puede cambiar el estado de `PENDIENTE_FUNDADOR` a `PENDIENTE_RECTOR`.
   - Si rechaza, el estado cambia a `RECHAZADO`.
3. **Validación Legal (Filtro 2):** 
   - Solo el **Ente Rector** puede cambiar el estado de `PENDIENTE_RECTOR` a `APROBADO`.
   - El Ente Rector tiene visibilidad de todas las membresías en cualquier estado para supervisión.

## Requerimientos Técnicos
- Implementar validación a nivel de servicios/vistas para asegurar que una parte no apruebe lo que le corresponde a la otra.
- Documentar cada función con Docstrings siguiendo el estándar Google Style.
- Registrar un log de cambios (quién aprobó y cuándo).

# Especificación: Proceso de Admisión a Club (Ecosistema Legal)

## Contexto del Modelo
- **Entidades:** Institución Rectora (Owner), Inst. Fundadora (Operador), Inst. Solicitante (Candidato).
- **Estado de Pertenencia:** El control legal reside en la Rectora, la operativa en la Fundadora.

## Workflow de Aprobación (Sección 6)
1. **Solicitud:** `Solicitante` crea registro con estado `PENDIENTE_FILTRO`.
2. **Primer Filtro (Fundadora):** - Acción: `visto_bueno()`. 
   - Cambio de estado: de `PENDIENTE_FILTRO` a `VISTO_BUENO_FUNDADORA`.
3. **Aprobación Final (Ente Rector):** - Acción: `validar_normativa_global()`.
   - Cambio de estado: de `VISTO_BUENO_FUNDADORA` a `MIEMBRO_ACTIVO`.

## Reglas de Negocio
- Solo usuarios con rol  Institucional y  `FUNDADORA` pueden ejecutar el paso 2.
- Solo usuarios con rol `RECTORA` ente rector pueden ejecutar el paso 3.
- Ninguna institución puede ser `MIEMBRO_ACTIVO` sin ambos checks.

## Agregar las notificaciones p
