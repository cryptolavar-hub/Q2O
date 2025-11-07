import argparse, sys, secrets, string, hashlib
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..api.core.db import SessionLocal
from ..api.core.settings import settings
from ..api.models.licensing import Plan, Tenant, Subscription, SubscriptionState, ActivationCode

ALPHABET = string.ascii_uppercase + string.digits

def _hash_code(code: str) -> str:
    return hashlib.sha256((settings.ACTIVATION_CODE_PEPPER + code).encode()).hexdigest()

def _gen_code() -> str:
    parts = [''.join(secrets.choice(ALPHABET) for _ in range(4)) for __ in range(4)]
    return '-'.join(parts)

def seed_plan(args):
    db: Session = SessionLocal()
    try:
        p = Plan(name=args.name, stripe_price_id=args.price_id, monthly_run_quota=args.quota)
        db.add(p); db.commit()
        print(f"Seeded plan {p.name} -> {p.stripe_price_id} quota={p.monthly_run_quota}")
    finally:
        db.close()

def add_tenant(args):
    db: Session = SessionLocal()
    try:
        t = Tenant(name=args.name, slug=args.slug, logo_url=args.logo_url, primary_color=args.color, domain=args.domain)
        db.add(t); db.commit()
        print(f"Created tenant {t.slug}")
    finally:
        db.close()

def link_sub(args):
    db: Session = SessionLocal()
    try:
        t = db.query(Tenant).filter_by(slug=args.tenant).first()
        if not t: print("Tenant not found", file=sys.stderr); sys.exit(2)
        sub = db.query(Subscription).filter_by(tenant_id=t.id).first()
        if not sub:
            plan = db.query(Plan).filter_by(name=args.plan).first()
            if not plan: print("Plan required (--plan)", file=sys.stderr); sys.exit(2)
            sub = Subscription(tenant_id=t.id, plan_id=plan.id)
            db.add(sub)
        sub.stripe_customer_id = args.customer
        sub.stripe_subscription_id = args.sub
        sub.state = SubscriptionState(args.state)
        db.commit()
        print(f"Linked subscription for {t.slug} -> {sub.stripe_subscription_id} [{sub.state}]")
    finally:
        db.close()

def gen_codes(args):
    db: Session = SessionLocal()
    try:
        t = db.query(Tenant).filter_by(slug=args.tenant).first()
        if not t: print("Tenant not found", file=sys.stderr); sys.exit(2)
        expires_at = datetime.utcnow() + timedelta(days=args.ttl_days) if args.ttl_days else None
        for _ in range(args.count):
            code = _gen_code()
            ac = ActivationCode(tenant_id=t.id, code_hash=_hash_code(code), label=args.label, expires_at=expires_at, max_uses=args.max_uses)
            db.add(ac); db.commit()
            print(code)
    finally:
        db.close()

def list_codes(args):
    db: Session = SessionLocal()
    try:
        t = db.query(Tenant).filter_by(slug=args.tenant).first()
        if not t: print("Tenant not found", file=sys.stderr); sys.exit(2)
        q = db.query(ActivationCode).filter_by(tenant_id=t.id)
        rows = q.order_by(ActivationCode.created_at.desc()).all()
        for r in rows:
            status = "revoked" if r.revoked_at else ("used" if r.use_count >= r.max_uses or r.used_at else "unused")
            exp = r.expires_at.isoformat() if r.expires_at else "none"
            print(f"id={r.id} label={r.label or '-'} status={status} uses={r.use_count}/{r.max_uses} exp={exp}")
    finally:
        db.close()

def revoke_code(args):
    db: Session = SessionLocal()
    try:
        t = db.query(Tenant).filter_by(slug=args.tenant).first()
        if not t: print("Tenant not found", file=sys.stderr); sys.exit(2)
        h = _hash_code(args.code)
        ac = db.query(ActivationCode).filter_by(tenant_id=t.id, code_hash=h).first()
        if not ac: print("Code not found", file=sys.stderr); sys.exit(2)
        ac.revoked_at = datetime.utcnow(); db.commit()
        print("revoked")
    finally:
        db.close()

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    sp = sub.add_parser("seed-plan"); sp.add_argument("--name", required=True); sp.add_argument("--price-id", required=True); sp.add_argument("--quota", type=int, required=True); sp.set_defaults(func=seed_plan)
    st = sub.add_parser("add-tenant"); st.add_argument("--name", required=True); st.add_argument("--slug", required=True); st.add_argument("--logo-url"); st.add_argument("--color"); st.add_argument("--domain"); st.set_defaults(func=add_tenant)
    sl = sub.add_parser("link-sub"); sl.add_argument("--tenant", required=True); sl.add_argument("--customer", required=True); sl.add_argument("--sub", required=True); sl.add_argument("--state", default="active"); sl.add_argument("--plan", required=True); sl.set_defaults(func=link_sub)
    sg = sub.add_parser("gen-codes"); sg.add_argument("--tenant", required=True); sg.add_argument("--count", type=int, default=1); sg.add_argument("--ttl-days", type=int); sg.add_argument("--label"); sg.add_argument("--max-uses", type=int, default=1); sg.set_defaults(func=gen_codes)
    slc = sub.add_parser("list-codes"); slc.add_argument("--tenant", required=True); slc.set_defaults(func=list_codes)
    srv = sub.add_parser("revoke-code"); srv.add_argument("--tenant", required=True); srv.add_argument("--code", required=True); srv.set_defaults(func=revoke_code)

    args = p.parse_args()
    if not hasattr(args, "func"):
        p.print_help(); sys.exit(1)
    args.func(args)

if __name__ == "__main__":
    main()
