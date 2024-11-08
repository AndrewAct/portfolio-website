# services/url_shortener/router.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from typing import Dict
from .schemas import URLBase, URLResponse, DeleteURLRequest
from .service import URLShortenerService
import logging

logger = logging.getLogger("url_shortener")

# Create two separate routers
redirect_router = APIRouter()  # For redirect routes
api_router = APIRouter()       # For API endpoints

url_shortener_service = URLShortenerService()


# Redirect route on redirect_router
@redirect_router.get("/r/{short_url}")
async def redirect_to_original_url(short_url: str) -> RedirectResponse:
    """
    Redirect to the original URL using the short url code
    """
    try:
        logger.info(f"Redirecting short url code: {short_url}")
        original_url = await url_shortener_service.get_original_url(short_url)

        if not original_url.startswith(('http://', 'https://')):
            original_url = 'https://' + original_url

        logger.info(f"Redirecting to: {original_url}")
        return RedirectResponse(url=original_url, status_code=302)
    except Exception as e:
        logger.error(f"Error redirecting {short_url}: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"URL not found for code: {short_url}"
        )


# API routes on api_router
@api_router.post("", response_model=URLResponse)
async def create_short_url(url_request: URLBase) -> URLResponse:
    try:
        logger.info(f"Creating short URL for: {url_request.url}")
        response = await url_shortener_service.create_short_url(url_request.url)
        return response
    except Exception as e:
        logger.error(f"Error creating short URL: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create short URL: {str(e)}"
        )


@api_router.get("/{short_url}")
async def get_original_url(short_url: str) -> Dict[str, str]:
    try:
        logger.info(f"Getting original URL for code: {short_url}")
        original_url = await url_shortener_service.get_original_url(short_url)
        return {"original_url": original_url}
    except Exception as e:
        logger.error(f"Error retrieving URL for code {short_url}: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"URL not found for code: {short_url}"
        )


# @api_router.delete("/{short_url}")
@api_router.delete("/")
async def delete_url(request: DeleteURLRequest,) -> Dict[str, str]:
    try:
        logger.info(f"Deleting URL mapping for code: {request.url}")
        await url_shortener_service.delete_url(request.url)
        return {"message": "URL mapping deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting URL mapping: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Failed to delete URL mapping: {str(e)}"
        )


@api_router.get("")
async def get_service_info() -> Dict[str, str]:
    """
    Get information about the URL shortener service.

    Returns:
        Dict containing service information
    """
    return {
        "service": "URL Shortener",
        "version": "0.0.1",
        "base_url": "andrewcee.io/",
        "endpoints": {
            "create": "POST /",
            "redirect": "GET /r/{short_url}",
            "retrieve": "GET /{short_url}",
            "delete": "DELETE /{short_url}",
            "info": "GET /"
        }
    }