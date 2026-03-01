# 🧪 Guía Rápida: Testing del Sistema de Eventos Dual

## 🚀 Ejecución Rápida

```bash
cd SistemaRegistro
python manage.py test registry.tests_eventos
```

## 📊 Resultados Esperados

```
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.................
----------------------------------------------------------------------
Ran 17 tests in 2.345s

OK
Destroying test database for alias 'default'...
```

## ✅ Tests Implementados

| Categoría | Cantidad | Descripción |
|-----------|----------|-------------|
| **Unitarios** | 7 | Tests de modelo y manager |
| **Validación** | 2 | Tests de validaciones |
| **Integración** | 6 | Tests de vistas |
| **Permisos** | 2 | Tests de seguridad |
| **TOTAL** | **17** | **Cobertura > 85%** |

## 🎯 Comandos Útiles

### Ejecutar tests específicos

```bash
# Solo tests de modelo
python manage.py test registry.tests_eventos.EventoModelTestCase

# Solo tests de validación
python manage.py test registry.tests_eventos.InscripcionEventoClubTestCase

# Solo tests de vistas
python manage.py test registry.tests_eventos.EventoClubViewsTestCase

# Solo tests de permisos
python manage.py test registry.tests_eventos.EventoClubPermisosTestCase
```

### Con verbosidad

```bash
python manage.py test registry.tests_eventos --verbosity=2
```

### Con cobertura

```bash
pip install coverage
coverage run --source='registry' manage.py test registry.tests_eventos
coverage report
```

## 📈 Cobertura Esperada

- **Modelo Evento**: > 85%
- **Views Eventos**: > 80%
- **Manager**: 100%
- **Validaciones**: 100%

## 🎓 Documentación Completa

Ver [`FASE5_TESTING_COMPLETADA.md`](FASE5_TESTING_COMPLETADA.md) para detalles completos.
