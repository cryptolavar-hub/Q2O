#!/usr/bin/env python3
"""Database bootstrap utility for the Q2O Licensing platform.

This script creates all database tables defined by SQLAlchemy models and can
optionally seed baseline/demo data so that the admin portal has meaningful
records to display immediately after installation.

Usage:
    python addon_portal/bootstrap_db.py --seed-demo
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Sequence

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.core.db import Base, engine
from api.core.settings import settings
from api.core.logging import JsonLogFormatter
from api.models.licensing import (
    Plan,
    Subscription,
    SubscriptionState,
    Tenant,
)
from api.services.activation_code_service import generate_codes

# Import all model modules so Base.metadata is aware of every table.
import api.models.events  # noqa: F401
import api.models.llm_config  # noqa: F401
import api.models.research  # noqa: F401


class DatabaseBootstrapError(RuntimeError):
    """Raised when bootstrap operations fail."""


@dataclass(frozen=True)
class PlanSeed:
    """Subscription plan definition used during seeding."""

    name: str
    stripe_price_id: str
    monthly_run_quota: int


def _configure_logger(verbose: bool) -> logging.Logger:
    """Configure JSON logging for this script.

    Args:
        verbose: When True, enable DEBUG level logging.

    Returns:
        A configured :class:`logging.Logger`.
    """

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter())
    level = logging.DEBUG if verbose else logging.INFO
    logger = logging.getLogger("q2o.bootstrap")
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def _redact_dsn(dsn: str) -> str:
    """Redact credentials from the database DSN for safe logging."""

    if "@" not in dsn or "://" not in dsn:
        return dsn
    scheme, remainder = dsn.split("://", 1)
    if "@" not in remainder:
        return f"{scheme}://***"
    _, host_part = remainder.split("@", 1)
    return f"{scheme}://***@{host_part}"


def _create_schema(logger: logging.Logger) -> None:
    """Create all database tables if they do not already exist.

    Args:
        logger: Structured logger instance.

    Raises:
        DatabaseBootstrapError: If SQLAlchemy cannot create the schema.
    """

    logger.info(
        "creating_database_schema",
        extra={"database": _redact_dsn(settings.DB_DSN)},
    )
    try:
        Base.metadata.create_all(bind=engine)
    except SQLAlchemyError as exc:  # pragma: no cover - critical failure
        logger.error("create_schema_failed", extra={"error": str(exc)})
        raise DatabaseBootstrapError("Unable to create database schema") from exc
    logger.info("schema_ready")


def _seed_plans(session: Session, logger: logging.Logger) -> None:
    """Insert baseline subscription plans when none exist.

    Args:
        session: Active SQLAlchemy session.
        logger: Logger used for structured messages.

    Raises:
        DatabaseBootstrapError: If the insert fails.
    """

    existing_count = session.query(Plan).count()
    if existing_count > 0:
        logger.info("plans_exist", extra={"count": existing_count})
        return

    seeds: Sequence[PlanSeed] = (
        PlanSeed("Starter", "price_starter_monthly", 10),
        PlanSeed("Pro", "price_pro_monthly", 50),
        PlanSeed("Enterprise", "price_enterprise_monthly", 200),
    )

    plans = [
        Plan(name=seed.name, stripe_price_id=seed.stripe_price_id, monthly_run_quota=seed.monthly_run_quota)
        for seed in seeds
    ]
    session.add_all(plans)
    try:
        session.commit()
    except SQLAlchemyError as exc:  # pragma: no cover - critical failure
        session.rollback()
        logger.error("plan_seed_failed", extra={"error": str(exc)})
        raise DatabaseBootstrapError("Failed to seed subscription plans") from exc
    logger.info("plans_seeded", extra={"count": len(plans)})


def _seed_demo_tenant(session: Session, logger: logging.Logger) -> None:
    """Seed a demo tenant with activation codes if it does not exist."""

    existing = session.query(Tenant).filter(Tenant.slug == "demo").first()
    if existing:
        logger.info("demo_tenant_exists", extra={"tenant_id": existing.id})
        return

    pro_plan: Plan | None = session.query(Plan).filter(Plan.name == "Pro").first()
    if pro_plan is None:
        raise DatabaseBootstrapError("Pro plan must exist before seeding demo data.")

    demo_tenant = Tenant(
        name="Demo Consulting Firm",
        slug="demo",
        logo_url="https://cdn.q2o.ai/assets/demo-logo.png",
        primary_color="#875A7B",
        domain="demo.quicktoobjective.com",
        email="demo@quicktoobjective.com",
        phone_number="+15555550123",
        otp_delivery_method="email",
        usage_quota=pro_plan.monthly_run_quota,
    )
    session.add(demo_tenant)
    session.flush()

    subscription = Subscription(
        tenant_id=demo_tenant.id,
        plan_id=pro_plan.id,
        state=SubscriptionState.active,
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow() + timedelta(days=30),
    )
    session.add(subscription)

    try:
        session.commit()
    except SQLAlchemyError as exc:  # pragma: no cover - critical failure
        session.rollback()
        logger.error("demo_tenant_failed", extra={"error": str(exc)})
        raise DatabaseBootstrapError("Unable to insert demo tenant") from exc

    generated_codes: List[str] = generate_codes(
        session=session,
        tenant_id=demo_tenant.id,
        count=3,
        ttl_days=30,
        label="Demo Bootstrap Code",
        max_uses=1,
    )
    logger.info(
        "demo_tenant_seeded",
        extra={"tenant_id": demo_tenant.id, "activation_codes": generated_codes},
    )


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Bootstrap the Q2O Licensing database schema.",
    )
    parser.add_argument(
        "--seed-demo",
        action="store_true",
        help="Create a demo tenant with activation codes for smoke testing.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser.parse_args()


def main() -> int:
    """Entrypoint for the bootstrap script."""

    args = _parse_args()
    logger = _configure_logger(verbose=args.verbose)
    logger.info("bootstrap_start")
    try:
        _create_schema(logger)
        with Session(engine) as session:
            _seed_plans(session, logger)
            if args.seed_demo:
                _seed_demo_tenant(session, logger)
    except DatabaseBootstrapError:
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("bootstrap_unhandled_exception", extra={"error": str(exc)})
        return 1

    logger.info("bootstrap_complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())

