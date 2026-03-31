# This helper starts the API locally using the repository's default .env file.
# Use the API keys from .env in the X-API-Key header when calling protected endpoints.
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
