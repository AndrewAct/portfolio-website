import logging
import random
import string
from datetime import datetime
from typing import Any

import validators

# import validators
from fastapi import HTTPException

from .database import get_collection
from .models import URLMapping
from .schemas import URLResponse

# Create logger
logger = logging.getLogger("url_shortener")


class URLShortenerService:
    ## Not deployed yet, testing with localhost
    # def __init__(self, domain: str = "localhost:8000"):

    # If deployed (in production mode), change to andrewcee.io
    def __init__(self, domain: str = "andrewcee.io", collection: Any = None):
        self.domain = domain
        self.collection = collection if collection is not None else get_collection()

    def generate_short_url(self, length: int = 6) -> str:
        characters = string.ascii_letters + string.digits
        return "".join(random.choice(characters) for _ in range(length))

    async def create_short_url(self, url: str) -> URLResponse:
        # Validate URL format
        if not validators.url(url):
            # Try to add 'https://' if the URL does not have a prefix
            if validators.url("https://" + url):
                url = "https://" + url
            else:
                raise HTTPException(status_code=400, detail="Invalid URL format")

        # First, check if this URL already exists in the database
        existing_mapping = await self.collection.find_one({"original_url": url})

        if existing_mapping is not None:
            logger.info(f"Found existing shortened URL for: {url}")
            return URLResponse(
                original_url=existing_mapping["original_url"],
                shortened_url=existing_mapping["short_url"],
                created_at=existing_mapping["created_at"],
            )

        # Generate a code that is not already in use.
        while True:
            short_url = self.generate_short_url()
            logger.info(f"Short url: {short_url}")
            if not await self.collection.find_one({"short_url": short_url}):
                break

        url_mapping = URLMapping(
            short_url=f"{self.domain}/r/{short_url}",
            original_url=url,
            created_at=datetime.utcnow(),
        )
        await self.collection.insert_one(url_mapping.model_dump(by_alias=True))

        return URLResponse(
            original_url=url,
            shortened_url=url_mapping.short_url,
            created_at=url_mapping.created_at,
        )

    # async def get_original_url(self, short_url: str) -> str:
    #     url_mapping = await self.collection.find_one({"short_url": short_url})
    #     if not url_mapping:
    #         raise HTTPException(status_code=404, detail="URL not found")
    #     return url_mapping["original_url"]
    async def get_original_url(self, short_url: str) -> str:
        """
        Get the original URL for a given short code.
        Only uses the code part of the short URL for lookup.
        """
        # Clean the short_url to get just the code
        # Remove any full URL if present, we just want the code
        if "/" in short_url:
            short_url = short_url.split("/")[-1]

        # Remove any quotes that might have been added
        short_url = short_url.replace('"', "")

        logger.info(f"Looking up code: {short_url}")

        # Look up using the full URL pattern
        url_mapping = await self.collection.find_one({"short_url": f"{self.domain}/r/{short_url}"})

        if not url_mapping:
            logger.error(f"No URL mapping found for code: {short_url}")
            raise HTTPException(status_code=404, detail="URL not found")

        logger.info(f"Found original URL: {url_mapping['original_url']}")
        return url_mapping["original_url"]

    async def delete_url(self, short_url: str) -> bool:
        result = await self.collection.delete_one({"short_url": short_url})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="URL not found")
        return True
