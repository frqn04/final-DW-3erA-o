# 📚 Guía Explicativa del Sistema de Gestión Académica

## 🎯 Visión General del Proyecto

Este es un **Sistema de Gestión Académica** desarrollado en Django que permite gestionar carreras universitarias, materias, alumnos e inscripciones. El sistema implementa un control de acceso basado en roles (RBAC) con tres tipos de usuarios: **Administradores**, **Alumnos** e **Invitados**.

---

## 🏗️ Arquitectura del Proyecto

### Tecnologías Utilizadas
- **Django 5.2.5** - Framework web principal
- **Python 3.13** - Lenguaje de programación
- **SQLite** - Base de datos
- **Bootstrap 5.3** - Framework CSS para interfaz responsive
- **django-bootstrap5** - Integración de Bootstrap con formularios Django
- **django-filters** - Sistema de filtros para búsquedas
- **django-tables2** - Tablas HTML dinámicas

### Estructura de Aplicaciones

El proyecto sigue el patrón **MTV (Model-Template-View)** de Django y está dividido en **5 aplicaciones**:

```
escuela/                 # Configuración principal del proyecto
├── settings.py          # Configuración de Django
├── urls.py             # Enrutamiento principal
└── wsgi.py             # Servidor WSGI

core/                    # Funcionalidades centrales
├── views.py            # Vista de inicio (HomeView)
└── urls.py             # Ruta principal "/"

users/                   # Sistema de autenticación personalizado
├── models.py           # User personalizado con roles
├── views.py            # Login, logout, registro
└── forms.py            # Formularios de autenticación

escuelas/                # Gestión de carreras y materias
├── models.py           # Carrera, Materia
├── views.py            # CRUD de carreras y materias
├── filters.py          # MateriaFilter (búsquedas)
└── forms.py            # Formularios de carreras/materias

students/                # Gestión de alumnos
├── models.py           # Persona (abstracta), Alumno
├── views.py            # CRUD de alumnos
└── forms.py            # AlumnoForm con auto-creación de usuarios

enrollments/             # Sistema de inscripciones
├── models.py           # Inscripcion
├── views.py            # CRUD de inscripciones
└── forms.py            # InscripcionForm con lógica de roles
```

---

## 📦 Aplicaciones y su Funcionalidad

### 1️⃣ **CORE** - Centro del Sistema

**Propósito:** Proporciona la vista principal y funcionalidades compartidas.

**Componentes clave:**
- `HomeView`: Página de inicio que muestra tarjetas de acceso rápido según el rol del usuario
  - **Administradores:** Ven 4 tarjetas (Carreras, Materias, Alumnos, Inscripciones)
  - **Alumnos:** Ven 2 tarjetas (Materias, Inscripciones)
  - **Invitados:** Ven 2 tarjetas públicas (Carreras, Materias) sin necesidad de login

**Lógica destacada:**
- Acceso público sin autenticación requerida
- Interfaz adaptativa según permisos del usuario
- Diseño centrado con Bootstrap grid responsive

---

### 2️⃣ **USERS** - Sistema de Autenticación

**Propósito:** Gestionar usuarios con modelo personalizado y control de acceso basado en roles.

#### Modelo `User` (CustomUser)

Hereda de `AbstractUser` y agrega funcionalidad específica:

```python
ROLE_CHOICES = [
    ('ADMIN', 'Administrador'),      # Acceso total al sistema
    ('ALUMNO', 'Alumno'),            # Acceso limitado a sus datos
    ('INVITADO', 'Invitado'),        # Acceso público sin modificaciones
]
```

**Campos personalizados:**
- `email` (único) - Campo principal de autenticación
- `dni` (único, 8 dígitos) - Documento de identidad
- `role` - Determina los permisos del usuario
- `must_change_password` - Flag para forzar cambio de contraseña
- `password_changed_at` - Registro de cambios de contraseña

**Métodos útiles del modelo:**
```python
user.is_admin()      # ¿Es administrador?
user.is_alumno()     # ¿Es alumno?
user.is_invitado()   # ¿Es invitado?
```

