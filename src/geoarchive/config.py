from datetime import datetime
from typing import Literal, List

import pydantic


class TMSSourceConfig(pydantic.BaseModel):
    type: Literal['tms']
    url: str

    created_at: datetime = pydantic.Field(default_factory=datetime.now)
    cached_at: datetime | None = None


class WMSSourceConfig(pydantic.BaseModel):
    type: Literal['wms']


class ProjectConfig(pydantic.BaseModel):
    name: str

    sources: List[TMSSourceConfig] = pydantic.Field(
        ..., discriminator='type', default_factory=list)
