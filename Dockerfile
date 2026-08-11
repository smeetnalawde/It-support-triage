# Agent service (root_orch + agent1/2/3), served by main.py. Deployed
# separately from mcp_server — see .github/workflows/ci.yml.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY root_orch/ root_orch/
COPY access_agent/ access_agent/
COPY hardware_agent/ hardware_agent/
COPY licensing_agent/ licensing_agent/
COPY main.py .

ENV PORT=8080
EXPOSE 8080

CMD ["python", "main.py"]
