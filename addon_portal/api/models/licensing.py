import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum, BigInteger, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from ..core.db import Base

class SubscriptionState(str, enum.Enum):
    active = "active"
    past_due = "past_due"
    canceled = "canceled"
    unpaid = "unpaid"
    trialing = "trialing"
    suspended = "suspended"

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    logo_url = Column(String, nullable=True)
    primary_color = Column(String, nullable=True)
    domain = Column(String, nullable=True)
    usage_quota = Column(Integer, default=10, nullable=False)  # For usage-based billing
    usage_current = Column(Integer, default=0, nullable=False)  # Current usage count
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    subscription = relationship("Subscription", back_populates="tenant", uselist=False, overlaps="subscriptions")
    subscriptions = relationship("Subscription", back_populates="tenant", overlaps="subscription")  # For admin API

class Plan(Base):
    __tablename__ = "plans"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    stripe_price_id = Column(String, unique=True, nullable=False)
    monthly_run_quota = Column(Integer, nullable=False, default=100)

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    state = Column(Enum(SubscriptionState), default=SubscriptionState.trialing, nullable=False)
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    tenant = relationship("Tenant", back_populates="subscription")
    plan = relationship("Plan")

class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    label = Column(String, nullable=True)
    hw_fingerprint = Column(String, nullable=False)
    refresh_token_hash = Column(String, nullable=True)
    last_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    __table_args__ = (UniqueConstraint("tenant_id", "hw_fingerprint", name="uq_device_per_tenant_fpr"),)

class UsageEvent(Base):
    __tablename__ = "usage_events"
    id = Column(BigInteger, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    kind = Column(String, nullable=False)
    at = Column(DateTime, default=datetime.utcnow, nullable=False)
    event_metadata = Column(String, nullable=True)

class MonthlyUsageRollup(Base):
    __tablename__ = "monthly_usage_rollups"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    runs = Column(Integer, default=0, nullable=False)
    __table_args__ = (UniqueConstraint("tenant_id", "year", "month", name="uq_tenant_month"),)

class ActivationCode(Base):
    __tablename__ = "activation_codes"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    code_plain = Column(String, nullable=False)  # Plain text code for admin display
    code_hash = Column(String, nullable=False)  # Hashed for verification
    label = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    used_at = Column(DateTime, nullable=True)
    max_uses = Column(Integer, nullable=False, default=1)
    use_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    tenant = relationship("Tenant", backref="activation_codes")
    __table_args__ = (Index("ix_activation_codes_tenant", "tenant_id"),)
