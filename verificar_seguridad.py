#!/usr/bin/env python
"""
Script de verificación de seguridad para SNR-PRO
Verifica que todas las configuraciones de seguridad estén correctamente aplicadas
"""
import os
import sys
from pathlib import Path

# Colores para output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def check_env_file():
    """Verifica que el archivo .env exista y tenga las variables necesarias"""
    print("\n🔍 Verificando archivo .env...")

    env_path = Path(".env")
    if not env_path.exists():
        print(f"{RED}❌ Archivo .env no encontrado{RESET}")
        print(f"{YELLOW}   Copia .env.example a .env y configura las variables{RESET}")
        return False

    required_vars = [
        "SECRET_KEY",
        "DEBUG",
        "EMAIL_HOST_USER",
        "EMAIL_HOST_PASSWORD",
        "ALLOWED_HOSTS",
    ]

    with open(env_path, "r") as f:
        content = f.read()

    missing = []
    for var in required_vars:
        if f"{var}=" not in content or f"{var}=\n" in content or f"{var}= " in content:
            missing.append(var)

    if missing:
        print(f"{RED}❌ Variables faltantes o vacías: {', '.join(missing)}{RESET}")
        return False

    # Verificar que SECRET_KEY no sea la default
    if "django-insecure" in content:
        print(f"{RED}❌ SECRET_KEY usa valor por defecto inseguro{RESET}")
        print(
            f'{YELLOW}   Genera una nueva con: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"{RESET}'
        )
        return False

    print(f"{GREEN}✅ Archivo .env configurado correctamente{RESET}")
    return True


def check_debug_mode():
    """Verifica que DEBUG esté en False para producción"""
    print("\n🔍 Verificando modo DEBUG...")

    env_path = Path(".env")
    if env_path.exists():
        with open(env_path, "r") as f:
            content = f.read()

        if "DEBUG=True" in content:
            print(f"{YELLOW}⚠️  DEBUG=True detectado (solo usar en desarrollo){RESET}")
            return True
        elif "DEBUG=False" in content:
            print(f"{GREEN}✅ DEBUG=False configurado{RESET}")
            return True

    print(f"{RED}❌ No se pudo verificar DEBUG{RESET}")
    return False


def check_credentials_in_code():
    """Verifica que no haya credenciales hardcodeadas en settings.py"""
    print("\n🔍 Verificando credenciales hardcodeadas...")

    settings_path = Path("SistemaRegistro/SistemaRegistro/settings.py")
    if not settings_path.exists():
        print(f"{RED}❌ No se encontró settings.py{RESET}")
        return False

    with open(settings_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Buscar patrones sospechosos
    suspicious = []

    if (
        'EMAIL_HOST_USER = "' in content
        and "os.getenv" not in content.split("EMAIL_HOST_USER")[1].split("\n")[0]
    ):
        suspicious.append("EMAIL_HOST_USER hardcodeado")

    if (
        'EMAIL_HOST_PASSWORD = "' in content
        and "os.getenv" not in content.split("EMAIL_HOST_PASSWORD")[1].split("\n")[0]
    ):
        suspicious.append("EMAIL_HOST_PASSWORD hardcodeado")

    if suspicious:
        print(f"{RED}❌ Credenciales hardcodeadas encontradas:{RESET}")
        for item in suspicious:
            print(f"   - {item}")
        return False

    print(f"{GREEN}✅ No se encontraron credenciales hardcodeadas{RESET}")
    return True


def check_decorators():
    """Verifica que los decoradores de seguridad estén implementados"""
    print("\n🔍 Verificando decoradores de seguridad...")

    decorators_path = Path("SistemaRegistro/users/decorators.py")
    if not decorators_path.exists():
        print(f"{RED}❌ Archivo decorators.py no encontrado{RESET}")
        return False

    with open(decorators_path, "r", encoding="utf-8") as f:
        content = f.read()

    required_decorators = [
        "admin_required",
        "institucional_required",
        "owns_institution",
    ]
    missing = [d for d in required_decorators if d not in content]

    if missing:
        print(f"{RED}❌ Decoradores faltantes: {', '.join(missing)}{RESET}")
        return False

    print(f"{GREEN}✅ Decoradores de seguridad implementados{RESET}")
    return True


def check_middleware():
    """Verifica que los middlewares de seguridad estén configurados"""
    print("\n🔍 Verificando middlewares de seguridad...")

    middleware_path = Path("SistemaRegistro/users/middleware.py")
    if not middleware_path.exists():
        print(f"{RED}❌ Archivo middleware.py no encontrado{RESET}")
        return False

    settings_path = Path("SistemaRegistro/SistemaRegistro/settings.py")
    with open(settings_path, "r", encoding="utf-8") as f:
        settings_content = f.read()

    required_middlewares = ["RateLimitMiddleware", "SecurityHeadersMiddleware"]
    missing = [m for m in required_middlewares if m not in settings_content]

    if missing:
        print(
            f"{RED}❌ Middlewares no configurados en settings: {', '.join(missing)}{RESET}"
        )
        return False

    print(f"{GREEN}✅ Middlewares de seguridad configurados{RESET}")
    return True


def check_protected_endpoints():
    """Verifica que los endpoints críticos estén protegidos"""
    print("\n🔍 Verificando protección de endpoints...")

    views_path = Path("SistemaRegistro/users/views.py")
    if not views_path.exists():
        print(f"{RED}❌ Archivo views.py no encontrado{RESET}")
        return False

    with open(views_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Verificar que funciones críticas tengan decoradores
    critical_functions = [
        "aprobar_institucion",
        "desactivar_institucion",
        "eliminar_institucion",
        "exportar_participantes_excel",
    ]

    unprotected = []
    for func in critical_functions:
        if f"def {func}" in content:
            # Buscar el decorador antes de la función
            func_index = content.index(f"def {func}")
            before_func = content[:func_index].split("\n")[
                -5:
            ]  # Últimas 5 líneas antes

            has_decorator = any(
                "@admin_required" in line or "@login_required" in line
                for line in before_func
            )
            if not has_decorator:
                unprotected.append(func)

    if unprotected:
        print(f"{RED}❌ Funciones sin protección: {', '.join(unprotected)}{RESET}")
        return False

    print(f"{GREEN}✅ Endpoints críticos protegidos{RESET}")
    return True


def main():
    print("=" * 60)
    print("🔒 VERIFICACIÓN DE SEGURIDAD - SNR-PRO")
    print("=" * 60)

    checks = [
        check_env_file,
        check_debug_mode,
        check_credentials_in_code,
        check_decorators,
        check_middleware,
        check_protected_endpoints,
    ]

    results = [check() for check in checks]

    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"\nPruebas pasadas: {passed}/{total}")

    if passed == total:
        print(f"\n{GREEN}✅ TODAS LAS VERIFICACIONES PASARON{RESET}")
        print(f"{GREEN}   El sistema está configurado de forma segura{RESET}")
        return 0
    else:
        print(f"\n{RED}❌ ALGUNAS VERIFICACIONES FALLARON{RESET}")
        print(
            f"{YELLOW}   Revisa los errores arriba y corrígelos antes de desplegar{RESET}"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
