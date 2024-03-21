import os
import time
from pathlib import Path

import click
import pytermgui
from pytermgui import Container, Label, Splitter, Button, Checkbox, Window, Overflow
from pytermgui.widgets.boxes import Box

from geoarchive.project import Project

workdir = Path('.')


@click.group()
def cli():
    pass


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
        click.echo(f' - source type={source.type} cached={source.cached_at} refrest={source.refresh_interval}')


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
@click.option('--type', default='softpro', type=str, required=True)
@click.option('--url', type=str, required=True)
def import_sources(path: Path, type: str, url: str):
    project = Project.load(path)

    assert type == 'softpro', 'Unsupported source type'

    from geoarchive.services import get_service_protocol
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
def tui():
    import pytermgui as ptg

    def macro_time(fmt: str) -> str:
        return time.strftime(fmt)

    ptg.tim.define("!time", macro_time)

    with ptg.WindowManager() as manager:
        layout = manager.layout
        layout.add_slot("Header", height=5)
        layout.add_slot("Header Left", width=0.2)

        layout.add_break()

        layout.add_slot("Body Left", width=0.2)
        layout.add_slot("Body", width=0.7)
        layout.add_slot("Body Right")

        layout.add_break()

        layout.add_slot("Footer", height=3)


if __name__ == '__main__':
    cli()
