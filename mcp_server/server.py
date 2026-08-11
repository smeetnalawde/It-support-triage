"""MCP server: exposes the 4 IT support tools over streamable-http.

Run locally: python -m mcp_server.server  (serves http://localhost:8080/mcp)
Cloud Run listens on $PORT.
"""

from __future__ import annotations

import logging
import os

from mcp.server.fastmcp import FastMCP

try:
    from . import logic
except ImportError:
    import logic  # type: ignore  # flat import inside the container

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
log = logging.getLogger("it-support-mcp")

mcp = FastMCP(
    "it-support",
    host=os.environ.get("HOST", "0.0.0.0"),
    port=int(os.environ.get("PORT", "8080")),
)


@mcp.tool()
def check_user_access(user_id: str, resource: str) -> dict:
    """Check whether a user has access to a named resource (e.g. a shared drive)."""
    log.info(f"tool=check_user_access user_id={user_id} resource={resource}")
    return logic.check_user_access(user_id, resource)


@mcp.tool()
def reset_vpn_credentials(user_id: str) -> dict:
    """Reset a user's VPN credentials and issue a short-lived temporary token."""
    log.info(f"tool=reset_vpn_credentials user_id={user_id}")
    return logic.reset_vpn_credentials(user_id)


@mcp.tool()
def get_asset_status(asset_tag: str) -> dict:
    """Look up the lifecycle/warranty status of a hardware asset by tag."""
    log.info(f"tool=get_asset_status asset_tag={asset_tag}")
    return logic.get_asset_status(asset_tag)


@mcp.tool()
def request_license_approval(user_id: str, software: str, seats: int = 1) -> dict:
    """Submit a software license request; cheap seats auto-approve, others go to review."""
    log.info(f"tool=request_license_approval user_id={user_id} software={software} seats={seats}")
    return logic.request_license_approval(user_id, software, seats)


if __name__ == "__main__":
    log.info("starting IT Support MCP server (transport=streamable-http)")
    mcp.run(transport="streamable-http")
