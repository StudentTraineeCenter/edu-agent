"""General API endpoints."""

from core.config import app_config
from fastapi import APIRouter
from scalar_fastapi import get_scalar_api_reference
from starlette.responses import HTMLResponse

router = APIRouter()


@router.get("/health")
async def health_check():
    """Simple health check that doesn't require database"""
    return {"status": "healthy"}


@router.get("/oauth2-redirect", include_in_schema=False)
async def oauth2_redirect():
    """OAuth2 redirect endpoint for Scalar documentation"""
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


@router.get("/", include_in_schema=False)
async def scalar_docs_ui():
    """Scalar API documentation UI with Azure Entra authentication."""
    client_id = app_config.AZURE_ENTRA_CLIENT_ID

    return get_scalar_api_reference(
        openapi_url="/openapi.json",
        title="EduAgent API",
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
