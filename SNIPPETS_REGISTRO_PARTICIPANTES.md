# 📝 Snippets de Código - Registro de Participantes

## 🎯 Código JavaScript Principal

### 1. Lógica de Edad y Cédulas
```javascript
fechaNac.addEventListener('change', () => {
    const born = new Date(fechaNac.value);
    const now = new Date();
    let edad = now.getFullYear() - born.getFullYear();
    if (now.getMonth() < born.getMonth() || 
        (now.getMonth() === born.getMonth() && now.getDate() < born.getDate())) {
        edad--;
    }
    
    edadDisp.value = edad;
    edadHid.value = edad;

    // Validación de edad mínima (3 años)
    if (edad < 3) {
        document.getElementById('edad-error').classList.remove('d-none');
        document.getElementById('btnFinalizar').disabled = true;
    } else {
        document.getElementById('edad-error').classList.add('d-none');
        document.getElementById('btnFinalizar').disabled = false;
    }

    // Mostrar cédula escolar si edad <= 10 años
    if (edad <= 10 && edad >= 3) {
        cedulaEscolarCont.style.display = 'block';
        cedulaEscolarInput.required = true;
        cedulaPersonalInput.required = false;
    } else {
        cedulaEscolarCont.style.display = 'none';
        cedulaEscolarInput.required = false;
        cedulaPersonalInput.required = true;
    }

    // Mostrar sección de representante si es menor de 18
    if (edad >= 3 && edad < 18) {
        repSec.style.display = 'block';
        document.querySelectorAll('#representanteSection input, #representanteSection select')
            .forEach(i => i.required = true);
    } else {
        repSec.style.display = 'none';
        document.querySelectorAll('#representanteSection input, #representanteSection select')
            .forEach(i => i.required = false);
    }
});
```

### 2. Validación de Duplicados (AJAX)
```javascript
registroForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const nombres = document.querySelector('[name="nombres"]').value;
    const apellidos = document.querySelector('[name="apellidos"]').value;
    const fechaNacimiento = fechaNac.value;
    const cedulaPersonal = cedulaPersonalInput.value;
    const cedulaEscolar = cedulaEscolarInput.value;
    
    // Validar que tenga al menos una cédula
    if (!cedulaPersonal && !cedulaEscolar) {
        alert('Debe ingresar al menos una cédula (personal o escolar)');
        return;
    }
    
    // Verificar duplicados
    try {
        const response = await fetch('/verificar-participante/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({
                nombres,
                apellidos,
                fecha_nacimiento: fechaNacimiento,
                cedula_personal: cedulaPersonal,
                cedula_escolar: cedulaEscolar
            })
        });
        
        const data = await response.json();
        
        if (data.existe) {
            // Mostrar modal con datos del duplicado
            participanteDuplicadoId = data.participante_id;
            const datosDuplicado = `
                <strong>Nombres:</strong> ${data.datos.nombres}<br>
                <strong>Apellidos:</strong> ${data.datos.apellidos}<br>
                <strong>Fecha Nacimiento:</strong> ${data.datos.fecha_nacimiento}<br>
                <strong>Cédula:</strong> ${data.datos.cedula || 'N/A'}
            `;
            document.getElementById('datosDuplicado').innerHTML = datosDuplicado;
            const modal = new bootstrap.Modal(document.getElementById('modalDuplicado'));
            modal.show();
        } else {
            // No hay duplicados, enviar formulario
            registroForm.submit();
        }
    } catch (error) {
        console.error('Error al verificar duplicados:', error);
        // En caso de error, permitir continuar
        registroForm.submit();
    }
});
```

---

## 🐍 Código Python Principal

