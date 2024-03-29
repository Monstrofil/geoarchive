import logging
import urllib.parse
import warnings
from typing import TypedDict, Literal, NotRequired

from bs4 import BeautifulSoup

import requests
from slugify import slugify

from geoarchive.services.base import Layer, ServiceProtocol


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

        soup = BeautifulSoup(r.text, "html.parser")

        layers = []
        for layer in soup.find_all(attrs={'class': 'access-list__item'}):
            map_id = layer.find_next('input').attrs['map-layer']
            map_name = layer.find_next(attrs={'class': 'access-list__item_name'}).text

            url = f"/map/rtile/carto_{map_id}/ua/%(z)s/%(x)s/%(y)s.png"
            layers.append(Layer(
                name=slugify(map_name),
                type='tms',
                bounds=(21.225586, 44.318589, 40.363770, 52.709394),
                url=f"{self._url_parts.scheme}://{self._url_parts.hostname}{url}"
            ))

        return layers
