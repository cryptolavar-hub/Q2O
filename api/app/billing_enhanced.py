"""
Enhanced Billing System with Data-Volume-Based Pricing
Integrates with Stripe and migration pricing engine
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Optional, List
import stripe
import logging
import os

from utils.migration_pricing import (
    MigrationPricingEngine,
    calculate_migration_cost,
    quick_estimate
)

logger = logging.getLogger(__name__)

# Stripe configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
BILLING_SUCCESS_URL = os.getenv("BILLING_SUCCESS_URL", "https://app.quick2odoo.com/billing/success")
BILLING_CANCEL_URL = os.getenv("BILLING_CANCEL_URL", "https://app.quick2odoo.com/billing/cancel")


# Request/Response Models
class PricingEstimateRequest(BaseModel):
    """Request for pricing estimate."""
    platform_name: str
    years_of_data: int
    estimated_records: Optional[int] = None
    tax_rate: Optional[float] = 0.0


class DataVolumeAnalysisRequest(BaseModel):
    """Request for detailed data volume analysis."""
    platform_name: str
    platform_credentials: Dict[str, str]
    years_of_data: int
    tax_rate: Optional[float] = 0.0


class CheckoutRequest(BaseModel):
    """Request to create Stripe checkout session."""
    migration_id: str
    customer_email: str
    pricing_data: Dict
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class EnhancedBillingManager:
    """Enhanced billing manager with data-volume-based pricing."""
    
    def __init__(self):
        self.pricing_engine = MigrationPricingEngine(tax_rate=0.0)  # Default, override per request
    
    def get_pricing_tiers(self) -> List[Dict]:
        """Get pricing tiers information."""
        return self.pricing_engine.get_pricing_tiers_info()
    
    def estimate_cost_quick(self, platform_name: str, years: int, 
                           estimated_records: int = None, tax_rate: float = 0.0) -> Dict:
        """
        Quick cost estimation without platform connection.
        
        Args:
            platform_name: Platform name
            years: Years of data
            estimated_records: Estimated record count
            tax_rate: Tax rate
            
        Returns:
            Pricing estimate
        """
        # Use typical record counts if not provided
        if not estimated_records:
            estimated_records = self._estimate_typical_records(platform_name, years)
        
        self.pricing_engine.tax_rate = tax_rate
        pricing = quick_estimate(platform_name, years, estimated_records, tax_rate)
        
        return pricing.to_dict()
    
    def analyze_and_price(self, source_client: Any, platform_name: str, 
                         years: int, tax_rate: float = 0.0) -> Dict:
        """
        Analyze actual data volume and calculate accurate pricing.
        
        Args:
            source_client: Connected source platform client
            platform_name: Platform name
            years: Years of data to migrate
            tax_rate: Tax rate
            
        Returns:
            Complete analysis and pricing
        """
        self.pricing_engine.tax_rate = tax_rate
        
        # Analyze data volume
        data_volume = self.pricing_engine.analyze_data_volume(
            source_client, years, platform_name
        )
        
        # Calculate pricing
        pricing = self.pricing_engine.calculate_pricing(data_volume)
        
        return {
            "data_volume": {
                "years_of_data": data_volume.years_of_data,
                "total_records": data_volume.total_records,
                "entity_breakdown": data_volume.entity_breakdown,
                "estimated_size_mb": data_volume.estimated_size_mb,
                "complexity_score": data_volume.complexity_score,
                "complexity_level": data_volume.get_complexity_level(),
                "platform_name": data_volume.platform_name
            },
            "pricing": pricing.to_dict()
        }
    
    def _estimate_typical_records(self, platform_name: str, years: int) -> int:
        """Estimate typical record count for platform and years."""
        # Average records per year by business size
        annual_averages = {
            "small": 1000,      # 1K records/year
            "medium": 10000,    # 10K records/year
            "large": 50000      # 50K records/year
        }
        
        # Assume medium business as default
        annual_avg = annual_averages["medium"]
        
        return annual_avg * years
    
    def create_checkout_session(self, migration_id: str, customer_email: str, 
                               pricing_data: Dict, metadata: Dict = None) -> Dict:
        """
        Create Stripe checkout session for migration payment.
        
        Args:
            migration_id: Unique migration ID
            customer_email: Customer email
            pricing_data: Pricing information from calculate_pricing()
            metadata: Additional metadata
            
        Returns:
            Checkout session data with URL
        """
        try:
            # Create line item
            line_items = [{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": int(pricing_data["total"] * 100),  # Convert to cents
                    "product_data": {
                        "name": f"Odoo Migration - {migration_id}",
                        "description": (
                            f"{pricing_data['tier'].title()} Tier: "
                            f"{pricing_data['pricing_details']['years_of_data']} years, "
                            f"{pricing_data['pricing_details']['total_records']:,} records from "
                            f"{pricing_data['pricing_details']['platform']}"
                        ),
                        "metadata": pricing_data["pricing_details"]
                    }
                },
                "quantity": 1
            }]
            
            # Merge metadata
            session_metadata = {
                "migration_id": migration_id,
                "tier": pricing_data["tier"],
                "years": pricing_data["pricing_details"]["years_of_data"],
                "records": pricing_data["pricing_details"]["total_records"],
                "platform": pricing_data["pricing_details"]["platform"]
            }
            
            if metadata:
                session_metadata.update(metadata)
            
            # Create Stripe checkout session
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=line_items,
                mode="payment",  # One-time payment
                success_url=BILLING_SUCCESS_URL + f"?session_id={{CHECKOUT_SESSION_ID}}&migration_id={migration_id}",
                cancel_url=BILLING_CANCEL_URL + f"?migration_id={migration_id}",
                customer_email=customer_email,
                metadata=session_metadata,
                allow_promotion_codes=True,
                billing_address_collection="required"
            )
            
            logger.info(f"Created checkout session {session.id} for migration {migration_id}")
            
            return {
                "session_id": session.id,
                "url": session.url,
                "amount": pricing_data["total"],
                "currency": "usd"
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment system error: {str(e)}"
            )
    
    def verify_payment_status(self, session_id: str) -> Dict:
        """
        Verify payment status for a checkout session.
        
        Args:
            session_id: Stripe session ID
            
        Returns:
            Payment status
        """
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            
            return {
                "migration_id": session.metadata.get("migration_id"),
                "payment_status": session.payment_status,
                "status": session.status,
                "amount_total": session.amount_total / 100,
                "customer_email": session.customer_email,
                "tier": session.metadata.get("tier"),
                "paid": session.payment_status == "paid"
            }
        except stripe.error.StripeError as e:
            logger.error(f"Error verifying payment: {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment session not found"
            )
    
    def handle_webhook(self, payload: bytes, sig_header: str) -> Dict:
        """Handle Stripe webhook events."""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook"
            )
        
        event_type = event["type"]
        
        if event_type == "checkout.session.completed":
            session = event["data"]["object"]
            migration_id = session.get("metadata", {}).get("migration_id")
            
            logger.info(f"Payment completed for migration {migration_id}")
            
            # TODO: Update migration status to "paid" in database
            # TODO: Trigger migration start
            
            return {
                "status": "success",
                "migration_id": migration_id,
                "action": "payment_received"
            }
        
        elif event_type == "payment_intent.payment_failed":
            payment_intent = event["data"]["object"]
            logger.warning(f"Payment failed: {payment_intent.get('id')}")
            
            return {
                "status": "failed",
                "action": "payment_failed"
            }
        
        return {"status": "ignored", "event_type": event_type}


# FastAPI Router
def create_enhanced_billing_router() -> APIRouter:
    """Create FastAPI router for enhanced billing."""
    router = APIRouter(prefix="/api/billing", tags=["billing"])
    billing_manager = EnhancedBillingManager()
    
    @router.get("/pricing-tiers")
    async def get_pricing_tiers():
        """Get available pricing tiers."""
        return billing_manager.get_pricing_tiers()
    
    @router.post("/estimate")
    async def estimate_cost(request: PricingEstimateRequest):
        """
        Get quick cost estimate.
        
        Returns pricing based on platform, years, and estimated records.
        """
        try:
            estimate = billing_manager.estimate_cost_quick(
                platform_name=request.platform_name,
                years=request.years_of_data,
                estimated_records=request.estimated_records,
                tax_rate=request.tax_rate
            )
            
            return estimate
            
        except Exception as e:
            logger.error(f"Error estimating cost: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    @router.post("/analyze-volume")
    async def analyze_data_volume(request: DataVolumeAnalysisRequest):
        """
        Analyze actual data volume from platform.
        
        Connects to source platform and calculates exact pricing.
        """
        try:
            # TODO: Initialize source client with credentials
            # For now, return quick estimate
            estimate = billing_manager.estimate_cost_quick(
                platform_name=request.platform_name,
                years=request.years_of_data,
                tax_rate=request.tax_rate
            )
            
            return {
                "note": "Full analysis requires platform connection",
                "estimate": estimate
            }
            
        except Exception as e:
            logger.error(f"Error analyzing volume: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    @router.post("/checkout")
    async def create_checkout(request: CheckoutRequest):
        """Create Stripe checkout session for migration payment."""
        try:
            session = billing_manager.create_checkout_session(
                migration_id=request.migration_id,
                customer_email=request.customer_email,
                pricing_data=request.pricing_data,
                metadata={
                    "migration_id": request.migration_id
                }
            )
            
            return session
            
        except Exception as e:
            logger.error(f"Error creating checkout: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @router.get("/payment/{session_id}/status")
    async def check_payment_status(session_id: str):
        """Check payment status for a checkout session."""
        try:
            status_data = billing_manager.verify_payment_status(session_id)
            return status_data
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
    
    @router.post("/webhook")
    async def stripe_webhook(
        request: Request,
        stripe_signature: str = Header(..., alias="Stripe-Signature")
    ):
        """Handle Stripe webhooks."""
        payload = await request.body()
        
        try:
            result = billing_manager.handle_webhook(payload, stripe_signature)
            return result
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    return router