#### Lógica de Autenticación

**UserManager personalizado:**
- `create_user()`: Crea usuarios normales con email y DNI
- `create_superuser()`: Crea administradores con permisos completos

**Proceso de Login:**
1. Usuario ingresa email/DNI y contraseña
2. Sistema valida credenciales
3. Redirección según rol:
   - Admin → Dashboard completo
   - Alumno → Vista de materias e inscripciones
   - Invitado → Acceso público

**Sistema de Logout:**
- Implementado con método POST (seguridad CSRF)
- Formulario en navbar con token CSRF

---

### 3️⃣ **ESCUELAS** - Carreras y Materias

**Propósito:** Gestionar la oferta académica (carreras y materias).

#### Modelo `Carrera`

Representa una carrera universitaria completa.

**Campos principales:**
- `codigo` (único) - Ej: "ING", "LIC", "TEC"
- `nombre` (único) - Ej: "Ingeniería en Sistemas"
- `duracion_años` - Duración de la carrera
- `activa` - Estado de la carrera

**Protección de integridad:**
```python
def delete(self):
    # No se puede eliminar si tiene materias asociadas
    if self.materias.exists():
        raise ValidationError('⛔ Tiene X materia(s) asociada(s)')
    # No se puede eliminar si tiene alumnos inscriptos
    if self.alumnos.exists():
        raise ValidationError('⛔ Tiene X alumno(s) inscripto(s)')
```

#### Modelo `Materia`

Representa una asignatura de una carrera.

**Campos principales:**
- `carrera` (ForeignKey) - Carrera a la que pertenece
- `nombre` - Nombre de la materia
- `codigo` - Código único dentro de la carrera
- `año_carrera` - Año en que se cursa (1, 2, 3...)
- `cupo_maximo` - Cantidad máxima de inscriptos
- `activa` - Estado de la materia

**Validaciones únicas:**
```python
unique_together = [['carrera', 'codigo'], ['carrera', 'nombre']]
```
No puede haber dos materias con el mismo código o nombre en la misma carrera.

**Métodos importantes:**
```python
def tiene_cupo_disponible():
    return self.inscriptos_actuales() < self.cupo_maximo

def inscriptos_actuales():
    return self.inscripciones.filter(estado='CURSANDO').count()
```

#### Vistas y Acceso

**Acceso PÚBLICO (sin login):**
- `CarreraListView`: Listar todas las carreras activas
- `CarreraDetailView`: Ver detalles de una carrera
- `MateriaListView`: Listar materias (filtradas por carrera si el usuario es alumno)
- `MateriaDetailView`: Ver detalles de una materia

**Acceso ADMIN (solo administradores):**
- Crear, editar, eliminar carreras
- Crear, editar, eliminar materias

**Filtros disponibles (MateriaFilter):**
- Por nombre (búsqueda parcial)
- Por carrera
- Por año de carrera
- Por estado (activa/inactiva)

---

### 4️⃣ **STUDENTS** - Gestión de Alumnos

**Propósito:** Administrar el registro de alumnos con POO (Programación Orientada a Objetos).

#### Modelo `Persona` (Clase Abstracta)

Implementa **herencia** en Django:

```python
class Persona(models.Model):
    first_name = models.CharField('Nombre')
    last_name = models.CharField('Apellido')
    dni = models.CharField(max_length=8, unique=True)
    email = models.EmailField(unique=True)
    
    class Meta:
        abstract = True  # No crea tabla en DB
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
```

#### Modelo `Alumno` (hereda de Persona)

Extiende `Persona` con datos académicos:

**Campos adicionales:**
- `user` (OneToOne) - Usuario asociado para login
- `legajo` (único) - Código de alumno autogenerado
- `carrera` (ForeignKey) - Carrera en la que está inscripto
- `fecha_ingreso` - Fecha de inicio
- `activo` - Estado del alumno

