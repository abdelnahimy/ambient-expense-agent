import json
import logging
import os

import uvicorn
from fastapi import FastAPI, Request
from google.adk.cli.fast_api import get_fast_api_app

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# The ADK needs the project root as agents_dir so it discovers
# expense_agent/ as an agent package.
AGENTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app: FastAPI = get_fast_api_app(
    agents_dir=AGENTS_DIR,
    web=True,
    trigger_sources=["pubsub"],
    otel_to_cloud=False,
)


@app.middleware("http")
async def normalize_pubsub_subscription(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Normalize ``projects/.../subscriptions/NAME`` to just ``NAME``.

    Pub/Sub push deliveries include the fully-qualified subscription
    resource path. The ADK trigger handler uses this value as the
    session ``user_id``. Normalizing to the short name keeps session
    records clean and consistent with the subscription name used by
    the frontend when querying for pending approvals.
    """
    logging.info(f"Middleware intercepted request to: {request.url.path} Method: {request.method}")
    if request.url.path.endswith("/trigger/pubsub") and request.method == "POST":
        body = await request.body()
        logging.info(f"Middleware read body: {body}")
        try:
            data = json.loads(body)
            sub = data.get("subscription", "")
            if "/" in sub:
                data["subscription"] = sub.rsplit("/", 1)[-1]
                # Fast API replaces request body
                async def new_receive():  # type: ignore[no-untyped-def]
                    return {"type": "http.request", "body": json.dumps(data).encode()}
                
                request._receive = new_receive
        except Exception as e:
            logging.error(f"Middleware error: {e} Body: {body}")
            pass
    return await call_next(request)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
    )
