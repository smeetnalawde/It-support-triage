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
    O -- AgentTool --> A[access_agent]
    O -- AgentTool --> H[hardware_agent]
    O -- AgentTool --> L[licensing_agent]

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

**Why `main.py` points `agents_dir` at `root_orch/` specifically:** ADK's
directory-based agent discovery treats any folder with an `agent.py` as a
selectable top-level app — `access_agent`, `hardware_agent`, and
`licensing_agent` all have one. Pointing `agents_dir` at `root_orch` puts
ADK's loader in single-agent mode: only `root_orch` is ever discoverable,
regardless of what other agent folders sit alongside it. Verified directly —
`/list-apps` returns `["root_orch"]` only, and requesting a session on any
specialist folder returns 404.

## Layout

```
main.py                 # explicit FastAPI entrypoint (get_fast_api_app) — what actually runs
Dockerfile               # agent service image
requirements.txt         # agent service deps

root_orch/
  agent.py               # root_agent: routes + fans out + synthesizes
  auth.py                # OIDC token minting for the private MCP call
  classifier.py           # deterministic routing spec / test oracle

access_agent/agent.py     # access specialist
hardware_agent/agent.py    # hardware specialist
licensing_agent/agent.py    # licensing specialist

mcp_server/
  logic.py                # pure tool logic, no MCP dep — unit-testable alone
  server.py                # FastMCP adapter, streamable-http
  Dockerfile

tests/                     # routing + e2e tests for the agent side
mcp_server/tests/           # tool logic tests
.github/workflows/ci.yml      # lint + test on every push; deploy on manual dispatch
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
```

Terminal 2 — set these env vars, then start the agent:
```bash
export MODEL=gemini-2.5-flash
export GOOGLE_GENAI_USE_VERTEXAI=TRUE
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_CLOUD_LOCATION=us-central1
export MCP_SERVER_URL=http://localhost:8080/mcp
export MCP_REQUIRE_AUTH=false

python main.py                     # serves the ADK web UI on :8080
```

Two terminals because these are two independent services talking over HTTP —
running them separately locally mirrors the two separate Cloud Run services in
production, rather than hiding the boundary in one process.

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
without them it's a documented, inert reference of the exact deploy steps. The
services in this project were deployed directly via `gcloud run deploy` for
speed during development.

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
