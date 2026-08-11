"""FastAPI entrypoint for the agent service (root_orch + specialists).

Explicit instead of relying on `adk deploy`'s generated server, so the
deployment mechanics are visible and this file is what actually runs in the
container. Discovers root_agent from root_orch/ via agents_dir=".".
"""

import os

import uvicorn
from google.adk.cli.fast_api import get_fast_api_app

app = get_fast_api_app(
    agents_dir="root_orch",
    web=True,
    host="0.0.0.0",
    port=int(os.environ.get("PORT", "8080")),
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
