"""Mints an OIDC token so the agent can call the private MCP Cloud Run service."""

from __future__ import annotations

import logging
import os
from urllib.parse import urlparse

log = logging.getLogger("it-support-agent.auth")


def fetch_id_token(audience: str) -> str | None:
    """Return an OIDC ID token for `audience`, or None if creds aren't available."""
    try:
        import google.auth.transport.requests
        import google.oauth2.id_token

        request = google.auth.transport.requests.Request()
        return google.oauth2.id_token.fetch_id_token(request, audience)
    except Exception as exc:
        log.warning(f"could not mint id token ({exc}); calling MCP without auth header")
        return None


def mcp_auth_headers(mcp_url: str) -> dict[str, str]:
    """Build the auth header for the MCP connection. Set MCP_REQUIRE_AUTH=false to skip."""
    if os.environ.get("MCP_REQUIRE_AUTH", "true").lower() == "false":
        return {}

    parsed = urlparse(mcp_url)
    audience = f"{parsed.scheme}://{parsed.netloc}"
    token = fetch_id_token(audience)
    return {"Authorization": f"Bearer {token}"} if token else {}
