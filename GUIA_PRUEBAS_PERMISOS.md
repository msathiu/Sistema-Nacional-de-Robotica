# 🧪 Guía de Pruebas: Correcciones de Permisos

## 📋 Preparación

```bash
# 1. Reiniciar el servidor
cd SistemaRegistro
python manage.py runserver

# 2. Abrir navegador en modo incógnito
# Chrome: Ctrl + Shift + N
# Firefox: Ctrl + Shift + P
```

---

## 🧑💼 Prueba 1: Fed. Central - Papelera

### Datos de Prueba
```
Usuario: [usuario_fed_central]
Rol: fed_central
```

### Pasos:
1. **Iniciar sesión** con usuario Fed. Central
2. **Verificar menú lateral:**
   - [ ] ✅ Debe aparecer "Papelera"
3. **Hacer clic en "Papelera"**
4. **Verificar resultado:**
   - [ ] ✅ Debe cargar la página sin errores
   - [ ] ✅ Debe mostrar lista de clubes eliminados
   - [ ] ✅ Debe tener botones "Restaurar" y "Eliminar Permanente"

### Prueba de Restauración:
5. **Seleccionar un club eliminado**
6. **Hacer clic en "Restaurar"**
7. **Verificar:**
   - [ ] ✅ Mensaje de éxito
   - [ ] ✅ Club desaparece de la papelera
   - [ ] ✅ Club aparece en lista de clubes activos

### ✅ Resultado Esperado
```
✓ Acceso completo a papelera
✓ Puede restaurar clubes
✓ Puede eliminar permanentemente
✓ Sin errores de permisos
```

---

## 🌎 Prueba 2: Fed. Regional - Métricas Clubes

### Datos de Prueba
```
Usuario: [usuario_fed_regional]
Rol: fed_regional
Estado asignado: Zulia (ejemplo)
```

### Pasos:
1. **Iniciar sesión** con usuario Fed. Regional
2. **Verificar menú lateral:**
   - [ ] ✅ Debe aparecer "Métricas Clubes"
   - [ ] ❌ NO debe aparecer "Papelera"
   - [ ] ❌ NO debe aparecer "Gestionar Sedes"
3. **Hacer clic en "Métricas Clubes"**
4. **Verificar resultado:**
   - [ ] ✅ Debe cargar el dashboard sin errores
   - [ ] ✅ Debe mostrar métricas de clubes

### Verificar Filtrado por Estado:
5. **Revisar "Clubes por Estado":**
   - [ ] ✅ Solo debe mostrar su estado (ej: Zulia)
   - [ ] ❌ NO debe mostrar otros estados
6. **Revisar "Total de Clubes":**
   - [ ] ✅ Solo debe contar clubes de su estado
7. **Revisar "Clubes Populares":**
   - [ ] ✅ Solo debe mostrar clubes de su estado

### Comparación con Fed. Central:
8. **Iniciar sesión con Fed. Central**
9. **Ir a "Métricas Clubes"**
10. **Verificar:**
    - [ ] ✅ Debe mostrar TODOS los estados
    - [ ] ✅ Debe contar TODOS los clubes

### ✅ Resultado Esperado
```
✓ Fed. Regional accede a métricas
✓ Datos filtrados por su estado
✓ No ve datos de otros estados
✓ Fed. Central ve todos los datos
```

---

## 🏢 Prueba 3: Institucional - Notificaciones

### Datos de Prueba
```
Usuario: [usuario_institucional]
Rol: institucional
Institución: [nombre_institucion]
```

### Pasos:
1. **Iniciar sesión** con usuario Institucional
2. **Verificar menú lateral:**
   - [ ] ✅ Debe aparecer "Notificaciones" con badge de contador
3. **Hacer clic en "Notificaciones"**
4. **Verificar resultado:**
   - [ ] ✅ Debe cargar la página sin errores
   - [ ] ✅ Debe mostrar lista de notificaciones
   - [ ] ❌ NO debe mostrar error 500
   - [ ] ❌ NO debe mostrar AttributeError

### Prueba de Funcionalidad:
5. **Verificar lista de notificaciones:**
   - [ ] ✅ Debe mostrar título, mensaje y fecha
   - [ ] ✅ Notificaciones no leídas deben estar resaltadas
6. **Hacer clic en "Marcar como leída":**
   - [ ] ✅ Notificación debe cambiar de estado
   - [ ] ✅ Contador debe disminuir
7. **Hacer clic en "Marcar todas como leídas":**
   - [ ] ✅ Todas las notificaciones deben marcarse
   - [ ] ✅ Contador debe llegar a 0

### Prueba de Robustez:
8. **Recargar la página varias veces:**
   - [ ] ✅ No debe mostrar errores
   - [ ] ✅ Debe cargar consistentemente
9. **Cerrar sesión y volver a entrar:**
   - [ ] ✅ Notificaciones deben persistir

### ✅ Resultado Esperado
```
✓ Acceso sin errores
✓ Lista de notificaciones funcional
✓ Marcar como leída funciona
✓ Contador actualiza correctamente
✓ Sin errores 500 o AttributeError
```

---

## 🔒 Prueba 4: Seguridad - Acceso No Autorizado

