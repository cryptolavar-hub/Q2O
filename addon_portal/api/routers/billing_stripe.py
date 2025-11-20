import stripe
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.settings import settings
from ..core.db import AsyncSessionLocal
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

    async with AsyncSessionLocal() as db:
        try:
            if event["type"] in ("customer.subscription.created","customer.subscription.updated"):
                obj = event["data"]["object"]
                stripe_sub_id = obj["id"]
                price_id = obj["items"]["data"][0]["price"]["id"]
                status = obj["status"]

                result = await db.execute(
                    select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
                )
                sub = result.scalar_one_or_none()
                if not sub:
                    result = await db.execute(
                        select(Subscription).where(Subscription.stripe_customer_id == obj["customer"])
                    )
                    sub = result.scalar_one_or_none()
                    if not sub: 
                        return {"ignored": True}

                result = await db.execute(select(Plan).where(Plan.stripe_price_id == price_id))
                plan = result.scalar_one_or_none()
                if plan: 
                    sub.plan_id = plan.id
                # clamp status
                state = status if status in SubscriptionState.__members__ else "active"
                sub.state = SubscriptionState[state]
                sub.current_period_start = datetime.utcfromtimestamp(obj["current_period_start"])
                sub.current_period_end = datetime.utcfromtimestamp(obj["current_period_end"])
                await db.commit()
            return {"ok": True}
        except Exception as e:
            await db.rollback()
            raise
