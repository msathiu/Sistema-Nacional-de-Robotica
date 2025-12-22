# SNR-PRO: Sistema Nacional de Robótica 🤖 🇻🇪

![Django](https://img.shields.io/badge/Framework-Django%205.0-092e20?style=for-the-badge&logo=django)
![Bootstrap](https://img.shields.io/badge/Frontend-Bootstrap%205.3-7952b3?style=for-the-badge&logo=bootstrap)
![Status](https://img.shields.io/badge/Status-En%20Desarrollo-green?style=for-the-badge)

**SNR-PRO** es la plataforma oficial para el **Registro Nacional de Semilleros Científicos**. Este sistema centraliza la gestión de participantes, instituciones y eventos de robótica a nivel nacional, proporcionando herramientas analíticas para el seguimiento del desarrollo tecnológico juvenil en Venezuela.

## 🚀 Características Principales

### 💎 Interfaz "Tech-Modern"
* **Dashboards Diferenciados:** Paneles específicos con lógica de acceso para Administradores, Instituciones y Participantes.
* **Visualización de Datos:** KPIs dinámicos con animaciones de contadores, estados de registro y mapas interactivos.
* **Diseño Adaptativo:** Basado en una estética futurista "Tech" con componentes optimizados para la gestión masiva de datos.

### 🛠 Funcionalidades de Gestión
* **Módulo Institucional:** Registro automatizado de sedes con validación de código SNR y activación por parte de entes rectores.
* **Padrón de Participantes:** Base de datos robusta con filtros avanzados (género, edad, estado) y perfiles detallados.
* **Gestión de Eventos:** Centro de control para crear convocatorias, monitorear proyectos inscritos y administrar estatus de competencia.

---

## ⚙️ Guía de Inicio Rápido

Sigue estos comandos en tu terminal para poner en marcha el sistema en tu entorno local:

### 1. Preparar el Entorno
Desde la raíz del repositorio, activa el entorno virtual de Python:
```bash
source env/bin/activate
```

### 2. Acceder al Proyecto
Entra en la carpeta raíz del código fuente de Django:
```bash
cd SistemaRegistro/
```

### 3. Ejecutar el Servidor
Inicia el servicio de desarrollo local:
```bash
python manage.py runserver
```

Luego, accede mediante tu navegador a: http://127.0.0.1:8000

---

## 🛠 Tech Stack
**Backend:** Python 3.12+ / Django 5.0  
**Frontend:** HTML5, CSS3 (Custom Tech UI), JavaScript (ES6+)  
**UI/UX:** Bootstrap 5.3 + Bootstrap Icons  
**Base de Datos:** PostgreSQL (Producción) / SQLite3 (Desarrollo)

---

## 📁 Estructura del Proyecto
```plaintext
SNR-PRO/
├── env/                # Entorno virtual de Python (Dependencias)
├── SistemaRegistro/    # Carpeta raíz del proyecto Django
│   ├── core/           # Configuración central (settings, urls)
│   ├── registry/       # App de lógica de negocio (Participantes, Eventos)
│   ├── users/          # App de gestión de usuarios, perfiles y dashboards
│   ├── templates/      # Vistas HTML con diseño Tech-Modern
│   ├── static/         # Archivos estáticos (CSS, JS, Imágenes)
│   └── manage.py       # Script de administración de Django
└── README.md           # Documentación del proyecto
```

---

## 📄 Licencia
Este proyecto es de uso institucional bajo la supervisión del Ministerio del Poder Popular para la Ciencia y la Tecnología (MINCYT).  
Queda prohibida su reproducción total o parcial sin autorización.

---