**Generación automática de legajo:**
```python
def save(self):
    if not self.legajo:
        # Formato: {año}{codigo_carrera}{nro_secuencial}
        # Ejemplo: 2025ING001
        año = timezone.now().year
        codigo_carrera = self.carrera.codigo
        ultimo_numero = ultimo_alumno_de_carrera + 1
        self.legajo = f"{año}{codigo_carrera}{ultimo_numero:03d}"
```

#### Formulario `AlumnoForm` - Auto-creación de Usuario

**Característica única:** Al crear un alumno, automáticamente se crea su cuenta de usuario.

**Proceso:**
1. Admin completa formulario con datos del alumno
2. Marca checkbox "Crear usuario automáticamente" (activado por defecto)
3. Sistema genera credenciales:
   - **Email:** `{DNI}@universidad.edu` (Ej: `12345678@universidad.edu`)
   - **Contraseña:** El DNI del alumno (Ej: `12345678`)
   - **Rol:** ALUMNO
   - **Flag:** `must_change_password=True`
4. Alumno puede iniciar sesión inmediatamente con sus credenciales

**Validaciones HTML5 del formulario:**
- DNI: `pattern="\d{8}"`, `minlength="8"`, `maxlength="8"`
- Mensajes de error con emojis: "⚠️ El DNI debe tener exactamente 8 dígitos. Ingresaste X dígito(s)."

**Vistas (solo ADMIN):**
- Listar alumnos
- Crear alumno (con auto-creación de usuario)
- Editar alumno
- Ver detalles de alumno
- Eliminar alumno (si no tiene inscripciones activas)

---

### 5️⃣ **ENROLLMENTS** - Sistema de Inscripciones

**Propósito:** Gestionar las inscripciones de alumnos a materias con validaciones de negocio.

#### Modelo `Inscripcion`

Relaciona alumnos con materias y controla su estado académico.

**Campos:**
- `alumno` (ForeignKey) - Alumno inscripto
- `materia` (ForeignKey) - Materia cursada
- `fecha_inscripcion` - Fecha de registro
- `estado` - Estado académico:
  - `CURSANDO` - Está cursando actualmente
  - `REGULAR` - Cursó pero no rindió final
  - `APROBADO` - Aprobó la materia
  - `DESAPROBADO` - No aprobó

**Restricciones únicas:**
```python
unique_together = [['alumno', 'materia']]
```
Un alumno no puede inscribirse dos veces a la misma materia.

#### Validaciones de Negocio (método `clean()`)

El sistema implementa **9 restricciones de integridad** verificadas antes de guardar:

**1. Verificación de alumno activo:**
```python
if not self.alumno.activo:
    raise ValidationError('El alumno no está activo.')
```

**2. Verificación de materia activa:**
```python
if not self.materia.activa:
    raise ValidationError('⚠️ La materia no está activa y no acepta inscripciones.')
```

**3. Prevención de inscripción duplicada:**
```python
if Inscripcion.objects.filter(alumno=self.alumno, materia=self.materia).exists():
    raise ValidationError('⚠️ El alumno ya está inscripto en esta materia.')
```

**4. Control de cupo máximo:**
```python
if not self.materia.tiene_cupo_disponible():
    raise ValidationError(
        f'⚠️ No hay cupo disponible en "{self.materia.nombre}". '
        f'Cupo máximo: {self.materia.cupo_maximo} | '
        f'Inscriptos actuales: {self.materia.inscriptos_actuales()}'
    )
```

#### Formulario `InscripcionForm` - Lógica por Roles

El formulario se adapta según quién lo use:

**Si el usuario es ADMINISTRADOR:**
- Ve todos los campos: alumno, materia, estado, observaciones
- Puede inscribir cualquier alumno a cualquier materia activa
- Tiene control completo del estado académico

**Si el usuario es ALUMNO:**
- **No ve campo `alumno`** (se asigna automáticamente)
- **No ve campo `estado`** (se asigna como 'CURSANDO')
- Solo ve materias de su propia carrera que estén activas
- Solo puede inscribirse a sí mismo

