# MCP server — deployed as its own Cloud Run service, separate from the agent.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run injects PORT (default 8080). FastMCP binds HOST/PORT from env.
ENV HOST=0.0.0.0
EXPOSE 8080

# Run flat (context is ./mcp_server), so server.py uses `import logic`.
CMD exec python server.py
