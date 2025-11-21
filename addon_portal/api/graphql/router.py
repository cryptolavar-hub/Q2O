"""
GraphQL Router for FastAPI

Integrates Strawberry GraphQL with FastAPI, providing:
- /graphql endpoint for queries and mutations
- /graphql (GET) GraphiQL playground for development
- /graphql/subscriptions for WebSocket subscriptions
"""
from strawberry.fastapi import GraphQLRouter as StrawberryRouter

from .schema import schema
from .context import get_graphql_context
from ..core.logging import get_logger

logger = get_logger(__name__)

# Create Strawberry GraphQL router with schema and context
# This IS a FastAPI router, so we export it directly
router = StrawberryRouter(
    schema=schema,
    context_getter=get_graphql_context,
    # Enable GraphiQL playground in development
    graphiql=True,  # Set to False in production
    path="/graphql",  # Explicit path for the GraphQL endpoint
)

logger.info("GraphQL router initialized")
logger.info("  - Endpoint: POST /graphql")
logger.info("  - Playground: GET /graphql (GraphiQL)")
logger.info("  - Subscriptions: WS /graphql (WebSocket)")

