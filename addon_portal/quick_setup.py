#!/usr/bin/env python3
"""
Quick Setup Script for Q2O Licensing System
Creates database tables and seeds with demo data
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from api.core.db import Base, engine
from api.core.settings import settings
from api.models.licensing import (
    Tenant, Plan, Subscription, ActivationCode,
    Device, UsageEvent, MonthlyUsageRollup, SubscriptionState
)
from sqlalchemy.orm import Session
import hashlib
import secrets

def generate_activation_code():
    """Generate a human-readable activation code (e.g., 12RY-S55W-4MZR-KP2J)"""
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # No ambiguous chars
    parts = []
    for _ in range(4):
        part = ''.join(secrets.choice(chars) for _ in range(4))
        parts.append(part)
    return '-'.join(parts)

def hash_code(code):
    """Hash an activation code for storage"""
    return hashlib.sha256(code.encode()).hexdigest()

def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("[OK] Tables created successfully")

def seed_demo_data():
    """Seed database with demo data"""
    print("\nSeeding demo data...")
    
    with Session(engine) as session:
        # Check if demo data already exists
        existing_tenant = session.query(Tenant).filter_by(slug="demo").first()
        if existing_tenant:
            print("[WARNING] Demo data already exists. Skipping seed.")
            return
        
        # Create subscription plans
        print("Creating subscription plans...")
        plans = [
            Plan(
                name="Starter",
                stripe_price_id="price_starter_monthly",
                monthly_run_quota=10
            ),
            Plan(
                name="Pro",
                stripe_price_id="price_pro_monthly",
                monthly_run_quota=50
            ),
            Plan(
                name="Enterprise",
                stripe_price_id="price_enterprise_monthly",
                monthly_run_quota=200
            )
        ]
        for plan in plans:
            session.add(plan)
        session.commit()
        print(f"[OK] Created {len(plans)} subscription plans")
        
        # Create demo tenant
        print("Creating demo tenant...")
        demo_tenant = Tenant(
            name="Demo Consulting Firm",
            slug="demo",
            logo_url="https://via.placeholder.com/150?text=Demo",
            primary_color="#875A7B",  # Odoo purple
            domain="demo.quick2odoo.com"
        )
        session.add(demo_tenant)
        session.commit()
        print(f"[OK] Created demo tenant: {demo_tenant.slug}")
        
        # Create active subscription (Pro plan)
        print("Creating active subscription...")
        pro_plan = session.query(Plan).filter_by(name="Pro").first()
        subscription = Subscription(
            tenant_id=demo_tenant.id,
            plan_id=pro_plan.id,
            state=SubscriptionState.active,
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30),
            stripe_customer_id="cus_demo_customer",
            stripe_subscription_id="sub_demo_subscription"
        )
        session.add(subscription)
        session.commit()
        print(f"[OK] Created active subscription (Pro - {pro_plan.monthly_run_quota} migrations/month)")
        
        # Create activation codes
        print("Creating activation codes...")
        codes = []
        for i in range(3):
            code = generate_activation_code()
            codes.append(code)
            activation_code = ActivationCode(
                tenant_id=demo_tenant.id,
                code_hash=hash_code(code),
                label=f"Demo Code {i+1}",
                expires_at=datetime.utcnow() + timedelta(days=30),
                max_uses=1,
                use_count=0
            )
            session.add(activation_code)
        session.commit()
        print(f"[OK] Created {len(codes)} activation codes:")
        for code in codes:
            print(f"   {code}")
        
        # Create monthly usage rollup
        print("Creating usage rollup...")
        now = datetime.utcnow()
        usage_rollup = MonthlyUsageRollup(
            tenant_id=demo_tenant.id,
            year=now.year,
            month=now.month,
            runs=0
        )
        session.add(usage_rollup)
        session.commit()
        print(f"[OK] Created usage rollup for {now.year}-{now.month:02d}")
        
        print("\n" + "="*70)
        print("[SUCCESS] Demo data seeded successfully!")
        print("="*70)
        print(f"\nDEMO CREDENTIALS:")
        print(f"   Tenant Slug:  demo")
        print(f"   Tenant Name:  Demo Consulting Firm")
        print(f"   Plan:         Pro (50 migrations/month)")
        print(f"   Status:       Active")
        print(f"\nACTIVATION CODES:")
        for code in codes:
            print(f"   {code}")
        print(f"\nDATABASE LOCATION:")
        print(f"   {settings.DB_DSN}")
        print(f"\nTO START THE LICENSING API:")
        print(f"   cd {Path(__file__).parent}")
        print(f"   python -m uvicorn api.main:app --port 8080")
        print(f"\nAPI DOCUMENTATION:")
        print(f"   http://localhost:8080/docs")
        print("="*70)

def main():
    """Main setup function"""
    print("="*70)
    print("  Q2O Licensing System - Quick Setup")
    print("="*70)
    print(f"\nDatabase: {settings.DB_DSN}\n")
    
    try:
        # Create tables
        create_tables()
        
        # Seed demo data
        seed_demo_data()
        
        print("\n[SUCCESS] Setup complete! Ready to start services.\n")
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

