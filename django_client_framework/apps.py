from django.apps import AppConfig


class DefaultApp(AppConfig):
    name = "django_client_framework"

    def ready(self):
        """
        Although you can access model classes as described above, avoid interacting with
        the database in your ready() implementation. This includes model methods that
        execute queries (save(), delete(), manager methods etc.), and also raw SQL
        queries via django.db.connection. Your ready() method will run during startup of
        every management command. For example, even though the test database
        configuration is separate from the production settings, manage.py test would
        still execute some queries against your production database!
        """

        from django.conf import settings

        settings.REST_FRAMEWORK[
            "EXCEPTION_HANDLER"
        ] = "django_client_framework.exceptions.handlers.dcf_exception_handler"

        from django_client_framework.permissions import auto  # noqa

        if settings.DEBUG or settings.TUNE_TEST:
            from django_client_framework.api import model_api
            from django_client_framework.models import abstract as model_abstract
            from django_client_framework.serializers import base as serializer_base

            model_abstract.check_integrity()
            model_api.check_integrity()
            serializer_base.check_integrity()
