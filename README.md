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
- ✅ **Menús por roles**: Menús de dashboard adaptados según permisos de usuario
- ✅ **Permisos corregidos**: Acceso correcto a Papelera, Métricas y Notificaciones por rol
- ✅ **Sistema de reenvío de clubes**: Ciclo completo de corrección y reenvío con límites y notificaciones
- ✅ **Notificaciones de clubes pendientes**: Badge en tiempo real para federación con caché optimizado
- ✅ **Membresía automática para creadores**: Institución creadora es miembro coordinador al aprobar club
- ✅ **Contador de instituciones corregido**: Cálculo preciso de instituciones participantes únicas
- ✅ **Sistema de eventos dual**: Eventos institucionales + eventos de club con aprobación de federación
- ✅ **Arquitectura de eventos mejorada**: Campo `audiencia` con 3 niveles (pública, club exclusivo, privado) y flujo de aprobación unificado
- ✅ **Menús de navegación**: Enlaces contextuales en dashboards para gestión de eventos de club
- ✅ **Testing completo**: 17 tests unitarios y de integración con cobertura > 85%
- ✅ **Registro de participantes mejorado**: Validación inteligente de cédulas (personal/escolar) según edad
- ✅ **Detección de duplicados**: Sistema de verificación atómica con modal interactivo
- ✅ **Cédula escolar condicional**: Visible solo para menores de 10 años con validación automática
- ✅ **Cédulas solo números en BD**: Sistema robusto de limpieza y validación en múltiples capas (frontend/backend/modelo)
- ✅ **Editar participante mejorado**: Diseño moderno y funcionalidad completa idéntica a crear participante
- ✅ **Guardado correcto de cédulas**: Corrección del flujo de guardado de cédula personal y escolar en base de datos
- ✅ **Modal de expediente completo**: Vista detallada con 17 campos organizados en 4 secciones (Datos Personales, Ubicación, Educación, Representante)
- ✅ **Exportación a Excel mejorada**: Exporta todos los datos de participantes (19 campos) con formato legible y profesional
- ✅ **Registro de tutores mejorado**: Campos de nacionalidad (V/E) y código de área del teléfono con validaciones robustas
- ✅ **Sistema de gestión de equipos**: Registro profesional con código automático, búsqueda inteligente de tutores/participantes y registro dinámico
- ✅ **Vista de detalle de equipo enriquecida**: Información completa con detalles de criterios, navegación mejorada y diseño profesional
- ✅ **Editar equipo modernizado**: Diseño consistente con crear equipo, interfaz moderna y funcionalidad completa
- ✅ **Registro de personas naturales**: Sistema completo para registrar particulares con validación atómica de cédula, campos dinámicos y autocompletado
- ✅ **Arquitectura multi-institución para Tutores**: Sistema completo que permite tutores vinculados a múltiples instituciones con estados independientes
- ✅ **Arquitectura multi-institución para Participantes**: Reestructuración completa del modelo Participante para soportar vinculaciones múltiples con estados independientes por institución
## 🚀 Configuración Inicial

### 1️⃣ Configurar Variables de Entorno

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar .env con tus configuraciones
# IMPORTANTE: Generar una SECRET_KEY única
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 2️⃣ Aplicar Migraciones

```bash
cd SistemaRegistro
python manage.py migrate
```

### 3️⃣ Crear Superusuario

```bash
python manage.py createsuperuser
# El sistema automáticamente asignará user_type='superuser' al perfil
```

### 4️⃣ Recolectar Archivos Estáticos

```bash
python manage.py collectstatic --noinput
```

---

## 📄 Licencia

Proyecto institucional supervisado por el MINCYT.