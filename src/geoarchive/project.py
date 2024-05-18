import logging
from pathlib import Path
from typing import Self

from geoarchive import environment, mapproxy
from geoarchive.config import (
    ProjectConfig,
    TMSSourceConfig,
    ArcgisSourceConfig,
    ProjectConfigDynamic, CacheConfig
)
from geoarchive.services.base import Layer


class Project(object):
    _CONFIG_FILE = 'geoproject.json'

    def __init__(self, config: ProjectConfig | None = None):
        self._config = config or ProjectConfig()

    def add_source(self, layer: Layer) -> None:
        exiting_layer = self._config.sources.get(layer.name)

        logging.info('Layer %s does not exists, adding new', layer.name)
        if layer.type == 'tms':
            source = TMSSourceConfig(
                name=layer.name, type=layer.type,
                url=layer.url, bounds=layer.bounds,
                bounds_srid=layer.bounds_srid,
                opts=layer.opts
            )
        elif layer.type == 'arcgis':
            source = ArcgisSourceConfig(
                name=layer.name, type=layer.type,
                url=layer.url, bounds=layer.bounds,
                bounds_srid=layer.bounds_srid,
                opts=layer.opts
            )
        else:
            raise NotImplementedError('Unsupported layer %s' % layer.type)

        self._config.sources[source.name] = source

    def get_sources(self) -> dict[str, TMSSourceConfig]:
        return self._config.sources

    def get_caches(self) -> dict[str, CacheConfig]:
        return self._config.caches

    def remove_source(self, name: str):
        ...

    def add_cache(self, cache_id: str, base_layers: list[str]) -> None:
        project_sources = self.get_sources()
        for layer in base_layers:
            if project_sources.get(layer) is None:
                raise FileNotFoundError('Layer `%s` does not exist' % layer)

        self._config.caches[cache_id] = CacheConfig(
            name=cache_id, sources=base_layers)

    def remove_cache(self, cache_id: str):
        del self._config.caches[cache_id]

    @property
    def name(self) -> str:
        return self._config.name

    def save(self, path: Path):
        logging.info('Saving project %s', path)
        with open(path / self._CONFIG_FILE, 'w') as f:
            f.write(self._config.model_dump_json(indent=2))

        mapproxy.write_config(
            self._config.sources.values(),
            path,
            additional_caches=list(self._config.caches.values())
        )

    @classmethod
    def load(cls, path: Path) -> Self:
        logging.info('Loading project %s', path)
        config_file = path / cls._CONFIG_FILE
        if not config_file.exists():
            raise FileNotFoundError(config_file)

        configuration = ProjectConfigDynamic.validate_json(config_file.read_text())
        # loop while we can upgrade config to never version
        while upgraded := configuration.upgrade():
            configuration = upgraded

        return cls(config=configuration)

    @classmethod
    def create(cls, path: Path, name: str, create_environment = True) -> Self:
        logging.info('Creating project %s', path)
        config_file = path / cls._CONFIG_FILE
        if config_file.exists():
            logging.info('Project %s already exists', path)
            raise FileExistsError(config_file)

        path.mkdir(parents=True, exist_ok=True)

        configuration = ProjectConfig(name=name)
        project = cls(config=configuration)
        if create_environment:
            environment.create_env(path)
        project.save(path)

        return project

    def upgrade(self, path: Path) -> None:
        logging.info('Upgrading project %s', path)
        environment.update_env(path)
