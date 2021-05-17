from subprocess import Popen, run
from pathlib import Path
import shutil
import unittest

PROJ = Path("/_out")


def debug():
    shell("sleep inf")


def shell(cmd, **kwargs):
    print(f"+ {cmd}", flush=True)
    return run(cmd, shell=True, text=True, check=True, **kwargs)


def clear():
    for content in PROJ.iterdir():
        if content.is_dir():
            shutil.rmtree(content.absolute())
        else:
            content.unlink()


def django_runserver() -> Popen:
    shell("pip3 install /django_client_framework")
    shell("mkdir /dcf-backend-example")
    shell("tar -xzvf /dcf-backend-example.tar.gz", cwd="/dcf-backend-example")
    proc = Popen(
        "python3 ./manage.py runserver",
        shell=True,
        cwd="/dcf-backend-example",
    )
    shell("wait-for-it localhost:8000")
    return proc


def installation():
    for cmd in [
        "cp /proj/* /_out",
        "yarn add file:///django-client-framework-typescript",
        "yarn install --dev",
    ]:
        shell(cmd, cwd=PROJ)


def yarn_build():
    shell("yarn build", cwd=PROJ)


def run_app():
    shell("node build/main.js", cwd=PROJ)


class Test(unittest.TestCase):
    def test_main(self):
        server = None
        try:
            clear()
            installation()
            server = django_runserver()
            yarn_build()
            run_app()
        finally:
            if server:
                server.terminate()


if __name__ == "__main__":
    unittest.main()
