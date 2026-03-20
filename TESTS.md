# Guia De Tests

## Estructura

Los tests quedaron organizados por app y por dominio funcional:

- `SistemaRegistro/registry/tests/eventos/`
- `SistemaRegistro/registry/tests/grupos/`
- `SistemaRegistro/registry/tests/tutores/`
- `SistemaRegistro/users/tests/general/`

## Recomendacion

Ejecuta los tests desde Docker para usar el mismo entorno del sistema:

```bash
docker compose exec web python manage.py test
```

## Comandos Utiles

Todos los tests:

```bash
docker compose exec web python manage.py test
```

Todos los tests de `registry`:

```bash
docker compose exec web python manage.py test registry
```

Todos los tests de eventos:

```bash
docker compose exec web python manage.py test registry/tests/eventos
```

Todos los tests de grupos:

```bash
docker compose exec web python manage.py test registry/tests/grupos
```

Todos los tests de tutores:

```bash
docker compose exec web python manage.py test registry/tests/tutores
```

Un archivo especifico:

```bash
docker compose exec web python manage.py test registry.tests.grupos.test_grupos_permisos
```

Una clase especifica:

```bash
docker compose exec web python manage.py test registry.tests.grupos.test_grupos_permisos.GruposPermisosFederacionTestCase
```

Un test especifico:

```bash
docker compose exec web python manage.py test registry.tests.grupos.test_grupos_permisos.GruposPermisosFederacionTestCase.test_fed_central_lista_grupos_sin_acciones_de_edicion
```

Tests del app `users`:

```bash
docker compose exec web python manage.py test users
```

## Convencion

- Usa nombres `test_*.py`.
- Agrupa nuevos tests en la carpeta del dominio que corresponda.
- Si agregas un dominio nuevo, crea su subcarpeta dentro de `tests/` con su `__init__.py`.
- Prefiere imports absolutos como `from registry.models import ...`.
- Para correr una carpeta completa, en este proyecto funciona mejor usar la ruta fisica, por ejemplo `registry/tests/grupos`.

## Notas

- Algunas corridas pueden mostrar logs de migraciones o señales; eso no implica fallo si el resultado final termina en `OK`.
- Si quieres acelerar una validacion, corre primero solo el modulo relacionado con el cambio que hiciste.