**Lógica del formulario:**
```python
def __init__(self, *args, **kwargs):
    self.user = kwargs.pop('user', None)
    
    if self.user.is_alumno():
        # Buscar el alumno asociado al usuario
        self.alumno_actual = Alumno.objects.get(user=self.user)
        
        # Remover campos
        self.fields.pop('alumno')
        self.fields.pop('estado')
        
        # Filtrar materias por su carrera
        self.fields['materia'].queryset = Materia.objects.filter(
            carrera=self.alumno_actual.carrera,
            activa=True
        )

def save(self, commit=True):
    inscripcion = super().save(commit=False)
    
    if self.user.is_alumno():
        inscripcion.alumno = self.alumno_actual
        inscripcion.estado = 'CURSANDO'
    
    if commit:
        inscripcion.save()
    return inscripcion
```

**Vistas:**
- `InscripcionListView`: Listar inscripciones (filtradas por alumno si no es admin)
- `InscripcionCreateView`: Crear inscripción (formulario adaptativo)
- `InscripcionDetailView`: Ver detalles
- `InscripcionUpdateView`: Editar estado (solo admin)
- `InscripcionDeleteView`: Eliminar inscripción

---

## 🔐 Sistema de Control de Acceso (RBAC)

### Mixins de Permisos

El proyecto usa **mixins personalizados** para controlar acceso:

**AdminRequiredMixin:**
```python
class AdminRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_admin():
            messages.error(request, '⛔ Acceso denegado: Solo los administradores pueden realizar esta acción.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
```

**AdminOrAlumnoMixin:**
```python
class AdminOrAlumnoMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_admin() or request.user.is_alumno()):
            messages.error(request, '⛔ Acceso denegado: Debes ser alumno o administrador.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
```

### Matriz de Permisos

| Funcionalidad | Admin | Alumno | Invitado |
|--------------|-------|--------|----------|
| Ver carreras | ✅ | ✅ | ✅ |
| Crear/Editar/Eliminar carreras | ✅ | ❌ | ❌ |
| Ver materias | ✅ | ✅ (solo su carrera) | ✅ |
| Crear/Editar/Eliminar materias | ✅ | ❌ | ❌ |
| Ver alumnos | ✅ | ❌ | ❌ |
| Crear/Editar/Eliminar alumnos | ✅ | ❌ | ❌ |
| Ver inscripciones | ✅ | ✅ (solo suyas) | ❌ |
| Crear inscripción | ✅ (cualquier alumno) | ✅ (solo a sí mismo) | ❌ |
| Eliminar inscripción (darse de baja) | ✅ | ✅ (solo las propias) | ❌ |
| Editar estado de inscripción | ✅ | ❌ | ❌ |

### Navegación Adaptativa

**Navbar según rol:**

```django
{% if user.is_authenticated %}
    {% if user.is_admin %}
        <!-- Admin ve: Carreras, Materias, Alumnos, Inscripciones -->
    {% elif user.is_alumno %}
        <!-- Alumno ve: Materias, Inscripciones -->
    {% endif %}
{% else %}
    <!-- Invitado ve: Carreras, Materias, Login -->
{% endif %}
```

---

## 🎨 Características de UX/UI

### Mensajes de Error Mejorados

Todos los mensajes usan **emojis** para mejor visualización:

- ✅ - Operación exitosa
- ⚠️ - Advertencia / Validación
- ⛔ - Acceso denegado / Error crítico
- 📧 - Información de email
- 🔑 - Información de contraseña

**Ejemplos:**
```python
# Error de validación
"⚠️ El DNI debe tener exactamente 8 dígitos. Ingresaste 7 dígito(s)."

# Error de cupo
"⚠️ No hay cupo disponible en 'Bases de Datos I'. Cupo máximo: 25 | Inscriptos actuales: 25"

# Error de permisos
"⛔ Acceso denegado: Solo los administradores pueden realizar esta acción."

# Éxito al crear alumno
"✅ Alumno 'Juan Pérez' creado exitosamente. 📧 Email: 12345678@universidad.edu | 🔑 Contraseña: 12345678"
```

