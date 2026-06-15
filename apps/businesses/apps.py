from django.apps import AppConfig


class BusinessesConfig(AppConfig):
    name = 'apps.businesses'

    def ready(self):
        import apps.businesses.signals
