from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from starlette.templating import Jinja2Templates
from starlette.status import HTTP_303_SEE_OTHER
from typing import Optional
from ..deps import get_db
from ..models.licensing import Tenant, ActivationCode, Device
from ..core.settings import settings
from ..deps_admin import require_admin
from .authz import _hash_code
from datetime import datetime, timedelta
import secrets, string

router = APIRouter(prefix="/admin", tags=["admin"], include_in_schema=False)
_templates = Jinja2Templates(directory="api/templates")

ALPHABET = string.ascii_uppercase + string.digits

@router.get("/codes", response_class=HTMLResponse)
async def codes_page(request: Request, tenant: str = "", user = Depends(require_admin), db: Session = Depends(get_db)):
    tenants = db.query(Tenant).order_by(Tenant.slug.asc()).all()
    selected = None; codes = []
    if tenant:
        selected = db.query(Tenant).filter_by(slug=tenant).first()
        if selected:
            codes = db.query(ActivationCode).filter_by(tenant_id=selected.id).order_by(ActivationCode.created_at.desc()).all()
    return _templates.TemplateResponse("admin/codes.html", {"request": request, "tenants": tenants, "selected": selected, "codes": codes})

@router.post("/codes/generate")
async def gen_codes_action(request: Request, user = Depends(require_admin),
    tenant_slug: str = Form(...), count: int = Form(1), ttl_days: Optional[int] = Form(None), label: Optional[str] = Form(None), max_uses: int = Form(1),
    db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter_by(slug=tenant_slug).first()
    if not tenant: raise HTTPException(404, "tenant not found")
    expires_at = datetime.utcnow() + timedelta(days=ttl_days) if ttl_days else None
    def _gen():
        return "-".join("".join(secrets.choice(ALPHABET) for _ in range(4)) for __ in range(4))
    printed = []
    for _ in range(count):
        code = _gen()
        ac = ActivationCode(tenant_id=tenant.id, code_hash=_hash_code(code), label=label, expires_at=expires_at, max_uses=max_uses)
        db.add(ac); db.commit(); printed.append(code)
    url = request.url_for("codes_page") + f"?tenant={tenant_slug}&created={'%2C'.join(printed)}"
    return RedirectResponse(url, status_code=HTTP_303_SEE_OTHER)

@router.post("/codes/revoke")
async def revoke_code_action(request: Request, user = Depends(require_admin), tenant_slug: str = Form(...), code_plain: str = Form(...), db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter_by(slug=tenant_slug).first()
    if not tenant: raise HTTPException(404, "tenant not found")
    h = _hash_code(code_plain)
    ac = db.query(ActivationCode).filter_by(tenant_id=tenant.id, code_hash=h).first()
    if not ac: raise HTTPException(404, "code not found")
    ac.revoked_at = datetime.utcnow(); db.commit()
    url = request.url_for("codes_page") + f"?tenant={tenant_slug}"
    return RedirectResponse(url, status_code=HTTP_303_SEE_OTHER)

@router.get("/devices", response_class=HTMLResponse)
async def devices_page(request: Request, tenant: str = "", user = Depends(require_admin), db: Session = Depends(get_db)):
    tenants = db.query(Tenant).order_by(Tenant.slug.asc()).all()
    selected = None; devices = []
    if tenant:
        selected = db.query(Tenant).filter_by(slug=tenant).first()
        if selected:
            devices = db.query(Device).filter_by(tenant_id=selected.id).order_by(Device.last_seen.desc()).all()
    return _templates.TemplateResponse("admin/devices.html", {"request": request, "tenants": tenants, "selected": selected, "devices": devices})

@router.post("/devices/revoke")
async def revoke_device_action(request: Request, user = Depends(require_admin), tenant_slug: str = Form(...), device_id: int = Form(...), db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter_by(slug=tenant_slug).first()
    if not tenant: raise HTTPException(404, "tenant not found")
    dev = db.query(Device).filter_by(id=device_id, tenant_id=tenant.id).first()
    if not dev: raise HTTPException(404, "device not found")
    dev.is_revoked = True; db.commit()
    url = request.url_for("devices_page") + f"?tenant={tenant_slug}"
    return RedirectResponse(url, status_code=HTTP_303_SEE_OTHER)