### Validaciones HTML5

Formularios con validación en el cliente:

```html
<input type="text" name="dni"
       pattern="\d{8}"
       maxlength="8"
       minlength="8"
       placeholder="12345678"
       title="Ingrese exactamente 8 dígitos numéricos"
       required>
```

### Interfaz Bootstrap Responsive

- **Grid system** responsive (col-md-6, col-lg-4)
- **Cards** con sombras y hover effects
- **Iconos Bootstrap Icons** para acciones
- **Alerts** con colores semánticos (success, warning, danger)
- **Tables** responsive con striped rows
- **Forms** con labels flotantes y validación visual

---

## 🔄 Flujos de Trabajo Principales

### Flujo 1: Administrador crea un alumno

1. Admin hace login con `admin@escuela.edu`
2. Navega a "Alumnos" → "Crear Alumno"
3. Completa el formulario:
   - Nombre: Juan
   - Apellido: Pérez
   - DNI: 12345678 (exactamente 8 dígitos)
   - Carrera: Ingeniería en Sistemas
   - Fecha de ingreso: 2025-03-01
   - ✅ Crear usuario automáticamente
4. Hace clic en "Guardar"
5. Sistema:
   - Crea registro de `Alumno`
   - Genera legajo: `2025ING001`
   - Crea `User` con:
     - Email: `12345678@universidad.edu`
     - Password: `12345678`
     - Role: `ALUMNO`
   - Vincula User con Alumno
6. Muestra mensaje: "✅ Alumno 'Juan Pérez' creado exitosamente. 📧 Email: 12345678@universidad.edu | 🔑 Contraseña: 12345678"

### Flujo 2: Alumno se inscribe a una materia

1. Alumno hace login con `12345678@universidad.edu` / `12345678`
2. Ve página de inicio con opciones: "Materias" e "Inscripciones"
3. Hace clic en "Materias"
4. Ve lista de materias **solo de su carrera** (Ingeniería en Sistemas)
5. Puede filtrar por año, nombre, etc.
6. Hace clic en "Inscripciones" → "Nueva Inscripción"
7. Ve formulario simplificado:
   - ❌ No ve campo "Alumno" (se asigna automáticamente)
   - ❌ No ve campo "Estado" (se asigna como 'CURSANDO')
   - ✅ Ve solo materias de su carrera activas
8. Selecciona "Algoritmos y Estructuras de Datos"
9. Hace clic en "Guardar"
10. Sistema valida:
    - ✅ Alumno activo
    - ✅ Materia activa
    - ✅ No inscripto anteriormente
    - ✅ Hay cupo disponible (Ej: 15/30)
11. Crea inscripción con estado 'CURSANDO'
12. Muestra mensaje: "✅ Inscripción creada exitosamente."

### Flujo 3: Invitado explora carreras sin cuenta

1. Invitado accede a la URL del sistema
2. Ve página de inicio sin estar autenticado
3. Ve 2 opciones:
   - "Ver Carreras"
   - "Ver Materias"
   - "Ingresar" (botón de login)
   - "Continuar como Invitado" (botón destacado)
4. Hace clic en "Ver Carreras"
5. Ve lista completa de carreras activas con:
   - Código, nombre, duración
   - Botón "Ver Detalles" (sin opciones de edición)
6. Hace clic en una carrera
7. Ve detalles: código, nombre, duración, descripción, materias asociadas
8. Puede navegar a materias desde ahí
9. En cualquier momento puede hacer clic en "Ingresar" para crear cuenta/loguearse

### Flujo 4: Control de cupo en inscripciones

1. Materia "Bases de Datos I" tiene `cupo_maximo = 25`
2. Ya hay 25 alumnos inscriptos en estado 'CURSANDO'
3. Alumno 26 intenta inscribirse
4. Sistema ejecuta `clean()`:
   ```python
   if not self.materia.tiene_cupo_disponible():
       # inscriptos_actuales() = 25
       # cupo_maximo = 25
       # tiene_cupo_disponible() = False
       raise ValidationError(...)
   ```
