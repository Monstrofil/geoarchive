import logging
from pathlib import Path
from typing import Self

from geoarchive import environment, mapproxy
from geoarchive.config import ProjectConfig, TMSSourceConfig, ArcgisSourceConfig
from geoarchive.services.base import Layer


class Project(object):
    _CONFIG_FILE = 'geoproject.json'

    def __init__(self, config: ProjectConfig | None = None):
        self._config = config or ProjectConfig()

    def add_source(self, layer: Layer) -> None:
        try:
            exiting_layer = next(source for source in self._config.sources if source.name == layer.name)
        except StopIteration:
            exiting_layer = None

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

        if exiting_layer is not None:
            self._config.sources.remove(exiting_layer)
        self._config.sources.append(source)

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

        mapproxy.write_config(self._config.sources, path)

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

    def upgrade(self, path: Path) -> None:
        logging.info('Upgrading project %s', path)
        environment.update_env(path)
