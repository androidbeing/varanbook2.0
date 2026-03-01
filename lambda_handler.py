"""
lambda_handler.py – AWS Lambda entry point.

Mangum wraps the FastAPI ASGI app so that API Gateway v2 (HTTP API) events
are translated into standard ASGI scope/receive/send calls.

Lambda function handler setting: lambda_handler.handler
"""
import os

from mangum import Mangum

from app.main import create_app

# create_app() is called once during cold start (module load).
# Subsequent warm invocations reuse this instance.
_app = create_app()

# lifespan="off" – Lambda is ephemeral; we skip the startup/shutdown
# lifecycle (DB ping in startup) because the connection pool is created
# lazily on first query. Set to "on" only if you need startup hooks to
# run and you've tested it doesn't cause cold-start timeouts.
handler = Mangum(
    _app,
    lifespan="off",
    api_gateway_base_path=os.getenv("API_GW_BASE_PATH", "/"),
)
