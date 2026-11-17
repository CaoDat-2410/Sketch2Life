# Host test environment note

The first host collection attempt used Python 3.14, while `backend/pyproject.toml` requires Python `>=3.12,<3.14`. The host also lacked Pillow and SQLAlchemy, causing 15 collection errors before tests ran. This was treated as a runner/environment failure; the full `backend/tests/contract` suite was then run in a disposable container using the existing Python 3.12 API image.
