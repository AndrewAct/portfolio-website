from datetime import datetime

from pydantic import BaseModel


class URLBase(BaseModel):
    url: str


class URLResponse(BaseModel):
    original_url: str
    shortened_url: str
    created_at: datetime


class DeleteURLRequest(BaseModel):
    url: str
