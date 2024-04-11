import logging
import urllib.parse
import warnings
from typing import TypedDict, Literal, NotRequired

import requests
from slugify import slugify

from geoarchive.services.base import Layer, ServiceProtocol


class ExtentInfo(TypedDict):
    xmin: float
    ymin: float
    xmax: float
    ymax: float


class LayerListItem(TypedDict):
    id: int
    name: str
    parentLayerId: int
    defaultVisibility: bool
    subLayerIds: list[int]
    minScale: int
    maxScale: int
    type: str


class LayerResponse(TypedDict):
    id: int
    name: str
    type: str
    extent: ExtentInfo


class MapServiceResponse(TypedDict):
    serviceDescription: str
    tileInfo: NotRequired[dict]
    mapName: str

    layers: list[LayerResponse]

    fullExtent: ExtentInfo

    minLOD: int
    maxLOD: int


class ArcGisProtocol(ServiceProtocol):
    def __init__(self, url: str):
        self._url = url
        self._url_parts = urllib.parse.urlparse(self._url)

    def _request_service(self, service_url: str) -> MapServiceResponse:
        logging.info('Requesting service: %s', service_url)
        # a lot of services of this kind have a very strange
        # ssl certificates which are not always correctly set up
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            r = requests.get(service_url, params={'f': 'json'}, verify=False)
            r.raise_for_status()

        result = r.json()
        if result.get('error'):
            raise PermissionError(result['error']['message'])

        return result

    def _request_layer(self, service_url: str, layer_id: int) -> LayerResponse:
        logging.info('Requesting layer: %s/%s', service_url, layer_id)
        # a lot of services of this kind have a very strange
        # ssl certificates which are not always correctly set up
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            r = requests.get(f'{service_url}/{layer_id}', params={'f': 'json'}, verify=False)
            r.raise_for_status()

        result = r.json()
        if result.get('error'):
            raise PermissionError(result['error']['message'])

        return result

    def list_layers(self) -> list[Layer]:
        layers = []

        try:
            service_data = self._request_service(self._url)
        except PermissionError:
            logging.warning('Skip service %s because of permission error', self._url)
            return []

        name_tokens = [
            service_data['mapName'],
            service_data['serviceDescription']
        ]

        for layer in service_data['layers']:
            url = self._url
            proxy_type = 'arcgis'

            layer_data = self._request_layer(self._url, layer_id=layer['id'])

            extent = layer_data['extent']
            min_x, min_y, max_x, max_y = extent['xmin'], extent['ymin'], extent['xmax'], extent['ymax']

            layer_name_tokens = name_tokens.copy()
            layer_name_tokens.append(layer_data['name'])
            layer_name_tokens.append(str(layer_data['id']))

            if extent['spatialReference'].get('wkid'):
                srid = f"EPSG:{extent['spatialReference']['wkid']}"
            else:
                srid = extent['spatialReference']['wkt']

            layers.append(Layer(
                name=slugify(' '.join(layer_name_tokens)),
                type=proxy_type,
                bounds=(min_x, min_y, max_x, max_y),
                bounds_srid=srid,
                url=url,
                opts=dict(
                    layers=f'show:{layer["id"]}',
                    official_name=f"{service_data['mapName']}/{layer_data['name']}"
                )
            ))

        return layers
