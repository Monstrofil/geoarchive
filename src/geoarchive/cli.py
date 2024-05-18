import logging
from pathlib import Path

import click

from geoarchive.environment import run_env_binary
from geoarchive.project import Project
from geoarchive.services import get_service_protocol
from geoarchive.cache import CacheService

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
def upgrade(path: Path):
    project = Project.load(path)
    project.upgrade(path)

    click.echo('Upgraded the project')


@cli.command()
@click.option('--path', default=workdir, type=Path)
def status(path):
    project = Project.load(path)

    click.echo(f'Project: {project.name}')

    click.echo('Sources:')
    for name, source in project.get_sources().items():
        click.echo(f' - source name={source.name} type={source.type} cached={source.cached_at} refresh={source.refresh_interval}')

    click.echo('Caches:')
    for name, cache in project.get_caches().items():
        click.echo(f' - source name={cache.name} sources={cache.sources}')


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
@click.option('--name', type=str, required=True)
@click.option('--sources', type=str, required=True)
def add_cache(path: Path, name: str, sources: str):
    project = Project.load(path)

    layers = sources.split(',')
    project.add_cache(name, layers)

    project.save(path)


@cli.command()
@click.option('--path', default=workdir, type=Path)
@click.option('--type', type=str, required=True)
@click.option('--url', type=str, required=True)
@click.option('--new-only', is_flag=True, type=bool)
def import_sources(path: Path, type: str, url: str, new_only: bool = False):
    project = Project.load(path)
    service = get_service_protocol(type, url)

    cache = CacheService.load(url, project_path=path)

    confirmed_layers = []
    for layer in service.list_layers():
        if new_only and cache.exists(layer):
            logging.info(f'Skipping layer {layer.name} because already exists in cache')
            continue

        if click.confirm(f"Do you want to include layer {layer.name}?", default=True):
            confirmed_layers.append(layer)

        cache.set(layer)

    for layer in confirmed_layers:
        project.add_source(layer)

    cache.save(url, path)
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
@click.option('--bind', '-b', default=None, type=str)
def serve(path: Path, bind: str):
    project = Project.load(path)

    click.echo(f'Serving project {project.name} in development mode')
    click.echo('THIS MODE SHOULD NOT BE USED IN PRODUCTION')

    args = ['serve-develop',  str(path / 'mapproxy.yaml'), '--debug']
    if bind is not None:
        args.append('-b')
        args.append(bind)

    run_env_binary(path, 'mapproxy-util', *args)


@cli.command(context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True,
))
@click.option('--path', default=workdir, type=Path)
@click.pass_context
def seed(ctx, path: Path):
    project = Project.load(path)

    click.echo(f'Serving project {project.name} in development mode')
    click.echo('THIS MODE SHOULD NOT BE USED IN PRODUCTION')

    args = [
        '-s', str(path / 'seeds.yaml'),
        '-f', str(path / 'mapproxy.yaml'),
        *ctx.args]

    run_env_binary(path, 'mapproxy-seed', *args)