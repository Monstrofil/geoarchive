import logging
import subprocess
import sys
from pathlib import Path


def create_env(path: Path):
    logging.info('Creating environment')
    subprocess.run([
        sys.executable, '-m', 'venv', str(path / '.venv')
    ], check=True)

    logging.info('Installing dependencies')
    run_env_binary(path, 'pip3', 'install', 'mapproxy', 'pyproj')


def run_env_binary(path: Path, binary: str, *args) -> None:
    subprocess.run([
        str(path / '.venv' / 'bin' / binary), *args
    ], check=True)