#!/usr/bin/python3
import click
import sh
import os
import sys
import time
from pathlib import Path


@click.group()
def cli():
    """ Collection of commands to manage the processing server

    This python script currently just executes docker-compose commands
    """
    pass


@cli.command()
@click.option("--build", is_flag=True, default=False,
              help="additionally build containers without cache")
def start(build=False):
    """ Start the processing server
    """
    logfile = "/tmp/ocrd-processing-server-startup.log"
    if Path(logfile).exists():
        sh.mv(
            logfile,
            f"/tmp/ocrd-processing-server-startup-{time.strftime('%Y-%m-%d-%H-%M-%S')}.log",
        )
    os.chdir(Path.home() / "tools")
    sh.docker_compose("down", "--remove-orphans", _out=sys.stdout, _err=sys.stderr)
    if build:
        sh.docker_compose("build", "--no-cache", _out=sys.stdout, _err=sys.stderr)
    sh.docker_compose("up", "-d", _out=sys.stdout, _err=sys.stderr)


@cli.command()
def stop():
    """ Stop the processing server
    """
    os.chdir(Path.home() / "tools")
    sh.docker_compose("down", _out=sys.stdout, _err=sys.stderr)


@cli.command()
@click.option("--force", is_flag=True, default=False, help="execute without conformation prompt")
def clean(force=False):
    """ Reset everything regarding docker

    Stop docker-containers, remove workspaces from disc
    """
    workspaces_dir = "/tmp/ocrd-webapi-data/workspaces"
    if not force:
        x = input(f"This deletes {workspaces_dir}. Type 'yes' to continue\n")

        if x != 'yes':
            print("abort")
            return

    os.chdir(Path.home() / "tools")
    sh.docker_compose("down", "--remove-orphans", _out=sys.stdout, _err=sys.stderr)

    os.chdir(Path.home())
    sh.rm("-rf", f"{workspaces_dir}")


if __name__ == "__main__":
    cli()