### Test 4.1: Fed. Regional intenta acceder a Papelera
```bash
# URL directa
http://localhost:8000/admin/clubes/eliminados/
```

**Resultado esperado:**
- [ ] ❌ Debe redirigir al dashboard
- [ ] ❌ Debe mostrar mensaje "No tiene permisos"
- [ ] ❌ NO debe mostrar la papelera

### Test 4.2: Institucional intenta acceder a Métricas
```bash
# URL directa
http://localhost:8000/admin/clubes/dashboard-metricas/
```

**Resultado esperado:**
- [ ] ❌ Debe redirigir al dashboard
- [ ] ❌ Debe mostrar mensaje "No tiene permisos"
- [ ] ❌ NO debe mostrar las métricas

### Test 4.3: Usuario sin perfil
```bash
# Crear usuario sin UserProfile
# Intentar acceder a cualquier vista
```

**Resultado esperado:**
- [ ] ❌ Debe redirigir al dashboard
- [ ] ❌ NO debe mostrar error 500

---

## 📊 Matriz de Pruebas

| Rol | Papelera | Métricas | Notificaciones |
|-----|----------|----------|----------------|
| **Fed. Central** | ✅ Completo | ✅ Todos los estados | ✅ Funcional |
| **Fed. Regional** | ❌ Sin acceso | ✅ Solo su estado | ✅ Funcional |
| **Institucional** | ❌ Sin acceso | ❌ Sin acceso | ✅ Funcional |
| **Participante** | ❌ Sin acceso | ❌ Sin acceso | ❌ Sin acceso |

---

## 🐛 Problemas Comunes

### Problema 1: "No tiene permisos" en Fed. Central
**Causa:** Usuario no tiene `user_type = 'fed_central'`

**Solución:**
```python
# En Django shell
python manage.py shell

from users.models import UserProfile
perfil = UserProfile.objects.get(user__username='usuario_central')
perfil.user_type = 'fed_central'
perfil.save()
```

### Problema 2: Fed. Regional ve todos los estados
**Causa:** Usuario no tiene estado asignado

**Solución:**
```python
# En Django shell
from users.models import UserProfile
from registry.models import Estado

perfil = UserProfile.objects.get(user__username='usuario_regional')
estado = Estado.objects.get(nombre='Zulia')
perfil.estado = estado
perfil.save()
```

### Problema 3: Notificaciones siguen dando error
**Causa:** Cache del navegador

**Solución:**
```bash
# Limpiar cache
Ctrl + Shift + R (Chrome/Firefox)

# O usar modo incógnito
Ctrl + Shift + N (Chrome)
Ctrl + Shift + P (Firefox)
```

---

## ✅ Checklist Final

### Funcionalidad
- [ ] Fed. Central accede a Papelera
- [ ] Fed. Regional accede a Métricas (filtradas)
- [ ] Institucional accede a Notificaciones
- [ ] Filtrado por estado funciona correctamente
- [ ] Mensajes de error son claros

### Seguridad
- [ ] Fed. Regional NO accede a Papelera
- [ ] Institucional NO accede a Métricas
- [ ] URLs directas están protegidas
- [ ] Sin errores 500 en accesos no autorizados

### UX/UI
- [ ] Menús muestran solo opciones permitidas
- [ ] Contadores funcionan correctamente
- [ ] Mensajes de éxito/error son claros
- [ ] Navegación es intuitiva

---

## 📝 Reporte de Pruebas

### Plantilla

```markdown
## Reporte de Pruebas - Correcciones de Permisos

**Fecha:** [Fecha]
**Probador:** [Nombre]
**Navegador:** [Chrome/Firefox/etc]

### Fed. Central - Papelera
- Acceso: ✅ / ❌
- Restaurar: ✅ / ❌
- Eliminar: ✅ / ❌

### Fed. Regional - Métricas
- Acceso: ✅ / ❌
- Filtrado: ✅ / ❌
- Solo su estado: ✅ / ❌

### Institucional - Notificaciones
- Acceso: ✅ / ❌
- Listar: ✅ / ❌
- Marcar leída: ✅ / ❌

### Seguridad
- Accesos bloqueados: ✅ / ❌
- Mensajes claros: ✅ / ❌

### Problemas Encontrados
1. [Descripción]
2. [Descripción]

### Observaciones
[Comentarios]
```

---

## 🚀 Después de las Pruebas

Si todas las pruebas pasan:

```bash
# 1. Ejecutar verificación automática
./verificar_permisos.sh

# 2. Commit de cambios
git add .
git commit -m "fix: Corregir permisos de Papelera, Métricas y Notificaciones por rol"

# 3. Documentar en changelog
echo "- Corregidos permisos de acceso por rol" >> CHANGELOG.md
```

---

## 📚 Referencias

- `CORRECCION_PERMISOS_ROLES.md` - Análisis técnico
- `RESUMEN_CORRECCION_PERMISOS.md` - Resumen ejecutivo
- `verificar_permisos.sh` - Verificación automática
- `users/models.py` - Definición de roles

---

**Tiempo estimado de pruebas:** 30-45 minutos  
**Roles necesarios:** 3 (Fed. Central, Fed. Regional, Institucional)  
**Prioridad:** 🔴 Alta
