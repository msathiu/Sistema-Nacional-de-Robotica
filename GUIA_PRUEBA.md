# 🧪 GUÍA DE PRUEBA - Nuevas Funcionalidades

## ✅ Archivos Verificados

Todos los archivos han sido creados exitosamente:

```
✓ users/management/commands/createsuperuser.py
✓ users/management/commands/__init__.py
✓ static/admin/js/userprofile_location.js
✓ templates/ejemplos/filtrado_cascada_ejemplo.html
✓ IMPLEMENTACION_UBICACION_CASCADA.md
✓ RESUMEN_IMPLEMENTACION_UBICACION.md
```

---

## 🚀 Pasos para Probar

### 1️⃣ Aplicar Migraciones

```bash
cd SistemaRegistro
python manage.py migrate
```

**Resultado esperado**: Las migraciones se aplican sin errores.

---

### 2️⃣ Recolectar Archivos Estáticos

```bash
python manage.py collectstatic --noinput
```

**Resultado esperado**: 
- Se copian los archivos JavaScript a `staticfiles/`
- Mensaje: "X static files copied to..."

---

### 3️⃣ Probar Comando Createsuperuser

```bash
python manage.py createsuperuser
```

**Pasos**:
1. Ingresar username: `admin_test`
2. Ingresar email: `admin@test.com`
3. Ingresar password (2 veces)

**Resultado esperado**:
```
Superuser created successfully.
Perfil de superusuario creado para admin_test
```

**Verificar**:
1. Ir a `/admin/`
2. Login con las credenciales creadas
3. Ir a **Users → User profiles**
4. Buscar el usuario `admin_test`
5. Verificar que `User type` = **Superusuario**

---

### 4️⃣ Probar Filtrado en Cascada en Admin

```bash
python manage.py runserver
```

**Pasos**:
1. Abrir navegador: `http://localhost:8000/admin/`
2. Login con superusuario
3. Ir a **Users → User profiles**
4. Click en **Add User Profile** (o editar uno existente)

**Prueba del filtrado**:

**Paso A - Seleccionar Estado**:
1. En el campo **Estado**, seleccionar "Distrito Capital"
2. **Resultado esperado**: 
   - El campo **Municipio** se habilita automáticamente
   - Se cargan solo los municipios de Distrito Capital
   - El campo **Parroquia** permanece deshabilitado

**Paso B - Seleccionar Municipio**:
1. En el campo **Municipio**, seleccionar un municipio
2. **Resultado esperado**:
   - El campo **Parroquia** se habilita automáticamente
   - Se cargan solo las parroquias de ese municipio

**Paso C - Seleccionar Parroquia**:
1. En el campo **Parroquia**, seleccionar una parroquia
2. Click en **Save**
3. **Resultado esperado**: El perfil se guarda correctamente

---

### 5️⃣ Verificar Seguridad de las APIs

**Prueba sin autenticación**:

Abrir una ventana de incógnito y probar:
```
http://localhost:8000/api/municipios/1/
```

**Resultado esperado**: 
```json
{"error": "No autorizado"}
```
Status: 403 Forbidden

**Prueba con autenticación**:

En la ventana donde estás logueado en el admin:
```
http://localhost:8000/api/municipios/1/
```

**Resultado esperado**:
```json
[
  {"id": 1, "nombre": "Libertador"},
  {"id": 2, "nombre": "Chacao"},
  ...
]
```
Status: 200 OK

---

## 🐛 Solución de Problemas

### Problema: El filtrado no funciona

**Solución**:
1. Abrir consola del navegador (F12)
2. Ir a la pestaña **Console**
3. Buscar errores de JavaScript
4. Verificar que jQuery esté cargado

**Verificar rutas**:
```bash
python manage.py show_urls | findstr api
```

Debe mostrar:
```
/api/municipios/<int:estado_id>/
/api/parroquias/<int:municipio_id>/
```

---

### Problema: Las APIs retornan 403

**Causa**: No estás autenticado

**Solución**:
1. Asegurarte de estar logueado en `/admin/`
2. Probar las APIs desde la misma ventana del navegador

---

### Problema: El comando createsuperuser no asigna el tipo

**Verificar que el archivo existe**:
```bash
dir SistemaRegistro\users\management\commands\createsuperuser.py
```

**Verificar que Django lo reconoce**:
```bash
python manage.py help createsuperuser
```

Debe mostrar: "Crea un superusuario con perfil de tipo superusuario"

---

## 📊 Checklist de Verificación

Marca cada item después de probarlo:

- [ ] Migraciones aplicadas sin errores
- [ ] Archivos estáticos recolectados
- [ ] Comando createsuperuser funciona
- [ ] Perfil creado con user_type='superuser'
- [ ] Filtrado en cascada funciona en admin
- [ ] Estado → Municipio carga correctamente
- [ ] Municipio → Parroquia carga correctamente
- [ ] API retorna 403 sin autenticación
- [ ] API retorna datos con autenticación
- [ ] Perfil se guarda correctamente con ubicación

---

## 🎯 Casos de Uso Adicionales

### Usar en Formularios Personalizados

Ver ejemplo completo en:
```
templates/ejemplos/filtrado_cascada_ejemplo.html
```

**Pasos para implementar**:
1. Copiar el código HTML del ejemplo
2. Copiar el JavaScript
3. En la vista, pasar `estados` al contexto:
   ```python
   from registry.models import Estado
   context = {'estados': Estado.objects.all().order_by('nombre')}
   ```

---

## 📞 Contacto y Soporte

Si encuentras algún problema:

1. **Revisar logs**:
   ```bash
   type logs\django.log
   ```

2. **Revisar consola del navegador**: F12 → Console

3. **Consultar documentación completa**:
   - `IMPLEMENTACION_UBICACION_CASCADA.md`
   - `RESUMEN_IMPLEMENTACION_UBICACION.md`

---

## ✅ Estado Final

**TODAS LAS FUNCIONALIDADES IMPLEMENTADAS Y LISTAS PARA USAR**

- ✅ Comando `createsuperuser` personalizado
- ✅ APIs seguras para ubicaciones
- ✅ JavaScript para filtrado en cascada
- ✅ Documentación completa
- ✅ Ejemplos de uso
- ✅ Scripts de verificación

**Próximo paso**: Ejecutar las pruebas siguiendo esta guía.

---

**Fecha**: 2025  
**Django**: 5.2.6  
**Estado**: ✅ LISTO PARA PROBAR
