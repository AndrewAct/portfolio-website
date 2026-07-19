from pydantic import BaseModel


class MediumPost(BaseModel):
    title: str
    link: str
    author: str
    published_date: str
    content: str
    reading_time: int
    # thumbnail: Optional[str] = None