### 1. Vista de Verificación de Duplicados
```python
@login_required
@require_http_methods(["POST", "GET"])
def verificar_participante_duplicado(request):
    """
    Vista AJAX para verificar si existe un participante con datos similares.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            nombres = data.get('nombres', '').strip()
            apellidos = data.get('apellidos', '').strip()
            fecha_nacimiento = data.get('fecha_nacimiento')
            cedula_personal = data.get('cedula_personal', '').strip()
            cedula_escolar = data.get('cedula_escolar', '').strip()
            
            participante_existente = None
            
            # 1. Buscar por cédula personal
            if cedula_personal:
                nacionalidad = data.get('nacionalidad', 'V')
                cedula_completa = f"{nacionalidad}-{cedula_personal}"
                participante_existente = Participante.objects.filter(
                    cedula=cedula_completa
                ).first()
            
            # 2. Buscar por cédula escolar
            if not participante_existente and cedula_escolar:
                participante_existente = Participante.objects.filter(
                    cedula_escolar=cedula_escolar
                ).first()
            
            # 3. Buscar por nombres + apellidos + fecha de nacimiento
            if not participante_existente and nombres and apellidos and fecha_nacimiento:
                participante_existente = Participante.objects.filter(
                    nombres__iexact=nombres,
                    apellidos__iexact=apellidos,
                    fecha_nacimiento=fecha_nacimiento
                ).first()
            
            if participante_existente:
                return JsonResponse({
                    'existe': True,
                    'participante_id': participante_existente.id,
                    'datos': {
                        'nombres': participante_existente.nombres,
                        'apellidos': participante_existente.apellidos,
                        'fecha_nacimiento': participante_existente.fecha_nacimiento.strftime('%Y-%m-%d'),
                        'cedula': participante_existente.cedula,
                        'cedula_escolar': participante_existente.cedula_escolar
                    }
                })
            else:
                return JsonResponse({'existe': False})
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)
```

### 2. Lógica de Creación con Cédulas Separadas
```python
# En la vista crear_participante
try:
    with transaction.atomic():
        # 1. Obtener datos del formulario
        nacionalidad = request.POST.get('nacionalidad', 'V')
        cedula_personal = request.POST.get('cedula_personal', '').strip()
        cedula_escolar = request.POST.get('cedula_escolar', '').strip()
        
        # 2. Determinar cédula principal para el username
        if cedula_personal:
            cedula_completa = f"{nacionalidad}-{cedula_personal}"
            username = cedula_completa
        elif cedula_escolar:
            cedula_completa = f"E-{cedula_escolar}"
            username = cedula_completa
        else:
            messages.error(request, "Debe proporcionar al menos una cédula")
            return render(request, "users/register.html", context)

        # 3. Verificar si ya existe
        if User.objects.filter(username=username).exists():
            messages.error(request, f"Ya existe un usuario con el identificador {username}")
            return render(request, "users/register.html", context)

        # 4. Crear Usuario
        password_aleatoria = ''.join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(12)
        )
        user = User.objects.create_user(
            username=username,
            email=participante_form.cleaned_data.get("email"),
            password=password_aleatoria,
        )
        
        # 5. Crear perfil
        UserProfile.objects.get_or_create(
            user=user, defaults={"user_type": "participante"}
        )

        # 6. Preparar Participante
        participante = participante_form.save(commit=False)
        participante.user = user
        
        # Asignar cédulas
        participante.cedula = cedula_completa
        if cedula_escolar:
            participante.cedula_escolar = cedula_escolar
        
        # ... resto de la lógica
        participante.save()
        
        messages.success(request, f'✅ Participante registrado exitosamente.')
        return redirect("lista_participantes")

except Exception as e:
    messages.error(request, f"❌ Error crítico: {str(e)}")
```

---

## 📝 Validaciones en Formulario

### Validación en forms.py
```python
def clean(self):
    cleaned_data = super().clean()
    fecha_nac = cleaned_data.get("fecha_nacimiento")
    cedula_personal = self.data.get('cedula_personal', '').strip()
    cedula_escolar = self.data.get('cedula_escolar', '').strip()
    
    # Validar que tenga al menos una cédula
    if not cedula_personal and not cedula_escolar:
        raise ValidationError("Debe proporcionar al menos una cédula (personal o escolar).")
    
    if fecha_nac:
        today = date.today()
        edad = today.year - fecha_nac.year - ((today.month, today.day) < (fecha_nac.month, fecha_nac.day))
        
        # Validar cédula escolar para menores de 10 años
        if edad <= 10 and not cedula_escolar:
            raise ValidationError("La cédula escolar es obligatoria para menores de 10 años.")
        
        # Validar cédula personal para mayores de 10 años
        if edad > 10 and not cedula_personal:
            raise ValidationError("La cédula personal es obligatoria para mayores de 10 años.")
        
        # Lógica para Menores de Edad (< 18 años)
        if edad < 18:
            campos_rep = [
                'nombre_representante', 'cedula_representante', 
                'codigo_area_representante', 'numero_telefono_representante', 
                'email_representante'
            ]
            for campo in campos_rep:
                if not cleaned_data.get(campo):
                    self.add_error(campo, "Este campo es obligatorio para menores de edad.")
    
    return cleaned_data
```

