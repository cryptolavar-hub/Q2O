"""
GraphQL Schema Builder

Combines types, queries, mutations, and subscriptions into a single schema.
"""
import strawberry
from .resolvers import Query, Mutation, Subscription


# Build the complete GraphQL schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    # Enable introspection for GraphiQL playground
    enable_federation_2=False
)

