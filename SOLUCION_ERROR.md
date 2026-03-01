# 🔧 SOLUCIÓN RÁPIDA AL ERROR

## Error Encontrado
```
ProgrammingError: column registry_evento.tipo does not exist
```

## Causa
Las migraciones no se han aplicado a la base de datos.

## Solución

### Opción 1: Usando Docker (Recomendado)

```bash
# Detener los contenedores
docker compose down

# Aplicar migraciones
docker compose run web python manage.py migrate

# Levantar de nuevo
docker compose up
```

### Opción 2: Comando directo

```bash
docker compose exec web python manage.py migrate
```

### Opción 3: Entrar al contenedor

```bash
# Entrar al contenedor
docker compose exec web bash

# Dentro del contenedor
cd /app
python manage.py migrate

# Salir
exit
```

## Verificar que funcionó

```bash
docker compose exec web python manage.py showmigrations registry
```

Deberías ver:
```
registry
 [X] 0001_initial
 [X] 0002_club
 ...
 [X] 0011_sistema_institucional  ← Esta debe tener [X]
```

## Si persiste el error

### Resetear la base de datos (CUIDADO: Borra todos los datos)

```bash
# Detener contenedores
docker compose down -v

# Eliminar volúmenes
docker volume prune

# Levantar de nuevo (creará BD nueva)
docker compose up --build

# Aplicar migraciones
docker compose exec web python manage.py migrate

# Crear superusuario
docker compose exec web python manage.py createsuperuser
```

## Instalar Pillow (para imágenes de clubes)

```bash
# Agregar a requirements.txt
echo "Pillow>=10.0.0" >> SistemaRegistro/requirements.txt

# Reconstruir imagen
docker compose build

# Reiniciar
docker compose up
```

## Verificar que todo funciona

1. Ir a: http://localhost:8000/login/
2. Ingresar con usuario institucional
3. Debería cargar el dashboard sin errores
