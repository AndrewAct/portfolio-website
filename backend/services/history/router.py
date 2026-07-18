# import datetime
import re
from datetime import datetime

import feedparser
import httpx
from fastapi import APIRouter, HTTPException
from schemas import MediumPost

router = APIRouter()


@router.get("/api/medium-posts/{username}", response_model=list[MediumPost])
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
            if hasattr(entry, "content") and len(entry.content) > 0:
                content = entry.content[0].value
            elif hasattr(entry, "summary"):
                content = entry.summary

            # Calculate reading time (rough estimate: 200 words per minute)
            content_text = re.sub(r"<[^>]+>", "", content)
            word_count = len(content_text.split())
            reading_time = max(1, round(word_count / 200))

            post = MediumPost(
                title=entry.title,
                link=entry.link,
                author=entry.author,
                published_date=datetime.strptime(
                    entry.published, "%a, %d %b %Y %H:%M:%S %Z"
                ).isoformat(),
                content=content,
                reading_time=reading_time,
                # thumbnail=thumbnail
            )
            posts.append(post)

        return posts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
