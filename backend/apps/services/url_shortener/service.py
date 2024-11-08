import logging
import string
import random
# import validators
from fastapi import HTTPException
from datetime import datetime
from .models import URLMapping
from .database import get_collection
from .schemas import URLResponse, DeleteURLRequest
import validators
import sys
import logging

# Create logger
logger = logging.getLogger("url_shortener")


# print("Python path:", sys.path)
#
# try:
#     import validators
#     print("Successfully imported validators version:", validators.__version__)
# except ImportError as e:
#     print("Failed to import validators:", str(e))
#     print("Python path:", sys.path)


class URLShortenerService:
    # def __init__(self, domain: str = "andrewcee.io"):
    ## Not deployed yet, testing with localhost
    def __init__(self, domain: str = "localhost:8000"):
        self.domain = domain
        self.collection = get_collection()

    def generate_short_url(self, length: int = 6) -> str:
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

    async def create_short_url(self, url: str) -> URLResponse:
        # Validate URL format
        if not validators.url(url):
            # Try to add 'https://' if the URL does not have a prefix
            if validators.url('https://' + url):
                url = 'https://' + url
            else:
                raise HTTPException(status_code=400, detail="Invalid URL format")

        # First, check if this URL already exists in the database
        existing_mapping = await self.collection.find_one({"original_url": url})

        if existing_mapping:
            logger.info(f"Found existing shortened URL for: {url}")
            return URLResponse(
                original_url=existing_mapping["original_url"],
                shortened_url=existing_mapping["short_url"],
                created_at=existing_mapping["created_at"]
            )
        else:
            # Generate unique short url
            while True:
                short_url = self.generate_short_url()
                logger.info(f"Short url: {short_url}")
                if not await self.collection.find_one({"short_url": short_url}):
                    break

            # Create URL mapping
            url_mapping = URLMapping(
                short_url=f"{self.domain}/r/{short_url}",
                original_url=url,
                created_at=datetime.utcnow()
            )

            # Save to database
            await self.collection.insert_one(url_mapping.dict(by_alias=True))

            # Return the complete shortened URL
            return URLResponse(
                original_url=url,
                shortened_url=f"{self.domain}/r/{short_url}",
                created_at=url_mapping.created_at
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
        if '/' in short_url:
            short_url = short_url.split('/')[-1]

        # Remove any quotes that might have been added
        short_url = short_url.replace('"', '')

        logger.info(f"Looking up code: {short_url}")

        # Look up using the full URL pattern
        url_mapping = await self.collection.find_one({
            "short_url": f"{self.domain}/r/{short_url}"
        })

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