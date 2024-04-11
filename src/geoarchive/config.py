from datetime import datetime
from typing import Literal, List

import pydantic


class TMSSourceConfig(pydantic.BaseModel):
    type: Literal['tms']
    url: str
    name: str

    bounds: tuple[float, float, float, float]
    bounds_srid: str = 'EPSG:4326'

    created_at: datetime = pydantic.Field(default_factory=datetime.now)
    cached_at: datetime | None = None

    refresh_interval: int | None = None
    opts: dict | None = None


class ArcgisSourceConfig(pydantic.BaseModel):
    type: Literal['arcgis']
    url: str
    name: str

    bounds: tuple[float, float, float, float]
    bounds_srid: str = 'EPSG:4326'

    created_at: datetime = pydantic.Field(default_factory=datetime.now)
    cached_at: datetime | None = None

    refresh_interval: int | None = None
    opts: dict | None = None


class WMSSourceConfig(pydantic.BaseModel):
    type: Literal['wms']


class ProjectConfig(pydantic.BaseModel):
    name: str

    sources: List[TMSSourceConfig | ArcgisSourceConfig] = pydantic.Field(
        ..., discriminator='type', default_factory=list)

    version: int = 1
