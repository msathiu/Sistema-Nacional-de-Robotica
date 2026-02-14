# 🚀 GUÍA RÁPIDA: Implementar Correcciones de Seguridad

## ⚡ Pasos Inmediatos (5 minutos)

### 1. Configurar Variables de Entorno

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Generar SECRET_KEY única
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Editar .env y pegar la SECRET_KEY generada
# También configurar:
# - EMAIL_HOST_USER
# - EMAIL_HOST_PASSWORD
# - DEBUG=False (para producción)
```

### 2. Verificar Configuración

```bash
# Ejecutar script de verificación
python verificar_seguridad.py

# Debe mostrar: ✅ TODAS LAS VERIFICACIONES PASARON
```

### 3. Reiniciar el Sistema

```bash
# Si usas desarrollo local:
cd SistemaRegistro
python manage.py runserver

# Si usas Docker:
docker compose down
docker compose up --build
```

---

## 📋 Checklist de Verificación

### Antes de Desplegar:
- [ ] Archivo `.env` creado y configurado
- [ ] `SECRET_KEY` única generada (no usar la default)
- [ ] `DEBUG=False` en producción
- [ ] Credenciales de email configuradas
- [ ] `ALLOWED_HOSTS` configurado con tu dominio
- [ ] Script `verificar_seguridad.py` ejecutado exitosamente

### Después de Desplegar:
- [ ] Login funciona correctamente
- [ ] Endpoints AJAX requieren autenticación
- [ ] Admin puede aprobar instituciones
- [ ] Instituciones solo ven sus propios datos
- [ ] Rate limiting funciona (probar 60+ peticiones)

---

## 🧪 Pruebas Rápidas

### 1. Probar Autenticación en AJAX
```bash
# Sin login - debe fallar
curl http://localhost:8000/ajax/cargar-municipios/?estado_id=1

# Con login - debe funcionar
# (usar navegador o curl con cookies)
```

### 2. Probar Rate Limiting
```bash
# Hacer 65 peticiones rápidas
for i in {1..65}; do
  curl -s http://localhost:8000/ajax/cargar-municipios/?estado_id=1
done

# La petición 61+ debe retornar error 429
```

### 3. Verificar Headers de Seguridad
```bash
curl -I http://localhost:8000

# Debe incluir:
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
# X-XSS-Protection: 1; mode=block
```

### 4. Probar Permisos
```bash
# Login como usuario institucional
# Intentar acceder a: /instituciones/
# Debe redirigir al dashboard (sin permiso)

# Login como admin
# Acceder a: /instituciones/
# Debe mostrar la lista completa
```

---

## 🔧 Solución de Problemas

### Error: "SECRET_KEY debe estar configurada"
```bash
# Verificar que .env existe
ls -la .env

# Verificar que SECRET_KEY no está vacía
cat .env | grep SECRET_KEY

# Generar nueva si es necesario
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Error: "No module named 'users.decorators'"
```bash
# Verificar que el archivo existe
ls -la SistemaRegistro/users/decorators.py

# Si no existe, fue un error en la creación
# Revisar CORRECCIONES_SEGURIDAD.md para recrearlo
```

### Error: "No module named 'users.middleware'"
```bash
# Verificar que el archivo existe
ls -la SistemaRegistro/users/middleware.py

# Verificar que está en MIDDLEWARE en settings.py
grep "RateLimitMiddleware" SistemaRegistro/SistemaRegistro/settings.py
```

### Error: AJAX no funciona después de las correcciones
```bash
# Verificar que el usuario está autenticado
# Los endpoints AJAX ahora requieren login

# En el frontend, asegurarse de incluir CSRF token:
# <script>
#   const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
#   fetch('/ajax/cargar-municipios/', {
#     headers: {'X-CSRFToken': csrftoken}
#   })
# </script>
```

---

## 📊 Archivos Modificados

### Archivos Nuevos:
- ✅ `users/decorators.py` - Decoradores de seguridad
- ✅ `users/middleware.py` - Middlewares de seguridad
- ✅ `CORRECCIONES_SEGURIDAD.md` - Documentación completa
- ✅ `verificar_seguridad.py` - Script de verificación
- ✅ `GUIA_RAPIDA_SEGURIDAD.md` - Este archivo

### Archivos Modificados:
- ✅ `SistemaRegistro/settings.py` - Configuración de seguridad
- ✅ `users/views.py` - Decoradores y validaciones
- ✅ `registry/views.py` - Protección de endpoints
- ✅ `SistemaRegistro/urls.py` - Protección de URLs
- ✅ `.env.example` - Template actualizado

---

## 🎯 Próximos Pasos (Opcional)

### Mejoras Adicionales Recomendadas:
1. **Implementar 2FA** para administradores
2. **Agregar logging de auditoría** para acciones críticas
3. **Configurar backup automático** de base de datos
4. **Implementar monitoreo** con Sentry o similar
5. **Agregar tests de seguridad** automatizados
6. **Configurar WAF** (Web Application Firewall)
7. **Implementar CAPTCHA** en formularios públicos

### Documentación Adicional:
- Ver `CORRECCIONES_SEGURIDAD.md` para detalles técnicos
- Ver `MEJORES_PRACTICAS.md` para guías de desarrollo
- Ver `README.md` para información general del proyecto

---

## 📞 Soporte

Si encuentras problemas:
1. Ejecutar `python verificar_seguridad.py`
2. Revisar logs en `logs/django.log`
3. Consultar `CORRECCIONES_SEGURIDAD.md`
4. Contactar al equipo de desarrollo

---

**Última actualización:** $(date)
**Versión:** SNR-PRO v1.0 + Parche de Seguridad
