from pathlib import Path

import yaml

from geoarchive.config import TMSSourceConfig


def write_config(sources: list[TMSSourceConfig], path: Path):
    _write_config(path, sources)
    _write_seeds(path, sources)


def _write_config(path, configured_sources: list[TMSSourceConfig]):
    sources = {}
    for layer in configured_sources:
        if layer.type == 'tms':
            configration = dict(
                coverage=dict(
                    bbox=list(layer.bounds),
                    srs=layer.bounds_srid
                ),
                http=dict(
                    ssl_no_cert_checks=True
                ),
                grid='GLOBAL_WEBMERCATOR',
                type='tile',
                url=layer.url,
                on_error={
                    404: dict(
                        response='transparent',
                        cache=True
                    )
                }
            )
        elif layer.type == 'arcgis':
            configration = dict(
                coverage=dict(
                    bbox=list(layer.bounds),
                    srs=layer.bounds_srid
                ),
                http=dict(
                    ssl_no_cert_checks=True
                ),
                supported_srs=[layer.bounds_srid],
                type='arcgis',
                req=dict(
                    url=layer.url
                ),
                on_error={
                    404: dict(
                        response='transparent',
                        cache=True
                    )
                }
            )
        else:
            raise NotImplementedError("Unsupported layer %s" % layer.type)

        sources[layer.name] = configration

    layers = [
        dict(
            name=layer.name,
            sources=[
                f'cache-{layer.name}'
            ],
            title=layer.name
        )
        for layer in configured_sources
    ]
    caches = {
        f'cache-{layer.name}': dict(
            cache=dict(type='compact', version=2),
            grids=['webmercator'],
            sources=[layer.name]
        )
        for layer in configured_sources
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
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    return sources


def _write_seeds(path, configured_sources: list[TMSSourceConfig]):
    seeds = {
        layer.name: dict(
            caches=[
                f'cache-{layer.name}'
            ],
            coverages=[
                layer.name
            ],
            levels=dict(
                to=18
            )
        )
        for layer in configured_sources
    }
    coverages = {
        layer.name: dict(
            bbox=list(layer.bounds),
            srs=layer.bounds_srid
        )
        for layer in configured_sources
    }
    seeds = dict(
        coverages=coverages,
        seeds=seeds
    )
    with open(path / 'seeds.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(seeds, f, default_flow_style=False, allow_unicode=True)
