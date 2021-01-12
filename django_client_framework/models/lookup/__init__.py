import importlib

Not = getattr(
    importlib.import_module(".not", "django_client_framework.models.lookup"), "Not"
)
