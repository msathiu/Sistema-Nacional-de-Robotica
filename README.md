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
- ✅ **Menús de navegación**: Enlaces contextuales en dashboards para gestión de eventos de club
- ✅ **Testing completo**: 17 tests unitarios y de integración con cobertura > 85%
- ✅ **Registro de participantes mejorado**: Validación inteligente de cédulas (personal/escolar) según edad
- ✅ **Detección de duplicados**: Sistema de verificación atómica con modal interactivo
- ✅ **Cédula escolar condicional**: Visible solo para menores de 10 años con validación automática
- ✅ **Cédulas solo números en BD**: Sistema robusto de limpieza y validación en múltiples capas (frontend/backend/modelo)

📖 Ver detalles completos en [`MEJORAS_CODIGO.md`](MEJORAS_CODIGO.md)  
📚 Consultar mejores prácticas en [`MEJORES_PRACTICAS.md`](MEJORES_PRACTICAS.md)  
🗺️ Sistema de ubicación en cascada en [`IMPLEMENTACION_UBICACION_CASCADA.md`](IMPLEMENTACION_UBICACION_CASCADA.md)  
🔒 Corrección de menús por roles en [`CORRECCION_MENUS_ROLES.md`](CORRECCION_MENUS_ROLES.md)  
🔐 Corrección de permisos por roles en [`CORRECCION_PERMISOS_ROLES.md`](CORRECCION_PERMISOS_ROLES.md)  
🔄 Sistema de reenvío de clubes en [`CORRECCION_REENVIO_CLUBES_RECHAZADOS.md`](CORRECCION_REENVIO_CLUBES_RECHAZADOS.md)  
🚀 Mejoras avanzadas implementadas en [`FASE2_REENVIO_CLUBES_IMPLEMENTADA.md`](FASE2_REENVIO_CLUBES_IMPLEMENTADA.md)  
🔔 Notificaciones de clubes pendientes en [`NOTIFICACIONES_CLUBES_PENDIENTES.md`](NOTIFICACIONES_CLUBES_PENDIENTES.md)  
🎯 Membresía automática para creadores en [`IMPLEMENTACION_MEMBRESIA_AUTOMATICA_CREADOR.md`](IMPLEMENTACION_MEMBRESIA_AUTOMATICA_CREADOR.md)  
📊 Corrección contador de instituciones en [`CORRECCION_CONTADOR_INSTITUCIONES.md`](CORRECCION_CONTADOR_INSTITUCIONES.md)  
🎭 Sistema de eventos dual en [`ARQUITECTURA_EVENTOS_DUAL.md`](ARQUITECTURA_EVENTOS_DUAL.md), [`FASE2_EVENTOS_CLUB_COMPLETADA.md`](FASE2_EVENTOS_CLUB_COMPLETADA.md), [`FASE3_TEMPLATES_EVENTOS_COMPLETADA.md`](FASE3_TEMPLATES_EVENTOS_COMPLETADA.md), [`FASE4_MENUS_NAVEGACION_COMPLETADA.md`](FASE4_MENUS_NAVEGACION_COMPLETADA.md), [`FASE5_TESTING_COMPLETADA.md`](FASE5_TESTING_COMPLETADA.md) y [`SISTEMA_EVENTOS_DUAL_COMPLETADO.md`](SISTEMA_EVENTOS_DUAL_COMPLETADO.md)  
📝 Mejoras en registro de participantes en [`MEJORAS_REGISTRO_PARTICIPANTES.md`](MEJORAS_REGISTRO_PARTICIPANTES.md), [`RESUMEN_MEJORAS_REGISTRO.md`](RESUMEN_MEJORAS_REGISTRO.md), [`SNIPPETS_REGISTRO_PARTICIPANTES.md`](SNIPPETS_REGISTRO_PARTICIPANTES.md), [`MEJORAS_CEDULAS_SOLO_NUMEROS.md`](MEJORAS_CEDULAS_SOLO_NUMEROS.md) y [`SNIPPETS_CEDULAS_SOLO_NUMEROS.md`](SNIPPETS_CEDULAS_SOLO_NUMEROS.md)

### 🗺️ Roadmap de Mejoras Futuras

**Fases Completadas**:
- ✅ Fase 1: Corrección Base de Reenvío de Clubes
- ✅ Fase 2: Mejoras Avanzadas (Límites, Checklist, Notificaciones)

**Fases Pendientes**:
- ⏳ Fase 3: Analytics y Reportes - [`FASE3_ANALYTICS_REPORTES_PENDIENTE.md`](FASE3_ANALYTICS_REPORTES_PENDIENTE.md)
- ⏳ Fase 4: Asistencia Inteligente - [`FASE4_ASISTENCIA_INTELIGENTE_PENDIENTE.md`](FASE4_ASISTENCIA_INTELIGENTE_PENDIENTE.md)

📋 Ver roadmap completo en [`ROADMAP_COMPLETO.md`](ROADMAP_COMPLETO.md)

---

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