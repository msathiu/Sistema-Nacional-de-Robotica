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

## 📄 Licencia

Proyecto institucional supervisado por el MINCYT.