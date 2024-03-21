import logging
from pathlib import Path
from typing import Self

from geoarchive.config import ProjectConfig, TMSSourceConfig
from geoarchive.services.base import Layer


class Project(object):
    _CONFIG_FILE = 'geoproject.json'

    def __init__(self, config: ProjectConfig | None = None):
        self._config = config or ProjectConfig()

    def add_source(self, layer: Layer) -> None:
        assert layer.type == 'tms', f"Non tms ({layer.type}) is not supported right now"

        self._config.sources.append(TMSSourceConfig(
            name=layer.name, type=layer.type, url=layer.url, bounds=layer.bounds))

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

    @classmethod
    def load(cls, path: Path) -> Self:
        logging.info('Saving project %s', path)
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
        project.save(path)

        return project
