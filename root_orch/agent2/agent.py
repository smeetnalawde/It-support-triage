"""Hardware specialist: laptops, asset status, warranty."""

import os

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StreamableHTTPConnectionParams

from common.auth import mcp_auth_headers

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")
MCP_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8080/mcp")

hardware_agent = LlmAgent(
    model=MODEL,
    name="hardware_agent",
    description=(
        "Handles physical device and hardware issues: laptops, asset status, "
        "warranty, RMA. Use for a broken/failing device or an asset tag lookup."
    ),
    instruction=(
        "You are the Hardware specialist. Look up asset status with your tool. "
        "If it returns ASSET_NOT_FOUND, don't invent details — tell the user the "
        "tag wasn't found and ask them to confirm it or provide the serial "
        "number. Keep the summary short for the orchestrator to merge."
    ),
    tools=[
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=MCP_URL, headers=mcp_auth_headers(MCP_URL)
            ),
            tool_filter=["get_asset_status"],
        )
    ],
)
