from contextlib import asynccontextmanager
import uvicorn
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference
from api.v1 import v1_router
from core.logger import get_logger
from core.config import app_config


OPENAPI_URL = "/openapi.json"
APP_NAME = "EduAgent API"

logger = get_logger(__name__)

az_logger = logging.getLogger("azure")
az_logger.setLevel(logging.ERROR)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for FastAPI."""
    try:
        logger.info(f"Starting {APP_NAME} API...")

        # Azure Search infrastructure setup removed - using PostgreSQL vector search instead

        yield
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    finally:
        logger.info(f"Shutting down {APP_NAME} API...")


app = FastAPI(
    title=APP_NAME,
    openapi_url=OPENAPI_URL,
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title=app.title,
        version="1.0.0",
        description="EduAgent API with Azure Entra Authentication",
        routes=app.routes,
    )

    # Add Azure Entra OAuth2 security scheme
    tenant_id = app_config.AZURE_ENTRA_TENANT_ID
    client_id = app_config.AZURE_ENTRA_CLIENT_ID

    openapi_schema["components"]["securitySchemes"] = {
        "AzureEntra": {
            "type": "oauth2",
            "flows": {
                "authorizationCode": {
                    "authorizationUrl": f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize",
                    "tokenUrl": f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
                    "scopes": {
                        f"api://{client_id}/user_impersonation": "Access API as user",
                        "openid": "OpenID Connect",
                        "profile": "User profile",
                        "email": "User email",
                    },
                },
                "implicit": {
                    "authorizationUrl": f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize",
                    "scopes": {
                        "openid": "OpenID Connect",
                        "profile": "User profile",
                        "email": "User email",
                    },
                },
            },
        },
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        },
    }

    # Apply security globally
    openapi_schema["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router=v1_router, prefix="/v1")


@app.get("/health")
async def health_check():
    """Simple health check that doesn't require database"""
    return {"status": "healthy"}


@app.get("/oauth2-redirect", include_in_schema=False)
async def oauth2_redirect():
    """OAuth2 redirect endpoint for Scalar documentation"""
    from starlette.responses import HTMLResponse

    return HTMLResponse(
        """
    <!DOCTYPE html>
    <html>
    <head>
        <title>OAuth2 Redirect</title>
    </head>
    <body>
        <script>
            if (window.opener) {
                window.opener.postMessage({
                    type: 'oauth2',
                    data: window.location.href
                }, '*');
                window.close();
            }
        </script>
    </body>
    </html>
    """
    )


@app.get("/", include_in_schema=False)
async def scalar_docs_ui():
    client_id = app_config.AZURE_ENTRA_CLIENT_ID

    return get_scalar_api_reference(
        openapi_url=OPENAPI_URL,
        title=APP_NAME,
        authentication={
            "preferredSecurityScheme": "BearerAuth",
            "clientId": client_id,
            "oauth2": {
                "clientId": client_id,
                "scopes": [
                    f"api://{client_id}/user_impersonation",
                    "openid",
                    "profile",
                    "email",
                ],
            },
        },
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
