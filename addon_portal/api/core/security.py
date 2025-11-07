import time, jwt
from .settings import settings

ALGO = "RS256"

def issue_access_token(tenant_id: int, device_id: int, plan: str, quota: int, subs_state: str) -> str:
    now = int(time.time())
    payload = {
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "iat": now,
        "exp": now + settings.JWT_ACCESS_TTL_SECONDS,
        "sub": f"tenant:{tenant_id}:device:{device_id}",
        "entitlements": {
            "plan": plan,
            "monthly_run_quota": quota,
            "subscription_state": subs_state,
        },
    }
    return jwt.encode(payload, settings.JWT_PRIVATE_KEY, algorithm=ALGO)

def verify_access(token: str) -> dict:
    return jwt.decode(token, settings.JWT_PUBLIC_KEY, audience=settings.JWT_AUDIENCE, algorithms=[ALGO])
