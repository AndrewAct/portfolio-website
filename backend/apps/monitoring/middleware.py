from fastapi import Request
from .prometheus import track_metrics
import time


class PrometheusMiddleware:
    async def __call__(self, request: Request, call_next):
        start_time = time.time()

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Skip tracking for healthcheck endpoint
            if not request.url.path.startswith("/metrics"):
                track_metrics(
                    method=request.method,
                    endpoint=request.url.path,
                    status_code=response.status_code,
                    duration=duration
                )

            return response

        except Exception as e:
            duration = time.time() - start_time
            # Track failed requests
            track_metrics(
                method=request.method,
                endpoint=request.url.path,
                status_code=500,
                duration=duration
            )
            raise e