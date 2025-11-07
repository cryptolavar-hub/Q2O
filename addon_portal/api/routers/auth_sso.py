from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from ..core.settings import settings

router = APIRouter(prefix="/auth", tags=["auth"], include_in_schema=False)

_config = Config(environ={
    "OIDC_CLIENT_ID": settings.OIDC_CLIENT_ID or "",
    "OIDC_CLIENT_SECRET": settings.OIDC_CLIENT_SECRET or "",
    "OIDC_SERVER_METADATA_URL": f"{settings.OIDC_ISSUER}/.well-known/openid-configuration" if settings.OIDC_ISSUER else "",
})
oauth = OAuth(_config)
oauth.register(
    name="oidc",
    server_metadata_url=_config.get("OIDC_SERVER_METADATA_URL"),
    client_id=_config.get("OIDC_CLIENT_ID"),
    client_secret=_config.get("OIDC_CLIENT_SECRET"),
    client_kwargs={"scope": "openid email profile"},
)

@router.get("/login")
async def login(request: Request):
    if not settings.OIDC_ISSUER:
        raise HTTPException(503, "OIDC not configured")
    redirect_uri = settings.OIDC_REDIRECT_URL
    return await oauth.oidc.authorize_redirect(request, redirect_uri)

@router.get("/callback")
async def callback(request: Request):
    token = await oauth.oidc.authorize_access_token(request)
    userinfo = token.get("userinfo") or await oauth.oidc.parse_id_token(request, token)
    request.session["user"] = {
        "sub": userinfo.get("sub"),
        "email": userinfo.get("email"),
        "name": userinfo.get("name") or userinfo.get("preferred_username"),
    }
    return RedirectResponse("/admin/codes")

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/")
