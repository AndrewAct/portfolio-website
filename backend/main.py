from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import feedparser
from typing import List, Optional
from pydantic import BaseModel
import xml.etree.ElementTree as ET
from datetime import datetime
import re

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MediumPost(BaseModel):
    title: str
    link: str
    author: str
    published_date: str
    content: str
    reading_time: int
    # thumbnail: Optional[str] = None


@app.get("/")
def hello_world():
    return {"Hello": "World"}


@app.get("/api/medium-posts/{username}", response_model=List[MediumPost])
async def get_medium_posts(username: str = "andrewact"):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://medium.com/feed/@{username}")
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="Medium feed not found")

        feed = feedparser.parse(response.text)
        posts = []

        for entry in feed.entries:
            # Extract content from either 'content' list or 'summary' field
            content = ""
            if hasattr(entry, 'content') and len(entry.content) > 0:
                content = entry.content[0].value
            elif hasattr(entry, 'summary'):
                content = entry.summary

            # Extract thumbnail
            # thumbnail = None
            # img_match = re.search(r'<img[^>]+src="([^">]+)"', content)
            # if img_match:
            #     thumbnail = img_match.group(1)

            # Calculate reading time (rough estimate: 200 words per minute)
            content_text = re.sub(r'<[^>]+>', '', content)
            word_count = len(content_text.split())
            reading_time = max(1, round(word_count / 200))

            post = MediumPost(
                title=entry.title,
                link=entry.link,
                author=entry.author,
                published_date=datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %Z").isoformat(),
                content=content,
                reading_time=reading_time
                # thumbnail=thumbnail
            )
            posts.append(post)

        return posts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))