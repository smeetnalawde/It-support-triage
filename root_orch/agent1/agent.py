"""Access specialist: VPN, login, shared-drive access."""

import os

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StreamableHTTPConnectionParams

from common.auth import mcp_auth_headers

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")
MCP_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8080/mcp")

access_agent = LlmAgent(
    model=MODEL,
    name="access_agent",
    description=(
        "Handles account, VPN, login, password, and shared-drive access issues. "
        "Use for anything about signing in, credentials, locked accounts, or "
        "permission to reach a resource."
    ),
    instruction=(
        "You are the Access specialist. Resolve the user's access/VPN/drive "
        "problem using your tools. If a tool returns status=error (e.g. "
        "ACCOUNT_LOCKED, USER_NOT_FOUND), don't retry blindly — explain what "
        "happened and state the concrete next action. Keep your summary short; "
        "the orchestrator will merge it into the final reply."
    ),
    tools=[
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=MCP_URL, headers=mcp_auth_headers(MCP_URL)
            ),
            tool_filter=["check_user_access", "reset_vpn_credentials"],
        )
    ],
)
