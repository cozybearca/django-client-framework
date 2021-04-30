#!/usr/bin/env python3
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path


def set_python_path():
    PYTHONPATH = os.environ.get("PYTHONPATH", "")
    __dir__ = Path(__file__).parent
    # always use the local django_client_framework over the system-wide
    # installed
    proj_root = str(__dir__.parent.absolute())
    os.environ["PYTHONPATH"] = f"{proj_root}:{PYTHONPATH}"


def main():
    """Run administrative tasks."""
    set_python_path()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dcf_test_proj.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
