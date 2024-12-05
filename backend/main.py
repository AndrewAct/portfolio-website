from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# from apps.services.url_shortener.router import router as url_shortener_router
from apps.services.url_shortener.router import redirect_router, api_router
# from apps.services.medium_posts.router import router as medium_posts_router // To be implemented
from apps.services.url_shortener.database import init_db, close_db
from apps.core.logger import setup_logging
from apps.monitoring.telemetry import setup_telemetry
# from apps.monitoring.prometheus import PrometheusMiddleware
# from apps.monitoring.middleware import PrometheusMiddleWare
from apps.monitoring.prometheus import router as metrics_router
from apps.monitoring.middleware import PrometheusMiddleware
from apps.monitoring.metrics_collector import MetricsCollector
import httpx
import feedparser
from typing import List, Optional
from pydantic import BaseModel
import xml.etree.ElementTree as ET
from datetime import datetime
import re
import os

# Setup logging
logger = setup_logging()

app = FastAPI(
    title="Andrew's Portfolio Website",
    description="Collection of utility services including URL shortener and Medium posts fetcher",
    version="0.0.1"
)

# Get environment type (development or production)
ENV = os.getenv("ENV", "development")

if ENV == "development":
    origins = [
        "http://localhost:4200",  # Angular dev server
        "http://localhost:80",    # Docker frontend port
        "http://127.0.0.1:4200",
        "http://127.0.0.1:80",
    ]
else:  # production
    origins = [
        "https://andrewcee.io",
        "http://andrewcee.io",
    ]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    # allow_origins=[
    #     "http://localhost:4200",  # Development mode
    #     "https://andrewcee.io"  # Production mode
    # ],  # Add your frontend URL
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
    return {
        "message": "Welcome to Andrew's Portfolio Website",
        "version": "0.0.1",
        "services": [
            "URL Shortener",
            "Medium Posts Fetcher"
        ]
    }


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


@app.get("/utilities")
def get_utilities():
    return {"Hello": "World"}


# Mount the redirect router at root level
app.include_router(
    redirect_router,
    tags=["URL Shortener Redirect"]
)

# Mount the API router with prefix
app.include_router(
    api_router,
    prefix="/utilities/url_shortener",
    tags=["URL Shortener API"]
)


# Add observability with OpenTelemetry
setup_telemetry(app)

# Add metrics endpoint
app.include_router(metrics_router, tags=['Monitoring'])

# Integrate middleware
app.middleware("http")(PrometheusMiddleware())
# app.add_middleware(PrometheusMiddleware)

metrics_collector = MetricsCollector(app, collection_interval=60)  # Collect on minute basis
metrics_collector.start()

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing database connection...")
    await init_db()


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Closing database connection...")
    await close_db()