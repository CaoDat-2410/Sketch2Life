"""HTTP cache and optimistic-concurrency metadata for authenticated Admin resources."""

import json

from fastapi.routing import APIRoute


class AdminRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def handle(request):
            response = await handler(request)
            response.headers["Cache-Control"] = "no-store"
            response.headers["Vary"] = "Authorization"
            if 200 <= response.status_code < 300 and hasattr(response, "body"):
                try:
                    body = json.loads(response.body)
                    revision = body.get("revision") if isinstance(body, dict) else None
                    if isinstance(revision, int) and revision > 0:
                        response.headers["ETag"] = f'"{revision}"'
                except (ValueError, TypeError):
                    pass
            return response

        return handle