---

## 🎨 HTML del Modal

```html
<!-- Modal de Registro Duplicado -->
<div class="modal fade" id="modalDuplicado" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content border-0 shadow-lg">
            <div class="modal-header bg-warning text-dark border-0">
                <h5 class="modal-title fw-bold">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    Registro Existente
                </h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body p-4">
                <p class="mb-3">Se encontró un registro con los siguientes datos:</p>
                <div class="alert alert-light border" id="datosDuplicado"></div>
                <p class="fw-bold">¿Es el mismo participante?</p>
            </div>
            <div class="modal-footer border-0">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                    No, continuar registro
                </button>
                <button type="button" class="btn btn-primary" id="btnIrEditar">
                    Sí, ir a editar
                </button>
            </div>
        </div>
    </div>
</div>
```

---

## 🔗 URL Pattern

```python
# En users/urls.py
urlpatterns = [
    # ... otras URLs
    path(
        "verificar-participante/",
        views.verificar_participante_duplicado,
        name="verificar_participante_duplicado",
    ),
    # ...
]
```

---

## 🧪 Casos de Prueba

### Test 1: Menor de 10 años
```python
# Datos de prueba
fecha_nacimiento = "2020-01-01"  # 4 años
cedula_escolar = "123456789"
cedula_personal = ""  # Vacío

# Resultado esperado
✅ Campo cédula escolar visible
✅ Campo cédula escolar obligatorio
✅ Sección representante visible
✅ Registro exitoso
```

### Test 2: Mayor de 10 años
```python
# Datos de prueba
fecha_nacimiento = "2010-01-01"  # 14 años
cedula_personal = "12345678"
cedula_escolar = ""  # Vacío

# Resultado esperado
✅ Campo cédula personal visible
✅ Campo cédula personal obligatorio
✅ Sección representante visible
✅ Registro exitoso
```

### Test 3: Duplicado por cédula
```python
# Paso 1: Registrar
cedula_personal = "12345678"
nombres = "Juan"
apellidos = "Pérez"

# Paso 2: Intentar registrar de nuevo
cedula_personal = "12345678"  # Misma cédula
nombres = "Pedro"  # Nombre diferente

# Resultado esperado
✅ Modal de duplicado aparece
✅ Muestra datos del primer registro
✅ Opciones: "Ir a editar" o "Continuar"
```

### Test 4: Duplicado por datos personales
```python
# Paso 1: Registrar
nombres = "Juan"
apellidos = "Pérez"
fecha_nacimiento = "2010-01-01"
cedula_personal = "11111111"

# Paso 2: Intentar registrar
nombres = "Juan"  # Mismo nombre
apellidos = "Pérez"  # Mismo apellido
fecha_nacimiento = "2010-01-01"  # Misma fecha
cedula_personal = "22222222"  # Cédula diferente

# Resultado esperado
✅ Modal de duplicado aparece
✅ Muestra datos del primer registro
✅ Usuario decide si es el mismo
```

---

## 🔍 Debugging

### Console.log útiles
```javascript
// Ver edad calculada
console.log('Edad calculada:', edad);

// Ver estado de campos
console.log('Cédula personal:', cedulaPersonalInput.value);
console.log('Cédula escolar:', cedulaEscolarInput.value);

// Ver respuesta del servidor
console.log('Respuesta verificación:', data);
```

### Print statements en Python
```python
# En la vista
print(f"Cédula personal recibida: {cedula_personal}")
print(f"Cédula escolar recibida: {cedula_escolar}")
print(f"Participante existente: {participante_existente}")
```

---

**Referencia rápida para desarrollo y debugging**
