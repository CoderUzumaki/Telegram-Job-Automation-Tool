from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Setting(BaseModel):
    key: str
    value_json: dict[str, Any] = Field(default_factory=dict)
    version: int = 1
    updated_at: datetime | None = None
