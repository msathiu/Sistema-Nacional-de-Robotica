from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"

    def ready(self):
        # Cada aplicación importa sus propias señales
        try:
            import registry.signals
            # Usar logging en lugar de print es más profesional
        except ImportError:
            pass
