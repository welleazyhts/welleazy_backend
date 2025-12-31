from django.apps import AppConfig


class ProvidersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.providers'
    verbose_name = 'Healthcare Service Providers'

    def ready(self):
        # Import providers to register them
        from . import registry  # noqa
