# ✅ CHECKLIST DE IMPLEMENTACIÓN DE SEGURIDAD

## 🎯 Objetivo
Asegurar que todas las correcciones de seguridad estén correctamente implementadas antes del despliegue.

---

## 📋 FASE 1: Configuración Inicial (5-10 minutos)

### Archivos de Configuración
- [ ] Archivo `.env` creado desde `.env.example`
- [ ] `SECRET_KEY` única generada y configurada
- [ ] `EMAIL_HOST_USER` configurado
- [ ] `EMAIL_HOST_PASSWORD` configurado
- [ ] `DEBUG=False` para producción (o `True` solo en desarrollo)
- [ ] `ALLOWED_HOSTS` configurado con dominio real
- [ ] `CSRF_TRUSTED_ORIGINS` configurado

### Comando para generar SECRET_KEY:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 📋 FASE 2: Verificación de Archivos (2 minutos)

### Archivos Nuevos Creados
- [ ] `SistemaRegistro/users/decorators.py` existe
- [ ] `SistemaRegistro/users/middleware.py` existe
- [ ] `CORRECCIONES_SEGURIDAD.md` existe
- [ ] `GUIA_RAPIDA_SEGURIDAD.md` existe
- [ ] `RESUMEN_EJECUTIVO_SEGURIDAD.md` existe
- [ ] `verificar_seguridad.py` existe
- [ ] `verificar_seguridad.bat` existe (Windows)

### Archivos Modificados
- [ ] `SistemaRegistro/SistemaRegistro/settings.py` actualizado
- [ ] `SistemaRegistro/users/views.py` actualizado
- [ ] `SistemaRegistro/registry/views.py` actualizado
- [ ] `SistemaRegistro/SistemaRegistro/urls.py` actualizado
- [ ] `.env.example` actualizado
- [ ] `README.md` actualizado

---

## 📋 FASE 3: Verificación Automatizada (2 minutos)

### Ejecutar Script de Verificación
```bash
# Linux/Mac
python verificar_seguridad.py

# Windows
verificar_seguridad.bat
```

### Resultado Esperado
- [ ] ✅ Archivo .env configurado correctamente
- [ ] ✅ Modo DEBUG verificado
- [ ] ✅ No se encontraron credenciales hardcodeadas
- [ ] ✅ Decoradores de seguridad implementados
- [ ] ✅ Middlewares de seguridad configurados
- [ ] ✅ Endpoints críticos protegidos

---

## 📋 FASE 4: Pruebas Funcionales (10-15 minutos)

### Autenticación y Autorización
- [ ] Login funciona correctamente
- [ ] Logout funciona correctamente
- [ ] Usuario admin puede acceder a `/instituciones/`
- [ ] Usuario institucional NO puede acceder a `/instituciones/`
- [ ] Usuario institucional solo ve sus propios datos
- [ ] Endpoints AJAX requieren login (probar sin autenticación)

### Operaciones Críticas
- [ ] Admin puede aprobar instituciones
- [ ] Admin puede desactivar instituciones
- [ ] Admin puede eliminar instituciones
- [ ] Institucional puede editar solo su propia institución
- [ ] Institucional NO puede editar otras instituciones

### Validación de Entrada
- [ ] Búsqueda con menos de 2 caracteres no funciona
- [ ] Búsqueda con más de 50 caracteres se trunca
- [ ] IDs negativos o cero son rechazados
- [ ] Parámetros no numéricos son manejados correctamente

---

## 📋 FASE 5: Pruebas de Seguridad (10 minutos)

### Rate Limiting
```bash
# Hacer 65 peticiones rápidas
for i in {1..65}; do curl -s http://localhost:8000/ajax/cargar-municipios/?estado_id=1; done
```
- [ ] Peticiones 1-60 funcionan
- [ ] Petición 61+ retorna error 429
- [ ] Mensaje de error apropiado mostrado

### Headers de Seguridad
```bash
curl -I http://localhost:8000
```
- [ ] `X-Frame-Options: DENY` presente
- [ ] `X-Content-Type-Options: nosniff` presente
- [ ] `X-XSS-Protection: 1; mode=block` presente
- [ ] `Referrer-Policy: strict-origin-when-cross-origin` presente
- [ ] `Permissions-Policy` presente

### Cookies Seguras (solo en producción con HTTPS)
- [ ] `SESSION_COOKIE_SECURE=True` configurado
- [ ] `CSRF_COOKIE_SECURE=True` configurado
- [ ] `SESSION_COOKIE_HTTPONLY=True` configurado
- [ ] `CSRF_COOKIE_HTTPONLY=True` configurado
- [ ] `SESSION_COOKIE_SAMESITE='Strict'` configurado

