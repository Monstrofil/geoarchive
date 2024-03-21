import logging
from pathlib import Path
from typing import Self

from geoarchive.config import ProjectConfig, TMSSourceConfig


class Project(object):
    _CONFIG_FILE = 'geoproject.json'

    def __init__(self, config: ProjectConfig | None = None):
        self._config = config or ProjectConfig()

    def add_source(self, type: str, name: str, url: str) -> None:
        assert type == 'tms', "Non tms is not supported right now"

        self._config.sources.append(TMSSourceConfig(
            name=name, type=type, url=url))

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
