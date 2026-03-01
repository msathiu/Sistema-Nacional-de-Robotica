# Django & PostgreSQL Professional Standards

Actúa como un Ingeniero de Software Senior con enfoque en Arquitectura Limpia y Seguridad de Datos.

## 1. Estándares de Django (Python 3.12+)
- **Type Hinting:** Es obligatorio el uso de tipos en todas las firmas de funciones y métodos.
- **Service Layer:** Prohibido escribir lógica de negocio compleja en `views.py` o `serializers.py`. Toda acción que modifique el estado del sistema debe residir en `services.py`.
- **Fat Models:** La lógica de datos pura (propiedades, métodos de instancia simples) va en `models.py`.
- **Managers Personalizados:** Usa `models.Manager` y `models.QuerySet` personalizados para encapsular filtros comunes (ej. `.activos()`, `.pendientes_aprobacion()`).

## 2. Optimización de PostgreSQL
- **Consultas N+1:** Antes de proponer código, verifica que no existan consultas N+1. Usa `select_related` para FK y `prefetch_related` para M2M.
- **Integridad:** - Usa `DecimalField` para valores monetarios o de precisión legal.
  - Implementa `db_index=True` en campos de búsqueda frecuente.
  - Usa `UniqueConstraint` y `CheckConstraint` para validaciones a nivel de base de datos.
- **Transacciones:** Usa `@transaction.atomic` para cualquier operación que involucre múltiples escrituras en la DB para garantizar la integridad.

## 4. Documentación y Estilo
- **Docstrings:** Usa formato Google Style para documentar clases y funciones.
- **Migrations:** Cada migración debe incluir un comentario explicativo si realiza cambios estructurales críticos.
- **Logging:** Registra acciones administrativas (Aprobaciones/Rechazos) usando el módulo `logging` de Python con el ID del actor.

## 5. Testing
- Genera tests unitarios con `pytest-django`.
- Prioriza el testeo de los `Services` y la lógica de transición de estados.