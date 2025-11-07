from pydantic import BaseModel
from typing import Optional

class ActivationRequest(BaseModel):
    tenant_slug: str
    activation_code: str
    hw_fingerprint: str

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int

class Policy(BaseModel):
    plan_name: str
    monthly_run_quota: int
    subscription_state: str

class Branding(BaseModel):
    logo_url: Optional[str]
    primary_color: Optional[str]
    domain: Optional[str]

class HeartbeatRequest(BaseModel):
    hw_fingerprint: str
