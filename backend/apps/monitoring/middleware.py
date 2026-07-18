import re
import time

from fastapi import Request

from .prometheus import track_metrics


def normalize_endpoint(path: str) -> str:
    """
    Normalize endpoint paths to reduce label cardinality.
    Replaces dynamic path segments (like IDs, UUIDs, short URLs) with placeholders.

    Examples:
        /r/abc123 -> /r/{short_url}
        /utilities/url_shortener/xyz789 -> /utilities/url_shortener/{short_url}
        /api/medium-posts/username -> /api/medium-posts/{username}
        /utilities/horoscope -> /utilities/horoscope (unchanged)
    """
    # Skip normalization for static paths
    if path in ["/", "/health", "/metrics", "/utilities"]:
        return path

    # Normalize URL shortener redirect paths: /r/{short_url}
    if path.startswith("/r/") and len(path) > 3:
        return "/r/{short_url}"

    # Normalize URL shortener API paths: /utilities/url_shortener/{short_url}
    if path.startswith("/utilities/url_shortener/"):
        # Check if it's a dynamic path (has a short_url segment)
        parts = path.split("/")
        # /utilities/url_shortener has 4 parts: ['', 'utilities', 'url_shortener', '']
        # /utilities/url_shortener/abc123 has 5 parts: ['', 'utilities', 'url_shortener', 'abc123']
        if len(parts) > 4:  # Has a short_url segment
            return "/utilities/url_shortener/{short_url}"
        elif len(parts) == 4 and parts[3]:  # Has a short_url segment (no trailing slash)
            return "/utilities/url_shortener/{short_url}"
        else:
            # Empty endpoint, just return base path
            return "/utilities/url_shortener"

    # Normalize medium posts paths: /api/medium-posts/{username}
    if path.startswith("/api/medium-posts/"):
        return "/api/medium-posts/{username}"

    # Normalize horoscope paths if they have dynamic segments
    if path.startswith("/utilities/horoscope/"):
        zodiac_sign = path.removeprefix("/utilities/horoscope/")
        if zodiac_sign:
            return "/utilities/horoscope/{id}"
        return "/utilities/horoscope"

    # For other paths, check if they look like UUIDs or IDs
    # Replace UUIDs (8-4-4-4-12 hex format) with {id}
    uuid_pattern = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
    path = re.sub(uuid_pattern, "{id}", path, flags=re.IGNORECASE)

    # Replace numeric IDs at the end of paths (common pattern)
    # e.g., /api/users/123 -> /api/users/{id}
    path = re.sub(r"/\d+$", "/{id}", path)

    # Replace alphanumeric strings that look like IDs (6+ chars) in path segments
    # This catches short URLs and similar identifiers
    path = re.sub(r"/[a-zA-Z0-9]{6,}", "/{id}", path)

    return path


class PrometheusMiddleware:
    async def __call__(self, request: Request, call_next):
        start_time = time.time()

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Skip tracking for healthcheck endpoint
            if not request.url.path.startswith("/metrics"):
                normalized_endpoint = normalize_endpoint(request.url.path)
                track_metrics(
                    method=request.method,
                    endpoint=normalized_endpoint,
                    status_code=response.status_code,
                    duration=duration,
                )

            return response

        except Exception as e:
            duration = time.time() - start_time
            # Track failed requests
            normalized_endpoint = normalize_endpoint(request.url.path)
            track_metrics(
                method=request.method,
                endpoint=normalized_endpoint,
                status_code=500,
                duration=duration,
            )
            raise e
