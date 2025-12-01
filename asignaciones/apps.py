from django.apps import AppConfig

class AsignacionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'asignaciones'

    def ready(self):
        import asignaciones.signals  # mantiene la conexión con los signals
