# 🎓 Sistema de Gestión Académica

Este es el trabajo final de la materia Desarrollo de Sistemas Web, en el cual se pidio el desarrollo de un sistema web que simule la gestion academica de instituciones educativas mediante las tecnologias de Python con el framework Django.

Autor del proyecto:
Castellano Francisco.

A continuación una explicacion de lo que contiene el proyecto y como levantarlo localmente.
---

## 📋 Tabla de Contenidos

- [Características Principales](#-características-principales)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación y Configuración](#-instalación-y-configuración)
- [Comandos Útiles](#-comandos-útiles)
- [Usuarios de Prueba](#-usuarios-de-prueba)
- [Gestión de Base de Datos](#-gestión-de-base-de-datos)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Tecnologías Utilizadas](#-tecnologías-utilizadas)
- [Solución de Problemas](#-solución-de-problemas)

---

## ✨ Características Principales

### Control de Acceso por Roles
- **Administradores**: Acceso completo (CRUD de carreras, materias, alumnos, inscripciones)
- **Alumnos**: Visualización de materias de su carrera e inscripciones propias
- **Invitados**: Acceso público a carreras y materias sin necesidad de login

### Funcionalidades Destacadas
- ✅ Auto-generación de usuarios al crear alumnos (email: `DNI@universidad.edu`, password: `DNI`)
- ✅ Control de cupo máximo en materias con validación en tiempo real
- ✅ Inscripciones inteligentes: alumnos solo ven materias de su carrera
- ✅ 9 restricciones de integridad implementadas (delete protection, unique constraints, cupo limits)
- ✅ Validaciones HTML5 + Django con mensajes de error claros y emojis
- ✅ Interfaz Bootstrap 5 responsive con navegación adaptativa por roles
- ✅ Sistema POO: herencia en modelos (`Persona` → `Alumno`)
- ✅ Generación automática de legajos (formato: `{año}{codigo_carrera}{nro_secuencial}`)

---

## 🔧 Requisitos Previos

### Software Necesario

- **Python 3.11+** (recomendado 3.13)
- **pip** (gestor de paquetes de Python)
- **Git** (opcional, para clonar el repositorio)

### Verificar instalación

```powershell
python --version
# Debe mostrar: Python 3.13.x o superior

pip --version
# Debe mostrar la versión de pip
```

---

## 🚀 Instalación y Configuración

### 1. Clonar el proyecto desde GitHub

```powershell
# Clonar el repositorio
git clone https://github.com/frqn04/final-DW-3erA-o.git

# Entrar al directorio del proyecto
cd final-DW-3erA-o
```

**Alternativa:** Descargar como ZIP desde https://github.com/frqn04/final-DW-3erA-o y descomprimir.

### 2. Crear entorno virtual (recomendado)

```powershell
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Si da error de permisos, ejecutar primero:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Instalar dependencias

```powershell
pip install -r requirements.txt
```

**Dependencias incluidas:**
- Django 5.2.5
- django-bootstrap5 24.2
- django-filter 24.3
- django-tables2 2.7.0

### 4. Aplicar migraciones

```powershell
# Crear las migraciones (si no existen)
python manage.py makemigrations

# Aplicar migraciones a la base de datos
python manage.py migrate
```

### 5. Crear superusuario (administrador)

```powershell
python manage.py createsuperuser
```

Se solicitará:
- **Email**: `admin@universidad.edu` (o el que prefieras)
- **DNI**: `12345678` (exactamente 8 dígitos)
- **Contraseña**: La que desees (mínimo 8 caracteres)

### 6. Iniciar el servidor

```powershell
python manage.py runserver
```

El sistema estará disponible en: **http://127.0.0.1:8000/**

---

## 🎮 Comandos Útiles

### Gestión del Servidor

```powershell
# Iniciar servidor de desarrollo
python manage.py runserver

# Iniciar en puerto específico
python manage.py runserver 8080

# Iniciar accesible desde la red
python manage.py runserver 0.0.0.0:8000
```

### Gestión de Migraciones

```powershell
# Ver estado de migraciones
python manage.py showmigrations

# Crear nuevas migraciones después de cambios en models.py
python manage.py makemigrations

# Aplicar migraciones pendientes
python manage.py migrate

# Ver SQL que ejecutará una migración
python manage.py sqlmigrate users 0001

# Revertir una migración
python manage.py migrate users 0001
```

### Django Shell (Interactivo)

```powershell
# Abrir shell de Django
python manage.py shell

# Dentro del shell, puedes hacer consultas:
```

```python
# Ejemplos de uso del shell
from users.models import User
from escuelas.models import Carrera, Materia
from students.models import Alumno
from enrollments.models import Inscripcion

# Ver todos los usuarios
User.objects.all()

# Ver carreras
Carrera.objects.all()

# Ver materias de una carrera
ing = Carrera.objects.get(codigo='ING')
ing.materias.all()

# Ver inscripciones
Inscripcion.objects.all()

# Ver cupo disponible en una materia
materia = Materia.objects.get(codigo='DW')
materia.tiene_cupo_disponible()
materia.inscriptos_actuales()
```

### Verificación del Sistema

```powershell
# Verificar problemas de configuración
python manage.py check

# Verificar problemas de seguridad
python manage.py check --deploy

# Ver versión de Django
python -m django --version
```

---

## 👥 Usuarios de Prueba

El sistema viene con usuarios de prueba creados mediante el script de inicialización:

| Rol | Email | Password |
|-----|-------|----------|
| **Admin** | admin@escuela.edu | admin123 |
| **Alumno** | alumno@escuela.edu | alumno123 |
| **Invitado** | invitado@escuela.edu | invitado123 |

**Alumnos de prueba adicionales:**
- `10000001@universidad.edu` / `10000001`
- `10000002@universidad.edu` / `10000002`
- `10000003@universidad.edu` / `10000003`
- `10000004@universidad.edu` / `10000004`

### Acceso al Sistema

1. **Panel de Administración Django**: http://127.0.0.1:8000/admin/
   - Usuario: admin@escuela.edu
   - Contraseña: admin123

2. **Sistema Principal**: http://127.0.0.1:8000/
   - Puedes ingresar como cualquiera de los usuarios de prueba
   - O hacer clic en "Continuar como Invitado"

---

## 🗄️ Gestión de Base de Datos

### Inspeccionar la Base de Datos (SQLite)

```powershell
# Instalar DB Browser (opcional, GUI)
# Descargar desde: https://sqlitebrowser.org/

# O usar sqlite3 desde PowerShell
sqlite3 db.sqlite3
```

Dentro de sqlite3:
```sql
-- Ver todas las tablas
.tables

-- Ver estructura de una tabla
.schema users_user

-- Consultas SQL directas
SELECT * FROM users_user;
SELECT * FROM escuelas_carrera;
SELECT * FROM escuelas_materia;
SELECT * FROM students_alumno;
SELECT * FROM enrollments_inscripcion;

-- Salir
.quit
```

### Backup y Restauración

```powershell
# Crear backup de datos
python manage.py dumpdata > backup.json

# Crear backup por aplicación
python manage.py dumpdata users > backup_users.json
python manage.py dumpdata escuelas > backup_escuelas.json
python manage.py dumpdata students > backup_students.json
python manage.py dumpdata enrollments > backup_enrollments.json

# Restaurar desde backup
python manage.py loaddata backup.json

# Copiar base de datos (Windows)
Copy-Item db.sqlite3 db.sqlite3.backup
```

### Limpiar Base de Datos

```powershell
# CUIDADO: Esto borrará TODOS los datos
python manage.py flush

# Alternativa: eliminar y recrear
Remove-Item db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

### Ver Logs de Consultas SQL

En `escuela/settings.py`, agregar temporalmente:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

---

## 📁 Estructura del Proyecto

```
final-DW-3erA-o/
├── escuela/                # Configuración principal del proyecto
│   ├── settings.py        # Configuraciones de Django
│   ├── urls.py            # Enrutamiento principal
│   └── wsgi.py            # Servidor WSGI
├── core/                  # Funcionalidades centrales
│   ├── views.py           # Vista de inicio (HomeView)
│   └── urls.py            # URLs de core
├── users/                 # Sistema de autenticación
│   ├── models.py          # User personalizado con roles
│   ├── views.py           # Login, logout, registro
│   └── forms.py           # Formularios de autenticación
├── escuelas/              # Gestión de carreras y materias
│   ├── models.py          # Carrera, Materia
│   ├── views.py           # CRUD de carreras/materias
│   ├── filters.py         # MateriaFilter (búsquedas)
│   └── forms.py           # Formularios
├── students/              # Gestión de alumnos
│   ├── models.py          # Persona (abstracta), Alumno
│   ├── views.py           # CRUD de alumnos
│   └── forms.py           # AlumnoForm con auto-creación
├── enrollments/           # Sistema de inscripciones
│   ├── models.py          # Inscripcion
│   ├── views.py           # CRUD de inscripciones
│   └── forms.py           # InscripcionForm adaptativo
├── templates/             # Plantillas HTML
│   ├── base.html          # Template base con navbar
│   ├── home.html          # Página de inicio
│   └── [apps]/            # Templates por app
├── static/                # Archivos estáticos (CSS, JS, imágenes)
├── media/                 # Archivos subidos por usuarios
├── db.sqlite3             # Base de datos SQLite
├── manage.py              # Script de gestión de Django
├── requirements.txt       # Dependencias del proyecto
├── README.md              # Este archivo
└── GUIA_EXPLICATIVA.md    # Documentación técnica completa
```

---

## 🛠️ Tecnologías Utilizadas

### Backend
- **Django 5.2.5** - Framework web
- **Python 3.13** - Lenguaje de programación
- **SQLite** - Base de datos (desarrollo)

### Frontend
- **Bootstrap 5.3.0** - Framework CSS
- **Bootstrap Icons 1.11.3** - Iconos
- **django-bootstrap5** - Integración con Django

### Herramientas
- **django-filter** - Sistema de filtros
- **django-tables2** - Tablas dinámicas
- **Git** - Control de versiones

---

## 🐛 Solución de Problemas

### Error: "No module named django"

```powershell
# Verificar que el entorno virtual esté activado
.\venv\Scripts\Activate.ps1

# Reinstalar Django
pip install Django==5.2.5
```

### Error: "Port is already in use"

```powershell
# Usar otro puerto
python manage.py runserver 8080
```

### Error: "OperationalError: no such table"

```powershell
# Aplicar migraciones
python manage.py migrate
```

### Error: "ExecutionPolicy" en Windows

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Problemas con migraciones

```powershell
# Ver migraciones aplicadas
python manage.py showmigrations

# Simular migraciones sin aplicarlas
python manage.py migrate --fake-initial

# Revertir todas las migraciones y empezar de nuevo
python manage.py migrate users zero
python manage.py migrate escuelas zero
python manage.py migrate students zero
python manage.py migrate enrollments zero
python manage.py migrate
```

### Base de datos corrupta

```powershell
# Eliminar base de datos y recrear
Remove-Item db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

---

## 📚 Documentación Adicional

Para más información sobre el funcionamiento interno del sistema, arquitectura y flujos de trabajo, consultar:

📖 **[GUIA_EXPLICATIVA.md](GUIA_EXPLICATIVA.md)** - Documentación técnica completa

Este documento incluye:
- Explicación detallada de cada aplicación
- Diagramas de relaciones entre modelos
- Flujos de trabajo paso a paso
- Restricciones de integridad
- Conceptos de programación aplicados

---

## 🔗 Enlaces del Proyecto

- **Repositorio GitHub**: https://github.com/frqn04/final-DW-3erA-o
- **Clonar proyecto**: `git clone https://github.com/frqn04/final-DW-3erA-o.git`
- **Descargar ZIP**: https://github.com/frqn04/final-DW-3erA-o/archive/refs/heads/main.zip

---

## 👨‍💻 Autor

**Francisco Castellano**
- GitHub: [@frqn04](https://github.com/frqn04)
- Proyecto: Trabajo Final - Desarrollo de Sistemas Web

---

**Desarrollado con ❤️ usando Django 5.2.5 y Python 3.13**

*Sistema de Gestión Académica - Versión 1.0.0*



