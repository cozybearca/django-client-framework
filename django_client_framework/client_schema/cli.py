#!/usr/bin/env python3

import json
import os
import shutil
from multiprocessing import Pool
from pathlib import Path

import click

from .convert import model_to_jsonschema

DEST_DIR = Path("/tmp/json_schema")


def generate_json(model):
    schema = model_to_jsonschema(model)
    dest_file = DEST_DIR / f"{model.__name__}.json"
    dump = json.dumps(schema, ensure_ascii=False, indent=2)
    dest_file.write_text(dump)
    print(dest_file)


@click.command()
def main():
    import django

    django.setup()
    from django_client_framework.serializers import generate_jsonschema

    if DEST_DIR.exists():
        shutil.rmtree(DEST_DIR)
    DEST_DIR.mkdir(parents=True)

    with Pool(os.cpu_count()) as pool:
        pool.map(generate_json, generate_jsonschema.get_models())


if __name__ == "__main__":
    main()
