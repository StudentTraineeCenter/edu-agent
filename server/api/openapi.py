from core.config import app_config
from fastapi import FastAPI


def custom_openapi(app: FastAPI):
    """Generate custom OpenAPI schema with Azure Entra authentication."""
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
