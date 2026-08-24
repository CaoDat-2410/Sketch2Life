"""ASGI entrypoint for the Sketch2Life backend foundation."""

from sketch2life.interfaces.http.app import create_app

app = create_app()
