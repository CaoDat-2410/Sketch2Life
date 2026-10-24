"""ASGI entrypoint for local and in-memory demo capabilities only."""

from sketch2life.interfaces.http.app import create_demo_app

app = create_demo_app()
