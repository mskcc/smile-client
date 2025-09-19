from django.apps import AppConfig


class SmileClientConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'smile_client'

    def ready(self):
        # Import signals or other startup code here if needed
        pass