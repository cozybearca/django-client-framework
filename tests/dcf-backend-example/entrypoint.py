from subprocess import Popen, run, SubprocessError
from pathlib import Path
import shutil
import os
import json
import unittest

PROJ = Path("/dcf-backend-example-proj")


def debug():
    shell("sleep inf")


def shell(cmd, **kwargs):
    print(f"+ {cmd}", flush=True)
    return run(cmd, shell=True, text=True, check=True, **kwargs)


def write_to_settings():
    settings = PROJ / "dcf_backend_example/settings.py"
    content = settings.read_text()
    new_content = f"""
import django_client_framework.settings

{content}

REST_FRAMEWORK = {{}}
AUTHENTICATION_BACKENDS = []
INSTALLED_APPS += ["dcf_backend_example.common"]

django_client_framework.settings.install(
    INSTALLED_APPS,
    REST_FRAMEWORK,
    MIDDLEWARE,
    AUTHENTICATION_BACKENDS
)
"""
    settings.write_text(new_content)


def installation():
    for cmd in [
        "pip3 install /django_client_framework",
        "pip3 install psycopg2-binary",
        "django-admin startproject dcf_backend_example",
        f"mv /dcf_backend_example/* {PROJ.absolute()}",
        f"touch {PROJ.absolute()}/__init__.py",
    ]:
        shell(cmd)
    shell(
        "python3 ../manage.py startapp common",
        cwd=PROJ / "dcf_backend_example",
    )


def run_migration():
    for cmd in [
        "python3 ./manage.py makemigrations",
        "python3 ./manage.py migrate",
    ]:
        shell(cmd, cwd=PROJ)


def django_runserver() -> Popen:
    proc = Popen(
        "python3 ./manage.py runserver",
        shell=True,
        cwd=PROJ,
    )
    shell("wait-for-it localhost:8000")
    return proc


def create_product():
    env = os.environ.copy()
    env.update({"PYTHONPATH": PROJ.absolute()})
    shell(
        "python3 ./manage.py shell",
        cwd=PROJ,
        env=env,
        input="""
from dcf_backend_example.common.models import Product
Product.objects.create(barcode="xxyy")
Product.objects.all()
""",
    )


def set_permissions():
    env = os.environ.copy()
    env.update({"PYTHONPATH": PROJ.absolute()})
    shell(
        "python3 ./manage.py shell",
        cwd=PROJ,
        env=env,
        input="""
from django_client_framework.permissions import reset_permissions
reset_permissions()
""",
    )


def send_get_request():
    return shell("curl http://localhost:8000/product", capture_output=True)


def clear():
    for content in PROJ.iterdir():
        if content.is_dir():
            shutil.rmtree(content.absolute())
        else:
            content.unlink()


def create_product_model():
    content = """
from django_client_framework.models import Serializable, AccessControlled
from django_client_framework.serializers import ModelSerializer
from django_client_framework.permissions import default_groups, set_perms_shortcut
from django_client_framework.api import register_api_model
from django.db.models import CharField


@register_api_model
class Product(Serializable, AccessControlled):
    barcode = CharField(max_length=32)

    @classmethod
    def serializer_class(cls):
        return ProductSerializer

    class PermissionManager(AccessControlled.PermissionManager):
        def add_perms(self, product):
            set_perms_shortcut(default_groups.anyone, product, "r")


class ProductSerializer(ModelSerializer):
    class Meta:
        model = Product
        exclude = []
"""
    (PROJ / "dcf_backend_example/common/models.py").write_text(content)


def add_routes():
    urls_py = PROJ / "dcf_backend_example/urls.py"
    content = urls_py.read_text()
    urls_py.write_text(
        f"""
import django_client_framework.api.urls

{content}

urlpatterns += django_client_framework.api.urls.urlpatterns
"""
    )


class Test(unittest.TestCase):
    def test_main(self):
        server = None

        try:
            clear()
            installation()
            write_to_settings()
            add_routes()
            create_product_model()
            run_migration()
            create_product()
            set_permissions()
            server = django_runserver()
            result = send_get_request()

            self.assertEqual(result.returncode, 0)
            response = json.loads(result.stdout)
            self.assertEqual(response["total"], 1)
            self.assertEqual(response["objects"], [{"id": 1, "barcode": "xxyy"}])

        except SubprocessError as err:
            exit(err.returncode)

        finally:
            if server:
                server.terminate()


if __name__ == "__main__":
    unittest.main()
