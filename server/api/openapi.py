from core.config import app_config
from fastapi import FastAPI


def custom_openapi(app: FastAPI):
    """Generate custom OpenAPI schema with Supabase authentication."""
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title=app.title,
        version="1.0.0",
        description="EduAgent API",
        routes=app.routes,
    )

    # Add Supabase Bearer JWT security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Supabase JWT token. Get your token from Supabase auth session.",
        },
    }

    # Apply security globally
    openapi_schema["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema
