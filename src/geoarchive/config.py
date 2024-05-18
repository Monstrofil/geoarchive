from datetime import datetime
from typing import Literal, List, Annotated

import pydantic
from pydantic import TypeAdapter, Field


class CacheConfig(pydantic.BaseModel):
    name: str
    sources: list[str]

    grids: list[str] = pydantic.Field(default_factory=lambda: ['webmercator'])


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


class ProjectConfigV2(pydantic.BaseModel):
    name: str

    sources: dict[str, TMSSourceConfig | ArcgisSourceConfig] = pydantic.Field(
        ..., discriminator='type', default_factory=dict)

    caches: dict[str, CacheConfig] = pydantic.Field(
        ..., default_factory=dict
    )

    version: Literal[2] = 2

    def upgrade(self) -> None:
        return None


class ProjectConfigV1(pydantic.BaseModel):
    name: str

    sources: List[TMSSourceConfig | ArcgisSourceConfig] = pydantic.Field(
        ..., discriminator='type', default_factory=list)

    version: Literal[1] = 1

    def upgrade(self) -> ProjectConfigV2:
        return ProjectConfigV2(
            name=self.name,
            sources={
                source.name: source
                for source in self.sources
            }
        )


_ProjectConfig = ProjectConfigV1 | ProjectConfigV2
_AnnotatedProjectConfig = Annotated[_ProjectConfig, Field(discriminator="version")]
ProjectConfigDynamic: TypeAdapter[_ProjectConfig] = TypeAdapter(_AnnotatedProjectConfig)
ProjectConfig = ProjectConfigV2  # keep reference to the latest here