---

## 📋 FASE 6: Configuración de Producción (Solo para Deploy)

### Variables de Entorno
- [ ] `DEBUG=False` configurado
- [ ] `SECRET_KEY` única (diferente a desarrollo)
- [ ] `ALLOWED_HOSTS` con dominio real
- [ ] `CSRF_TRUSTED_ORIGINS` con dominio real
- [ ] `SECURE_SSL_REDIRECT=True` (si usas HTTPS)
- [ ] Credenciales de email de producción configuradas

### Base de Datos
- [ ] PostgreSQL configurado (si aplica)
- [ ] `DATABASE_URL` configurado correctamente
- [ ] Migraciones aplicadas
- [ ] Backup configurado

### Servidor Web
- [ ] HTTPS habilitado
- [ ] Certificado SSL válido
- [ ] Nginx/Apache configurado correctamente
- [ ] Archivos estáticos servidos correctamente

---

## 📋 FASE 7: Monitoreo y Logs (Post-Deploy)

### Configuración de Logs
- [ ] Directorio `logs/` existe
- [ ] Archivo `logs/django.log` se está generando
- [ ] Logs rotativos funcionando (máx 10MB, 5 backups)
- [ ] Nivel de log apropiado (INFO en producción)

### Monitoreo
- [ ] Revisar logs cada día
- [ ] Configurar alertas para rate limiting
- [ ] Configurar alertas para errores de seguridad
- [ ] Monitorear intentos de acceso no autorizado

### Comandos Útiles
```bash
# Ver logs en tiempo real
tail -f logs/django.log

# Ver intentos de rate limiting
grep "Rate limit" logs/django.log

# Ver errores de seguridad
grep "WARNING\|ERROR" logs/django.log
```

---

## 📋 FASE 8: Documentación y Capacitación

### Documentación
- [ ] Equipo ha leído `CORRECCIONES_SEGURIDAD.md`
- [ ] Equipo ha leído `GUIA_RAPIDA_SEGURIDAD.md`
- [ ] Equipo conoce ubicación de logs
- [ ] Equipo conoce procedimiento de respuesta a incidentes

### Capacitación
- [ ] Desarrolladores capacitados en uso de decoradores
- [ ] Desarrolladores conocen validación de entrada
- [ ] Administradores conocen configuración de .env
- [ ] Administradores conocen monitoreo de logs

---

## 📋 FASE 9: Backup y Recuperación

### Backup
- [ ] Script de backup configurado
- [ ] Backup de base de datos funcionando
- [ ] Backup de archivos media funcionando
- [ ] Backup de configuración (.env) seguro

### Recuperación
- [ ] Procedimiento de recuperación documentado
- [ ] Procedimiento de recuperación probado
- [ ] Contactos de emergencia definidos

---

## 📋 FASE 10: Aprobación Final

### Revisión Técnica
- [ ] Código revisado por líder técnico
- [ ] Pruebas de seguridad completadas
- [ ] Documentación completa y actualizada
- [ ] Sin vulnerabilidades críticas pendientes

### Aprobación de Stakeholders
- [ ] Equipo de desarrollo aprueba
- [ ] Equipo de QA aprueba
- [ ] Equipo de seguridad aprueba (si aplica)
- [ ] Product Owner aprueba

### Firma de Aprobación
```
Desarrollador: _________________ Fecha: _______
QA:            _________________ Fecha: _______
DevOps:        _________________ Fecha: _______
Aprobador:     _________________ Fecha: _______
```

---

## 🎉 COMPLETADO

Si todos los checkboxes están marcados, el sistema está listo para producción.

**Fecha de implementación:** _________________
**Versión:** SNR-PRO v1.0 + Parche de Seguridad
**Próxima revisión:** _________________

---

## 📞 Contactos de Emergencia

**Líder Técnico:** _________________
**DevOps:** _________________
**Seguridad:** _________________

---

## 📚 Referencias Rápidas

- **Documentación técnica:** `CORRECCIONES_SEGURIDAD.md`
- **Guía rápida:** `GUIA_RAPIDA_SEGURIDAD.md`
- **Resumen ejecutivo:** `RESUMEN_EJECUTIVO_SEGURIDAD.md`
- **Verificación:** `python verificar_seguridad.py`
- **Logs:** `logs/django.log`

---

**IMPORTANTE:** Guarda este checklist completado para auditorías futuras.
