"""FastAPI entrypoint for the agent service.

agents_dir points at root_orch/ directly (not the repo root) so ADK's loader
locks to single-agent mode -- otherwise the specialist agent folders would
each show up as separate, broken, selectable apps.
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
