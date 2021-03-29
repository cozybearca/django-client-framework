from subprocess import run, SubprocessError

try:
    for cmd in [
        "mkdir ./example",
        "cd ./example",
        "pip3 install -e git+https://github.com/cozybearca/django-client-framework.git#egg=django_client_framework",
        "django-admin startproject example",
    ]:
        run(cmd, shell=True, check=True)
except SubprocessError as err:
    exit(err.returncode)
