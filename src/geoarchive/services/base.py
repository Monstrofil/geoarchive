import typing
from typing import Literal

import pydantic


class Layer(pydantic.BaseModel):
    name: str
    type: Literal['tms', 'wms', 'arcgis']
    url: str

    bounds: tuple[float, float, float, float]
    bounds_srid: str = 'EPSG:4326'

    opts: dict | None = None


class ServiceProtocol(typing.Protocol):

    def __init__(self, url):
        ...

    def list_layers(self) -> list[Layer]:
        ...
