from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"

    def ready(self):
        # Ahora importamos las señales que están dentro de esta misma app
        import users.signals  # noqa
