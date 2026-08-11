# IT Support Triage — Multi-Agent Orchestration (ADK + MCP + GCP)

Plain-language IT support triage. A root orchestrator classifies a request,
routes to one or more specialist agents, each of which calls tools on a
separately deployed MCP server, and synthesizes one reply.

Built with **Google ADK 2.6**, the **MCP Python SDK**, and **GCP** (two Cloud
Run services, Vertex AI/Gemini, IAM-based service-to-service auth).

## Architecture

```mermaid
flowchart TD
    U[User request] --> O[root_orch<br/>orchestrator]
    O -- AgentTool --> A[agent1<br/>access]
    O -- AgentTool --> H[agent2<br/>hardware]
    O -- AgentTool --> L[agent3<br/>licensing]

    A -- McpToolset --> M
    H -- McpToolset --> M
    L -- McpToolset --> M

    subgraph CR2[Cloud Run · mcp_server · private]
      M[MCP server] --> T1[check_user_access]
      M --> T2[reset_vpn_credentials]
      M --> T3[get_asset_status]
      M --> T4[request_license_approval]
    end

    subgraph CR1[Cloud Run · agent service · main.py]
      O
      A
      H
      L
    end

    O -. OIDC token · roles/run.invoker .-> M
    O -. Vertex AI · Gemini .-> V[(Vertex AI)]
```

**Why AgentTool, not sub-agent transfer:** transfer hands the whole turn to one
sub-agent. AgentTool keeps `root_orch` in control, so it can call more than one
specialist for a single request and merge their results — required for
requests that span domains (e.g. "VPN is down and I need a license").

**Why `agent1/agent2/agent3` live under `root_orch/`, not at repo root:** ADK's
directory-based agent discovery treats any folder with an `agent.py` as a
selectable top-level app. Nesting the specialists under `root_orch/` and
pointing `main.py` at `agents_dir="root_orch"` puts ADK in single-agent mode —
only `root_orch` is discoverable; the specialists stay library modules the
orchestrator imports, not separate apps a reviewer could accidentally select
and get an empty session.

## Layout

```
main.py              # explicit FastAPI entrypoint (get_fast_api_app), what actually runs
Dockerfile            # agent service image
requirements.txt      # agent service deps

root_orch/
  agent.py            # root_agent: routes + fans out + synthesizes
  agent1/agent.py      # access specialist
  agent2/agent.py      # hardware specialist
  agent3/agent.py       # licensing specialist

common/
  auth.py             # OIDC token minting for the private MCP call
  classifier.py        # deterministic routing spec / test oracle

mcp_server/
  logic.py            # pure tool logic, no MCP dep — unit-testable alone
  server.py            # FastMCP adapter, streamable-http
  Dockerfile

tests/                 # routing + e2e tests for the agent side
mcp_server/tests/       # tool logic tests
.github/workflows/ci.yml  # lint + test on every push; deploy on manual dispatch
```

## MCP tools

| Tool | Domain | Failure mode |
|------|--------|--------------|
| `check_user_access(user_id, resource)` | access | `USER_NOT_FOUND` |
| `reset_vpn_credentials(user_id)` | access | `ACCOUNT_LOCKED` |
| `get_asset_status(asset_tag)` | hardware | `ASSET_NOT_FOUND` |
| `request_license_approval(user_id, software, seats)` | licensing | `SOFTWARE_NOT_IN_CATALOG`, plus a legitimate `approved: false → manager_review` business outcome distinct from a tool error |

## Run locally

```bash
pip install -r mcp_server/requirements.txt
pip install -r requirements.txt
pip install -r requirements-dev.txt

python -m mcp_server.server        # terminal 1 — http://localhost:8080/mcp

cp .env.example .env               # terminal 2 — set GOOGLE_CLOUD_PROJECT
python main.py                     # serves the ADK web UI on :8080
```

Try: a single-domain request, a request spanning two domains (fan-out), and
`asset LAP-9999` (graceful failure — not in the mock asset table).

## Tests

```bash
MCP_REQUIRE_AUTH=false PYTHONPATH="." pytest mcp_server/tests tests -q
```

The e2e test needs live model credentials and skips without them, so CI stays
green.

## Deploy

`.github/workflows/ci.yml` has a `deploy` job (manual `workflow_dispatch`) that
does what a `gcloud` script would: enables the required APIs, deploys the MCP
server private, creates a dedicated agent service account with
`roles/aiplatform.user` and `roles/run.invoker` scoped to just the MCP
service, then deploys the agent private with that SA and the MCP URL wired in.
It needs `GCP_PROJECT_ID` and `GCP_SA_KEY` as repo secrets to actually run —
without them it's a documented, inert reference of the exact deploy steps.

To reach a private agent for a demo:
```bash
gcloud run services proxy it-support-agent --region us-central1 --port 8080
```

## Observability

Structured logs from `before_agent`/`before_tool`/`after_tool` callbacks show
which agent handled a request and each tool call's status, routed to Cloud
Logging on Cloud Run.

## Known limitations

- ID tokens are minted once at startup; a long-lived deployment should refresh
  them.
- Sessions are in-memory; durable state across restarts needs a backed
  session service.
- Tool backends in `logic.py` are mocked, as allowed — swapping in real
  systems touches only that file.
- `deploy` job needs its secrets configured to actually run; not wired live in
  this repo.
