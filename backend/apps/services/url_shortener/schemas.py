from pydantic import BaseModel
from datetime import datetime


class URLBase(BaseModel):
    url: str


class URLResponse(BaseModel):
    original_url: str
    shortened_url: str
    created_at: datetime
