from pathlib import Path

import yaml

from geoarchive.config import TMSSourceConfig


def write_config(sources: list[TMSSourceConfig], path: Path):
    _write_config(path, sources)
    _write_seeds(path, sources)


def _write_config(path, sources):
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
        for layer in sources
    }
    layers = [
        dict(
            name=layer.name,
            sources=[
                f'cache-{layer.name}'
            ],
            title=layer.name
        )
        for layer in sources
    ]
    caches = {
        f'cache-{layer.name}': dict(
            cache=dict(type='compact', version=2),
            grids=['webmercator'],
            sources=[layer.name]
        )
        for layer in sources
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
    return sources


def _write_seeds(path, sources):
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
        for layer in sources
    }
    coverages = {
        layer.name: dict(
            bbox=list(layer.bounds),
            srs='EPSG:4326'
        )
        for layer in sources
    }
    seeds = dict(
        coverages=coverages,
        seeds=seeds
    )
    with open(path / 'seeds.yaml', 'w') as f:
        yaml.dump(seeds, f, default_flow_style=False)
