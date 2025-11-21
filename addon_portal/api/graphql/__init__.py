"""
GraphQL API for Q2O Multi-Agent Dashboard

This module provides a flexible, bandwidth-optimized GraphQL API
for the customer-facing Multi-Agent Dashboard with real-time subscriptions.

Features:
- Flexible querying (clients request only what they need)
- Real-time subscriptions for live widgets
- Batch loading for performance
- Type-safe schema
"""

from .router import router

__all__ = ["router"]

