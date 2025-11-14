"""
GraphQL Router for FastAPI

Integrates Strawberry GraphQL with FastAPI, providing:
- /graphql endpoint for queries and mutations
- /graphql (GET) GraphiQL playground for development
- /graphql/subscriptions for WebSocket subscriptions
"""
from fastapi import APIRouter, Depends
from strawberry.fastapi import GraphQLRouter as StrawberryRouter

from .schema import schema
from .context import get_graphql_context, GraphQLContext
from ..core.logging import get_logger

logger = get_logger(__name__)

# Create FastAPI router
router = APIRouter(
    prefix="/graphql",
    tags=["GraphQL - Multi-Agent Dashboard"]
)

# Create Strawberry GraphQL router with schema and context
graphql_router = StrawberryRouter(
    schema=schema,
    context_getter=get_graphql_context,
    # Enable GraphiQL playground in development
    graphiql=True,  # Set to False in production
)

# Mount GraphQL router
# This creates:
# - POST /graphql - Execute GraphQL queries/mutations
# - GET /graphql - GraphiQL playground (if enabled)
router.include_router(graphql_router)

logger.info("GraphQL router initialized")
logger.info("  - Endpoint: POST /graphql")
logger.info("  - Playground: GET /graphql (GraphiQL)")
logger.info("  - Subscriptions: WS /graphql (WebSocket)")

