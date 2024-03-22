import logging
from pathlib import Path

import click

from geoarchive.environment import run_env_binary
from geoarchive.project import Project
from geoarchive.services import get_service_protocol

workdir = Path('.')


@click.group()
def cli():
    logging.basicConfig(level=logging.INFO, force=True)


@cli.command()
@click.argument('project_name')
def init(project_name: str):
    Project.create(workdir / project_name, name=project_name)
    click.echo('Initialized the project')


@cli.command()
@click.option('--path', default=workdir, type=Path)
def status(path):
    project = Project.load(path)

    click.echo(f'Project: {project.name}')

    click.echo('Sources:')
    for source in project.get_sources():
        click.echo(f' - source name={source.name} type={source.type} cached={source.cached_at} refrest={source.refresh_interval}')


@cli.command()
@click.option('--path', default=workdir, type=Path)
@click.option('--type', default='tms', type=str, required=True)
@click.option('--url', type=str, required=True)
@click.option('--name', type=str, required=True)
def add_source(path: Path, type: str, url: str, name: str):
    project = Project.load(path)
    project.add_source(type, name, url)
    project.save(path)

    click.echo('Adding source name=%s type=%s url=%s' % (name, type, url))


@cli.command()
@click.option('--path', default=workdir, type=Path)
@click.option('--type', type=str, required=True)
@click.option('--url', type=str, required=True)
def import_sources(path: Path, type: str, url: str):
    project = Project.load(path)
    protocol = get_service_protocol(type, url)

    confirmed_layers = []
    for layer in protocol.list():
        if click.confirm(f"Do you want to include layer {layer.name}?", default=True):
            confirmed_layers.append(layer)

    click.echo(confirmed_layers)

    for layer in confirmed_layers:
        project.add_source(layer)

    project.save(path)

    click.echo('Importing sources type=%s url=%s' % (type, url))


@cli.command()
@click.option('--path', default=workdir, type=Path)
def rewrite(path: Path):
    project = Project.load(path)
    project.save(path)

    click.echo('Rewriting configs')


@cli.command()
@click.option('--path', default=workdir, type=Path)
def serve(path: Path):
    project = Project.load(path)

    click.echo(f'Serving project {project.name} in development mode')
    click.echo('THIS MODE SHOULD NOT BE USED IN PRODUCTION')

    run_env_binary(path, 'mapproxy-util', 'serve-develop', str(path / 'mapproxy.yaml'), '--debug')