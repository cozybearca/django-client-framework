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


def create_objects():
    env = os.environ.copy()
    env.update({"PYTHONPATH": PROJ.absolute()})
    shell(
        "python3 ./manage.py shell",
        cwd=PROJ,
        env=env,
        input="""
from dcf_backend_example.common.models import Product, Brand
nike = Brand.objects.create(name="nike")
Product.objects.create(barcode="xxyy", brand=nike)
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


def clear():
    for content in PROJ.iterdir():
        if content.is_dir():
            shutil.rmtree(content.absolute())
        else:
            content.unlink()


def create_model():
    shutil.copyfile("/proj/models.py", PROJ / "dcf_backend_example/common/models.py")


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
    """
    The goal of this suite is to test for Django Client Framework's
    installation, making sure the instruction is up-to-date.
    """

    def query_product_list(self):
        result = shell("curl http://localhost:8000/product", capture_output=True)
        self.assertEqual(result.returncode, 0)
        response = json.loads(result.stdout)
        self.assertEqual(response["total"], 1)
        self.assertEqual(
            response["objects"],
            [{"id": 1, "barcode": "xxyy", "brand_id": 1}],
        )

    def query_product(self):
        result = shell("curl http://localhost:8000/product/1", capture_output=True)
        self.assertEqual(result.returncode, 0)
        response = json.loads(result.stdout)
        self.assertEqual(response, {"id": 1, "barcode": "xxyy", "brand_id": 1})

    def query_product_brand(self):
        result = shell(
            "curl http://localhost:8000/product/1/brand", capture_output=True
        )
        self.assertEqual(result.returncode, 0)
        response = json.loads(result.stdout)
        self.assertEqual(response, {"id": 1, "name": "nike"})

    def query_brand(self):
        result = shell("curl http://localhost:8000/brand/1", capture_output=True)
        self.assertEqual(result.returncode, 0)
        response = json.loads(result.stdout)
        self.assertEqual(response, {"id": 1, "name": "nike"})

    def query_brand_product_list(self):
        result = shell(
            "curl http://localhost:8000/brand/1/products", capture_output=True
        )
        self.assertEqual(result.returncode, 0)
        response = json.loads(result.stdout)
        self.assertEqual(response["total"], 1)
        self.assertEqual(
            response["objects"],
            [{"id": 1, "barcode": "xxyy", "brand_id": 1}],
        )

    def test_main(self):
        server = None

        try:
            clear()
            installation()
            write_to_settings()
            add_routes()
            create_model()
            run_migration()
            create_objects()
            set_permissions()
            server = django_runserver()
            self.query_product_list()
            self.query_product()
            self.query_product_brand()
            self.query_brand()
            self.query_brand_product_list()

        except SubprocessError as err:
            exit(err.returncode)

        finally:
            if server:
                server.terminate()


if __name__ == "__main__":
    unittest.main()
