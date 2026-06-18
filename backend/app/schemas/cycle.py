from pydantic import BaseModel

from app.schemas.common import Priority


class CycleRead(BaseModel):
    id: int
    name: str
    slug: str
    color: str | None
    priority: Priority

    model_config = {"from_attributes": True}


class CycleUpdate(BaseModel):
    color: str | None = None
    priority: Priority | None = None
