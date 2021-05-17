#!/usr/bin/env python3

from pathlib import Path
from subprocess import CalledProcessError, run
import click

SDK_ROOT = Path(__file__).parent.parent.absolute()


@click.command()
@click.option("-w", "--write", is_flag=True)
def main(write):
    if write:
        format_files()
    else:
        check_only()


def prettier(args, **kwargs):
    kwargs["check"] = True
    run(
        [
            "prettier",
            f"--config={SDK_ROOT/'.prettierrc.yml'}",
            f"--ignore-path={SDK_ROOT/'.prettierignore'}",
            *args,
        ],
        **kwargs,
    )


def check_only():
    try:
        run(["flake8", "--show-source", "."], cwd=SDK_ROOT, check=True)
        run(["black", "--check", "."], cwd=SDK_ROOT, check=True)
        prettier(["--check", "."], cwd=SDK_ROOT)
    except CalledProcessError as expt:
        exit(f"Issues found after running {expt.cmd} in {SDK_ROOT}.")


def format_files():
    run(["black", "."], cwd=SDK_ROOT)
    prettier(["-w", "."], cwd=SDK_ROOT)


if __name__ == "__main__":
    main()
