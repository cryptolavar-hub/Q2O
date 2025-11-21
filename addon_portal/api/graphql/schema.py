"""
GraphQL Schema Builder

Combines types, queries, mutations, and subscriptions into a single schema.
"""
import strawberry
from .resolvers import Query, Mutation, Subscription


# Build the complete GraphQL schema
# Note: enable_federation_2 parameter was removed in strawberry 0.286.0+
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
)