5. Muestra error: "⚠️ No hay cupo disponible en 'Bases de Datos I'. Cupo máximo: 25 | Inscriptos actuales: 25"
6. Inscripción **no se crea**
7. Alumno ve el mensaje y puede elegir otra materia

---

## 📊 Diagramas de Relaciones

### Relación entre Modelos

```
User (1) ←→ (0..1) Alumno (N) → (1) Carrera (1) → (N) Materia
                      ↓                                  ↑
                      └──────── (N) Inscripcion (N) ────┘
```

**Explicación:**
- 1 User puede tener 0 o 1 Alumno asociado (OneToOne opcional)
- 1 Alumno pertenece a 1 Carrera (ForeignKey)
- 1 Carrera tiene N Materias (ForeignKey inverso)
- 1 Alumno tiene N Inscripciones (ForeignKey inverso)
- 1 Materia tiene N Inscripciones (ForeignKey inverso)
- Inscripcion es una tabla intermedia entre Alumno y Materia (N:N con datos adicionales)

### Protecciones CASCADE y PROTECT

```python
# Carrera → Materia (PROTECT)
# No se puede eliminar carrera si tiene materias

# Carrera → Alumno (PROTECT)
# No se puede eliminar carrera si tiene alumnos

# Materia → Inscripcion (PROTECT)
# No se puede eliminar materia si tiene inscripciones

# Alumno → Inscripcion (CASCADE)
# Si se elimina alumno, se eliminan sus inscripciones

# User → Alumno (CASCADE)
# Si se elimina usuario, se elimina su registro de alumno
```

---

## 🛡️ Restricciones de Integridad Implementadas

### Las 9 Restricciones del Sistema

**1. Eliminación de Carrera con Materias:**
```python
# escuelas/models.py - Carrera.delete()
if self.materias.exists():
    raise ValidationError('⛔ No se puede eliminar...')
```

**2. Eliminación de Carrera con Alumnos:**
```python
# escuelas/models.py - Carrera.delete()
if self.alumnos.exists():
    raise ValidationError('⛔ No se puede eliminar...')
```

**3. Eliminación de Materia con Inscripciones:**
```python
# escuelas/models.py - Materia.delete()
if self.inscripciones.exists():
    raise ValidationError('⛔ No se puede eliminar...')
```

**4. DNI único de Alumno:**
```python
# students/models.py - Persona
dni = models.CharField(max_length=8, unique=True)
```

**5. Email único de Alumno:**
```python
# students/models.py - Persona
email = models.EmailField(unique=True)
```

**6. Código único de Materia por Carrera:**
```python
# escuelas/models.py - Materia.Meta
unique_together = [['carrera', 'codigo']]
```

**7. Nombre único de Materia por Carrera:**
```python
# escuelas/models.py - Materia.Meta
unique_together = [['carrera', 'nombre']]
```

**8. Inscripción única (Alumno + Materia):**
```python
# enrollments/models.py - Inscripcion.Meta
unique_together = [['alumno', 'materia']]
```

**9. Control de Cupo Máximo:**
```python
# enrollments/models.py - Inscripcion.clean()
if not self.materia.tiene_cupo_disponible():
    raise ValidationError('⚠️ No hay cupo disponible...')
```

---

## 🧪 Testing y Validación

### Scripts de Prueba Ejecutados

**test_restricciones.py:**
- Verificó las 8 primeras restricciones
- Intentó violaciones de integridad
- Confirmó que todas las validaciones funcionan

**crear_prueba_cupo.py:**
- Creó 4 alumnos de prueba
- Creó materia con cupo 3
- Inscribió 3 alumnos (cupo lleno)
- Intentó inscribir 4to alumno → Bloqueado ✅

