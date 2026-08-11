"""Licensing specialist: software license requests and approvals."""

import os

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StreamableHTTPConnectionParams

from root_orch.auth import mcp_auth_headers

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")
MCP_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8080/mcp")

licensing_agent = LlmAgent(
    model=MODEL,
    name="licensing_agent",
    description=(
        "Handles software license requests and approvals. Use for requests to "
        "install/buy/approve software or add seats."
    ),
    instruction=(
        "You are the Licensing specialist. Submit license requests with your "
        "tool. Distinguish a tool ERROR (e.g. SOFTWARE_NOT_IN_CATALOG) from a "
        "legitimate business outcome where approved=false and the request was "
        "routed to manager_review. Report the ticket id and the approval route."
    ),
    tools=[
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=MCP_URL, headers=mcp_auth_headers(MCP_URL)
            ),
            tool_filter=["request_license_approval"],
        )
    ],
)
