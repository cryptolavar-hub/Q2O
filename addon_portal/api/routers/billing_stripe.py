import stripe
from fastapi import APIRouter, Request, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional
from ..core.settings import settings
from ..core.db import AsyncSessionLocal
from ..models.licensing import Subscription, SubscriptionState, Plan, Tenant, ActivationCode
from ..routers.tenant_api import get_tenant_from_session
from ..core.logging import get_logger
from datetime import datetime, timezone

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

router = APIRouter(prefix="/billing/stripe", tags=["billing"])
LOGGER = get_logger(__name__)

@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.STRIPE_WEBHOOK_SECRET)
    except ValueError as e:
        LOGGER.error("stripe_webhook_invalid_payload", extra={"error": str(e)})
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")
    except stripe.error.SignatureVerificationError as e:
        LOGGER.error("stripe_webhook_invalid_signature", extra={"error": str(e)})
        raise HTTPException(status_code=400, detail=f"Invalid signature: {e}")

    async with AsyncSessionLocal() as db:
        try:
            event_type = event["type"]
            obj = event["data"]["object"]
            
            LOGGER.info("stripe_webhook_received", extra={"event_type": event_type})
            
            # Handle subscription events
            if event_type in ("customer.subscription.created", "customer.subscription.updated"):
                stripe_sub_id = obj["id"]
                price_id = obj["items"]["data"][0]["price"]["id"]
                sub_status = obj["status"]

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
                        LOGGER.warning("stripe_webhook_subscription_not_found", extra={"stripe_sub_id": stripe_sub_id})
                        return {"ignored": True}

                result = await db.execute(select(Plan).where(Plan.stripe_price_id == price_id))
                plan = result.scalar_one_or_none()
                if plan:
                    sub.plan_id = plan.id
                
                # Map Stripe status to our SubscriptionState enum
                state = sub_status if sub_status in SubscriptionState.__members__ else "active"
                sub.state = SubscriptionState[state]
                sub.current_period_start = datetime.fromtimestamp(obj["current_period_start"], tz=timezone.utc)
                sub.current_period_end = datetime.fromtimestamp(obj["current_period_end"], tz=timezone.utc)
                await db.commit()
                
            # Handle checkout session completion (for one-time purchases like activation codes)
            elif event_type == "checkout.session.completed":
                session_id = obj["id"]
                customer_id = obj.get("customer")
                metadata = obj.get("metadata", {})
                
                # Check if this is an activation code purchase
                if metadata.get("type") == "activation_codes":
                    tenant_id = int(metadata.get("tenant_id"))
                    quantity = int(metadata.get("quantity", 1))
                    
                    # Generate activation codes
                    from ..services.activation_code_service import generate_codes
                    await generate_codes(
                        session=db,
                        tenant_id=tenant_id,
                        count=quantity,
                        label=metadata.get("label", f"Purchased {quantity} codes via Stripe"),
                        max_uses=1,
                    )
                    await db.commit()
                    LOGGER.info("activation_codes_generated_via_stripe", extra={"tenant_id": tenant_id, "quantity": quantity})
                
                # Check if this is a subscription upgrade
                elif metadata.get("type") == "subscription_upgrade":
                    tenant_id = int(metadata.get("tenant_id"))
                    plan_id = int(metadata.get("plan_id"))
                    
                    result = await db.execute(
                        select(Subscription)
                        .where(Subscription.tenant_id == tenant_id)
                        .order_by(Subscription.id.desc())
                        .limit(1)
                    )
                    sub = result.scalar_one_or_none()
                    if sub:
                        result = await db.execute(select(Plan).where(Plan.id == plan_id))
                        plan = result.scalar_one_or_none()
                        if plan:
                            sub.plan_id = plan.id
                            await db.commit()
                            LOGGER.info("subscription_upgraded_via_stripe", extra={"tenant_id": tenant_id, "plan_id": plan_id})
            
            # Handle invoice payment succeeded
            elif event_type == "invoice.payment_succeeded":
                subscription_id = obj.get("subscription")
                if subscription_id:
                    result = await db.execute(
                        select(Subscription).where(Subscription.stripe_subscription_id == subscription_id)
                    )
                    sub = result.scalar_one_or_none()
                    if sub:
                        # Update subscription status to active
                        sub.state = SubscriptionState.active
                        await db.commit()
                        LOGGER.info("invoice_payment_succeeded", extra={"subscription_id": subscription_id})
            
            # Handle invoice payment failed
            elif event_type == "invoice.payment_failed":
                subscription_id = obj.get("subscription")
                if subscription_id:
                    result = await db.execute(
                        select(Subscription).where(Subscription.stripe_subscription_id == subscription_id)
                    )
                    sub = result.scalar_one_or_none()
                    if sub:
                        # Update subscription status to past_due
                        sub.state = SubscriptionState.past_due
                        await db.commit()
                        LOGGER.warning("invoice_payment_failed", extra={"subscription_id": subscription_id})
            
            return {"ok": True}
        except Exception as e:
            await db.rollback()
            LOGGER.error("stripe_webhook_error", extra={"error": str(e), "event_type": event_type})
            raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")