**Datos de prueba creados:**
- Usuarios: `10000001@universidad.edu` a `10000004@universidad.edu`
- Contraseñas: Mismo que el DNI (10000001, 10000002, etc.)
- Materia: "Materia de Prueba - Cupo Limitado" (cupo: 3)
- Estado: 3 inscripciones activas, cupo completo

---

## 🚀 Puntos Destacables para el Video

### 1. **Auto-generación de Usuarios**
Mostrar cómo al crear un alumno se genera automáticamente su cuenta con email `{DNI}@universidad.edu` y contraseña igual al DNI.

### 2. **Control de Acceso por Roles**
Demostrar cómo la interfaz cambia según el usuario (admin vs alumno vs invitado).

### 3. **Acceso Público sin Login**
Mostrar que cualquier persona puede ver carreras y materias sin necesidad de crear cuenta.

### 4. **Inscripción Inteligente**
Demostrar cómo un alumno solo ve materias de su carrera y no puede inscribir a otros alumnos.

### 5. **Control de Cupo en Tiempo Real**
Mostrar el error de "No hay cupo disponible" con contador exacto de inscriptos.

### 6. **Validaciones con Emojis**
Destacar los mensajes de error amigables con emojis y contadores específicos.

### 7. **Protecciones de Integridad**
Intentar eliminar una carrera con materias asociadas para mostrar el error protector.

### 8. **POO en Modelos**
Explicar la herencia `Persona → Alumno` como ejemplo de buenas prácticas.

### 9. **Filtros Dinámicos**
Usar el MateriaFilter para buscar por carrera, año, nombre, etc.

### 10. **Diseño Responsive**
Mostrar la interfaz en diferentes tamaños de pantalla (desktop, tablet, mobile).

---

## 📝 Resumen de Ventajas del Sistema

✅ **Seguridad:** Control de acceso por roles, validaciones en múltiples capas  
✅ **Usabilidad:** Interfaz intuitiva con Bootstrap, mensajes claros  
✅ **Integridad:** 9 restricciones de negocio implementadas  
✅ **Automatización:** Generación de usuarios, legajos, validaciones  
✅ **Accesibilidad:** Sistema público para invitados sin barreras  
✅ **Escalabilidad:** Arquitectura modular con apps independientes  
✅ **Mantenibilidad:** Código limpio con POO, comentarios, docstrings  
✅ **Testing:** Validado con scripts de prueba exhaustivos  

---

## 🎓 Conceptos de Programación Aplicados

- **POO:** Herencia (Persona → Alumno), Encapsulación, Métodos de clase
- **MVC/MTV:** Separación de responsabilidades (Models, Templates, Views)
- **DRY:** Mixins reutilizables, formularios compartidos
- **Validación en capas:** HTML5 → Django Forms → Django Models → Database
- **CRUD completo:** Create, Read, Update, Delete para todas las entidades
- **Foreign Keys:** Relaciones entre modelos con protecciones
- **Signals:** (Potencial) Para acciones automatizadas post-save
- **Querysets optimizados:** `select_related()`, `prefetch_related()`
- **Filtros dinámicos:** django-filters para búsquedas avanzadas
- **Autenticación custom:** UserManager, AbstractUser personalizado

---

## 💡 Mejoras Futuras Sugeridas

1. **Dashboard con gráficos:** Estadísticas de inscripciones, cupos disponibles
2. **Sistema de notificaciones:** Alertas cuando se libere cupo en una materia
3. **Historial académico:** Ver materias aprobadas, promedio, etc.
4. **Exportación de datos:** PDF de certificados, Excel de inscriptos
5. **Calendario académico:** Fechas de exámenes, entregas
6. **Foros por materia:** Comunicación entre alumnos de la misma materia
7. **Subida de archivos:** Programas de materias, apuntes
8. **API REST:** Para integración con apps móviles
9. **Autenticación con DNI:** Implementar DualAuthBackend para login con DNI
10. **Middleware de cambio de contraseña:** Forzar cambio en primer login

---

**¡Sistema completo y funcional listo para demostración! 🎉**
