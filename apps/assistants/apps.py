from django.apps import AppConfig


class AssistantsConfig(AppConfig):
    name = 'apps.assistants'

    def ready(self):
        import apps.assistants.signals

