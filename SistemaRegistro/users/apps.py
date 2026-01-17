from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        # Importamos las señales desde la otra aplicación (registry)
        try:
            import registry.signals 
            print("SISTEMA: Señales de 'registry' conectadas desde 'users'")
        except ImportError as e:
            print(f"SISTEMA: Error al conectar señales: {e}")