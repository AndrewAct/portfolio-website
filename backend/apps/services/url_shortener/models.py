from datetime import datetime

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field


class URLMapping(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    short_url: str
    original_url: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
