import stripe
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.orm import Session
from ..core.settings import settings
from ..core.db import SessionLocal
from ..models.licensing import Subscription, SubscriptionState, Plan
from datetime import datetime

router = APIRouter(prefix="/billing/stripe", tags=["billing"])

@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(400, f"Bad signature: {e}")

    db = SessionLocal()
    try:
        if event["type"] in ("customer.subscription.created","customer.subscription.updated"):
            obj = event["data"]["object"]
            stripe_sub_id = obj["id"]
            price_id = obj["items"]["data"][0]["price"]["id"]
            status = obj["status"]

            sub = db.query(Subscription).filter_by(stripe_subscription_id=stripe_sub_id).first()
            if not sub:
                sub = db.query(Subscription).filter_by(stripe_customer_id=obj["customer"]).first()
                if not sub: return {"ignored": True}

            plan = db.query(Plan).filter_by(stripe_price_id=price_id).first()
            if plan: sub.plan_id = plan.id
            # clamp status
            state = status if status in SubscriptionState.__members__ else "active"
            sub.state = SubscriptionState[state]
            sub.current_period_start = datetime.utcfromtimestamp(obj["current_period_start"])
            sub.current_period_end = datetime.utcfromtimestamp(obj["current_period_end"])
            db.commit()
        return {"ok": True}
    finally:
        db.close()
