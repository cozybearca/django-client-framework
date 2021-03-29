#!/usr/bin/env python3

import click
from subprocess import run


def build_ubuntu_base():
    run(
        ["docker-compose", "-f", "build.yml", "build", "dcf-test-ubuntu-base"],
        check=True,
    )


def build_example():
    build_ubuntu_base()


@click.command()
@click.argument("name")
def main(name):
    pass


if __name__ == "__main__":
    main()
