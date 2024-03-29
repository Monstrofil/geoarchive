import logging
import urllib.parse
import warnings
from typing import TypedDict, Literal, NotRequired

import requests
from slugify import slugify

from geoarchive.services.base import Layer, ServiceProtocol


class _SoftProLayer(TypedDict):
    id: str
    name: str
    category: str

    url: NotRequired[str]

    service: Literal['tms', 'vtile', 'geojson']
    bounds: NotRequired[str]


class SoftProService(ServiceProtocol):
    def __init__(self, url: str):
        self._url = url
        self._url_parts = urllib.parse.urlparse(self._url)

    def list_layers(self) -> list[Layer]:
        # a lot of services of this kind have a very strange
        # ssl certificates which are not always correctly set up
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            r = requests.get(self._url, verify=False)
            r.raise_for_status()

        response: list[_SoftProLayer] = r.json()

        layers = []
        for layer in response:
            if layer['service'].lower() != 'tms':
                logging.info('Skip %s layer because of incompatible type %s',
                             layer['name'], layer['service'])
                continue

            if layer.get('bounds') is None or not ',' in layer['bounds']:
                logging.info('Skip %s layer because of incompatible bounds', layer['name'])
                continue

            url = layer['url'].replace(
                '{z}', '%(z)s'
            ).replace(
                '{x}', '%(x)s'
            ).replace(
                '{y}', '%(y)s'
            )

            name_tokens = [
                token for token in (
                    layer['category'], layer['name']
                ) if token is not None
            ]
            layers.append(Layer(
                name=slugify(' '.join(name_tokens)),
                type='tms',
                bounds=tuple(map(float, layer['bounds'].split(','))),
                url=f"{self._url_parts.scheme}://{self._url_parts.hostname}{url}"
            ))

        return layers
