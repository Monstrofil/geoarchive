import logging
import urllib.parse
import warnings
from typing import TypedDict, Literal, NotRequired

import requests
from slugify import slugify

from geoarchive.services.base import Layer, ServiceProtocol


class ArcGisService(TypedDict):
    name: str
    type: Literal['MapServer', 'FeatureServer']


class FolderResponse(TypedDict):
    folders: list[str]
    services: list[ArcGisService]


class Lod(TypedDict):
    level: int
    resolution: float
    scale: float


class TileInfo(TypedDict):
    lods: list[Lod]


class ExtentInfo(TypedDict):
    xmin: float
    ymin: float
    xmax: float
    ymax: float


class MapServiceResponse(TypedDict):
    serviceDescription: str
    tileInfo: NotRequired[dict]

    fullExtent: ExtentInfo

    minLOD: int
    maxLOD: int


class ArcGisProtocol(ServiceProtocol):
    def __init__(self, url: str):
        self._url = url
        self._url_parts = urllib.parse.urlparse(self._url)

    def _traverse_folders(self, url: str, folders: list[str]):
        for folder in folders:
            logging.info('Traversing folder: %s', folder)

            folder_url = url + '/' + folder
            try:
                response = self._request_folder(folder_url)
            except PermissionError:
                logging.warning('Skip folder %s because of permission error', folder)
                continue

            yield from self._collect_services(folder_url, response)

    def _collect_services(self, url: str, response: FolderResponse):
        yield from self._traverse_folders(self._url, response['folders'])

        for service in response['services']:
            yield ArcGisService(**service)

    def _request_folder(self, url: str) -> FolderResponse:
        logging.info('Requesting folder: %s', url)
        # a lot of services of this kind have a very strange
        # ssl certificates which are not always correctly set up
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            r = requests.get(url, params={'f': 'json'}, verify=False)
            r.raise_for_status()

        result = r.json()
        if result.get('error'):
            raise PermissionError(result['error']['message'])

        return result

    def _request_service(self, root_url: str, service: ArcGisService) -> MapServiceResponse:
        service_url = root_url + '/' + service['name'] + '/MapServer'
        logging.info('Requesting folder: %s', service_url)
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

    def list_layers(self) -> list[Layer]:
        layers = []

        response = self._request_folder(url=self._url)
        services = list(self._collect_services(self._url, response))
        for service in services:
            if service['type'] != 'MapServer':
                logging.info('Skip layer %s because of type %s', service['name'], service['type'])
                continue

            try:
                service_data = self._request_service(self._url, service)
            except PermissionError:
                logging.warning('Skip service %s because of permission error', service['name'])
                continue

            name_tokens = [
                service['name'],
                service_data['serviceDescription']
            ]
            extent = service_data['fullExtent']
            min_x, min_y, max_x, max_y = extent['xmin'], extent['ymin'], extent['xmax'], extent['ymax']

            if service_data.get('tileInfo'):
                url = f'{self._url}/{service["name"]}/MapServer/tile/{{z}}/{{y}}/{{x}}'
                proxy_type = 'tms'
            else:
                url = f'{self._url}/{service["name"]}/MapServer'
                proxy_type = 'arcgis'

            if extent['spatialReference'].get('wkid'):
                srid = f"EPSG:{extent['spatialReference']['wkid']}"
            else:
                srid = extent['spatialReference']['wkt']

            layers.append(Layer(
                name=slugify(' '.join(name_tokens)),
                type=proxy_type,
                bounds=(min_x, min_y, max_x, max_y),
                bounds_srid=srid,
                url=url
            ))

        return layers
