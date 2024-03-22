import logging
import subprocess
from pathlib import Path
from typing import Self

import yaml

from geoarchive import environment
from geoarchive.config import ProjectConfig, TMSSourceConfig
from geoarchive.services.base import Layer


class Project(object):
    _CONFIG_FILE = 'geoproject.json'

    def __init__(self, config: ProjectConfig | None = None):
        self._config = config or ProjectConfig()

    def add_source(self, layer: Layer) -> None:
        assert layer.type == 'tms', \
            f"Non tms ({layer.type}) is not supported right now"

        try:
            exiting_layer = next(layer for name in self._config.sources if name == layer.name)
        except StopIteration:
            exiting_layer = None

        if exiting_layer is None:
            logging.info('Layer %s does not exists, adding new', layer.name)
            self._config.sources.append(TMSSourceConfig(
                name=layer.name, type=layer.type,
                url=layer.url, bounds=layer.bounds
            ))
        else:
            logging.info('Layer %s already exists, updating', layer.name)
            exiting_layer.url = layer.url
            exiting_layer.bounds = layer.bounds

    def get_sources(self) -> list[TMSSourceConfig]:
        return self._config.sources

    def remove_source(self, name: str):
        ...

    @property
    def name(self) -> str:
        return self._config.name

    def save(self, path: Path):
        logging.info('Saving project %s', path)
        with open(path / self._CONFIG_FILE, 'w') as f:
            f.write(self._config.model_dump_json(indent=2))

        sources = {
            layer.name: dict(
                coverage=dict(
                    bbox=list(layer.bounds),
                    srs='EPSG:4326'
                ),
                http=dict(
                    ssl_no_cert_checks=True
                ),
                grid='GLOBAL_WEBMERCATOR',
                type='tile',
                url=layer.url
            )
            for layer in self._config.sources
        }

        layers = [
            dict(
                name=layer.name,
                sources=[
                    f'cache-{layer.name}'
                ],
                title=layer.name
            )
            for layer in self._config.sources
        ]

        caches = {
            f'cache-{layer.name}': dict(
                cache=dict(type='compact', version=2),
                grids=['webmercator'],
                sources=[layer.name]
            )
            for layer in self._config.sources
        }

        services = dict(
            demo=dict(),
            tms=dict()
        )

        config = dict(
            sources=sources,
            layers=layers,
            caches=caches,
            services=services,
            grids=dict(
                webmercator=dict(base='GLOBAL_WEBMERCATOR')
            )
        )

        with open(path / 'mapproxy.yaml', 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

        seeds = {
            layer.name: dict(
                caches=[
                    f'cache-{layer.name}'
                ],
                coverages=[
                    layer.name
                ],
                levels=dict(
                    to=16
                )
            )
            for layer in self._config.sources
        }

        coverages = {
            layer.name: dict(
                bbox=list(layer.bounds),
                srs='EPSG:4326'
            )
            for layer in self._config.sources
        }

        seeds = dict(
            coverages=coverages,
            seeds=seeds
        )

        with open(path / 'seeds.yaml', 'w') as f:
            yaml.dump(seeds, f, default_flow_style=False)

    @classmethod
    def load(cls, path: Path) -> Self:
        logging.info('Loading project %s', path)
        config_file = path / cls._CONFIG_FILE
        if not config_file.exists():
            raise FileNotFoundError(config_file)

        configuration = ProjectConfig.parse_file(config_file)
        return cls(config=configuration)

    @classmethod
    def create(cls, path: Path, name: str) -> Self:
        logging.info('Creating project %s', path)
        config_file = path / cls._CONFIG_FILE
        if config_file.exists():
            logging.info('Project %s already exists', path)
            raise FileExistsError(config_file)

        path.mkdir(parents=True, exist_ok=True)

        configuration = ProjectConfig(name=name)
        project = cls(config=configuration)
        environment.create_env(path)
        project.save(path)

        return project
