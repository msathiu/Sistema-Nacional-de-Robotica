# SNR-PRO: Sistema Nacional de Robótica 🤖 🇻🇪

![Django](https://img.shields.io/badge/Framework-Django%205.0-092e20?style=for-the-badge&logo=django)
![Bootstrap](https://img.shields.io/badge/Frontend-Bootstrap%205.3-7952b3?style=for-the-badge&logo=bootstrap)
![Docker](https://img.shields.io/badge/Container-Docker-2496ED?style=for-the-badge&logo=docker)
![Status](https://img.shields.io/badge/Status-En%20Desarrollo-green?style=for-the-badge)

**SNR-PRO** es la plataforma oficial para el **Sistema Nacional de
Robótica** y el **Registro Nacional de Semilleros Científicos**,
orientada a centralizar la gestión de participantes, instituciones,
eventos y proyectos tecnológicos a nivel nacional.

------------------------------------------------------------------------

## 🚀 Características Principales

### 💎 Interfaz Tech-Modern

-   Dashboards diferenciados por rol (Administrador, Institución,
    Participante)
-   KPIs dinámicos y estados de registro
-   Diseño responsive con estética tecnológica institucional

### 🛠 Gestión Centralizada

-   Registro y validación de instituciones
-   Padrón nacional de participantes
-   Gestión de eventos, convocatorias y proyectos
-   Control de estatus y trazabilidad de información

------------------------------------------------------------------------

## 🐳 Ejecución con Docker (Modo Recomendado)

### Requisitos

-   Docker
-   Docker Compose

### 1️⃣ Construir y levantar los servicios

``` bash
docker compose up --build
```

### 2️⃣ Acceder al sistema

Abrir en el navegador:

http://127.0.0.1:8000

------------------------------------------------------------------------

## 🧪 Ejecución Local (Modo Desarrollo Alternativo)

``` bash
source env/bin/activate
cd SistemaRegistro/
python manage.py runserver
```

------------------------------------------------------------------------

## 🛠 Tech Stack

-   Backend: Python 3.12 / Django 5.0
-   Frontend: Bootstrap 5.3, HTML5, CSS3, JavaScript
-   Base de Datos: SQLite3 / PostgreSQL
-   Infraestructura: Docker & Docker Compose

------------------------------------------------------------------------

## 📁 Estructura del Proyecto

Sistema-Nacional-de-Robótica/ - docker-compose.yml - Dockerfile - env/ -
SistemaRegistro/ - README.md

------------------------------------------------------------------------

## 🔧 Mejoras Recientes

El sistema ha sido optimizado con las siguientes mejoras:

- ✅ **Seguridad mejorada**: Eliminación de credenciales hardcodeadas y configuraciones de seguridad robustas
- ✅ **Optimización de base de datos**: 20+ índices agregados para consultas más rápidas
- ✅ **Sistema de logging**: Logs rotativos con niveles configurables
- ✅ **Validaciones mejoradas**: Validaciones más robustas en modelos y formularios
- ✅ **Utilidades comunes**: Funciones reutilizables para validaciones y operaciones comunes
- ✅ **Documentación completa**: Docstrings y comentarios en todo el código
- ✅ **Comando createsuperuser personalizado**: Asignación automática de tipo 'superusuario'
- ✅ **Sistema de ubicación en cascada**: Filtrado seguro Estado → Municipio → Parroquia
- ✅ **Control de aprobación de instituciones**: Sistema de aprobación manual con códigos temporales
- ✅ **Flujo de activación optimizado**: Códigos TEMP → RNR con envío automático de correos
- ✅ **Panel de gestión institucional**: Switch de activación con confirmación y envío de credenciales

📖 Ver detalles completos en [`MEJORAS_CODIGO.md`](MEJORAS_CODIGO.md)
📚 Consultar mejores prácticas en [`MEJORES_PRACTICAS.md`](MEJORES_PRACTICAS.md)
🗺️ Sistema de ubicación en cascada en [`IMPLEMENTACION_UBICACION_CASCADA.md`](IMPLEMENTACION_UBICACION_CASCADA.md)
🔐 Control de aprobación de instituciones en [`INDICE_STATUS_INSTITUCIONES.md`](INDICE_STATUS_INSTITUCIONES.md)

---

## 🔒 Correcciones de Seguridad (NUEVO)

Se han aplicado correcciones críticas de seguridad:

- 🔐 **Control de acceso robusto**: Decoradores personalizados para validación de permisos
- 🛡️ **Protección de endpoints**: Todos los endpoints AJAX requieren autenticación
- 🚫 **Rate limiting**: Límite de 60 peticiones/minuto por IP
- 🔑 **Credenciales seguras**: Variables de entorno obligatorias
- 🍪 **Cookies seguras**: HttpOnly, SameSite, Secure habilitados
- 📋 **Headers de seguridad**: XSS, Clickjacking, MIME sniffing protegidos
- ✔️ **Validación de entrada**: Sanitización y límites en todos los inputs
- 🔍 **Auditoría**: Logging de intentos sospechosos

🔒 **Documentación de seguridad:**
- [`CORRECCIONES_SEGURIDAD.md`](CORRECCIONES_SEGURIDAD.md) - Detalles técnicos completos
- [`GUIA_RAPIDA_SEGURIDAD.md`](GUIA_RAPIDA_SEGURIDAD.md) - Guía de implementación
- [`RESUMEN_EJECUTIVO_SEGURIDAD.md`](RESUMEN_EJECUTIVO_SEGURIDAD.md) - Resumen ejecutivo
- `verificar_seguridad.py` / `verificar_seguridad.bat` - Scripts de verificación

---

## 🚀 Configuración Inicial

### ⚠️ IMPORTANTE: Configuración de Seguridad

Antes de ejecutar el sistema, **DEBES** configurar las variables de entorno:

```bash
# 1. Copiar el archivo de ejemplo
cp .env.example .env

# 2. Generar SECRET_KEY única (OBLIGATORIO)
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# 3. Editar .env y configurar:
#    - SECRET_KEY (pegar la generada arriba)
#    - EMAIL_HOST_USER
#    - EMAIL_HOST_PASSWORD
#    - DEBUG=False (para producción)

# 4. Verificar configuración
python verificar_seguridad.py
# O en Windows:
verificar_seguridad.bat
```

### 1️⃣ Aplicar Migraciones

```bash
cd SistemaRegistro
python manage.py migrate
```

### 2️⃣ Crear Superusuario

```bash
python manage.py createsuperuser
# El sistema automáticamente asignará user_type='superuser' al perfil
```

### 3️⃣ Recolectar Archivos Estáticos

```bash
python manage.py collectstatic --noinput
```

---

## 📄 Licencia

Proyecto institucional supervisado por el MINCYT.
