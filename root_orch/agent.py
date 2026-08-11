"""Root orchestrator: classifies intent, fans out to specialists, synthesizes.

Uses AgentTool (not sub-agent transfer) for the specialists so a single request
can hit more than one of them and get merged into one answer — transfer hands
off the whole turn to one sub-agent and can't do that.
"""

import logging
import os

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

from .agent1.agent import access_agent
from .agent2.agent import hardware_agent
from .agent3.agent import licensing_agent

try:
    import google.cloud.logging

    google.cloud.logging.Client().setup_logging()
except Exception:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")

log = logging.getLogger("it-support-agent")

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")

INSTRUCTION = """\
You are the IT Support Triage orchestrator. For every user request:

1. Classify the intent. A request may span MORE THAN ONE domain
   (e.g. "my VPN is down and I need a Tableau license" spans access + licensing).
2. Route by CALLING the specialist tools you need:
     - access_agent      -> account / VPN / login / shared-drive access
     - hardware_agent     -> laptops / devices / asset status / warranty
     - licensing_agent    -> software license requests & approvals
   For a multi-domain request, call EACH relevant specialist. Don't force
   everything through one specialist.
3. If nothing clearly matches, ask ONE concise clarifying question instead of
   guessing.
4. Synthesize a SINGLE coherent reply. Merge the specialists' results, state
   follow-up actions taken, and surface failures plainly rather than hiding them.

Never fabricate ticket ids, asset details, or approvals — only report what the
tools returned.
"""


def _log_agent_enter(**kwargs):
    ctx = kwargs.get("callback_context")
    name = getattr(ctx, "agent_name", "?")
    log.info(f'event=agent_enter agent="{name}"')


def _log_tool_call(**kwargs):
    tool = kwargs.get("tool")
    log.info(f'event=tool_call tool="{getattr(tool, "name", tool)}" args={kwargs.get("args")}')


def _log_tool_result(**kwargs):
    tool = kwargs.get("tool")
    resp = kwargs.get("tool_response")
    status = resp.get("status") if isinstance(resp, dict) else "n/a"
    log.info(f'event=tool_result tool="{getattr(tool, "name", tool)}" status={status}')


root_agent = LlmAgent(
    model=MODEL,
    name="it_support_orchestrator",
    description="Root IT support triage orchestrator: classifies, routes, synthesizes.",
    instruction=INSTRUCTION,
    tools=[
        AgentTool(agent=access_agent),
        AgentTool(agent=hardware_agent),
        AgentTool(agent=licensing_agent),
    ],
    before_agent_callback=_log_agent_enter,
    before_tool_callback=_log_tool_call,
    after_tool_callback=_log_tool_result,
)
