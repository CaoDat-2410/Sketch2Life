"""ASGI entrypoint for the durable classroom runtime only."""

from sketch2life.interfaces.http.app import create_classroom_app

app = create_classroom_app()
