import typing
from typing import Literal

import pydantic


class Layer(pydantic.BaseModel):
    name: str
    type: Literal['tms', 'wms']
    url: str

    bounds: tuple[float, float, float, float]
    bounds_srid: str = 'EPSG:4326'


class ServiceProtocol(typing.Protocol):

    def __init__(self, url):
        ...

    def list_layers(self) -> list[Layer]:
        ...
