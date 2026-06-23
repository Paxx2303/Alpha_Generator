#!/bin/bash
# GCE VM setup — idempotent.
# Installs Docker + Ollama, clones repos, starts DeerFlow via its own Docker Compose.
# Observation dashboard runs on Cloud Run (separate job in deploy.yml).

set -e

echo "=== Alpha VM Setup $(date) ==="

# ── Docker ────────────────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  echo "Installing Docker..."
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker "$USER"
  exec sg docker "bash $0 $*"
fi

if ! docker compose version &>/dev/null; then
  sudo apt-get install -y docker-compose-plugin
fi

# ── Directories ───────────────────────────────────────────────────────────────
sudo mkdir -p /app && sudo chown "$USER":"$USER" /app
mkdir -p /app/logs

# ── Clone / update repos ──────────────────────────────────────────────────────
if [ ! -d /app/deer-flow/.git ]; then
  echo "Cloning DeerFlow..."
  rm -rf /app/deer-flow
  git clone https://github.com/bytedance/deer-flow.git /app/deer-flow
fi

if [ ! -d /app/alpha-generator ]; then
  echo "Cloning Alpha Generator..."
  git clone https://github.com/Paxx2303/Alpha_Generator.git /app/alpha-generator
else
  echo "Updating Alpha Generator..."
  cd /app/alpha-generator && git fetch origin && git reset --hard origin/main
fi

# ── Sync DeerFlow configs ─────────────────────────────────────────────────────
echo "Syncing DeerFlow configs..."
cp /app/alpha-generator/operation/deerflow/config.yaml /app/deer-flow/config.yaml
cp /app/alpha-generator/operation/deerflow/extensions_config.json /app/deer-flow/extensions_config.json
# /app/deer-flow is owned by root (Docker creates it) — need sudo
sudo mkdir -p /app/deer-flow/skills/custom/alpha-research
sudo cp /app/alpha-generator/operation/deerflow/skills/alpha-research/SKILL.md \
   /app/deer-flow/skills/custom/alpha-research/SKILL.md
sudo chmod -R 755 /app/deer-flow/skills/custom/

# ── .env guard ───────────────────────────────────────────────────────────────
if [ -f /tmp/alpha-deerflow.env ]; then
  cp /tmp/alpha-deerflow.env /app/deer-flow/.env
  rm /tmp/alpha-deerflow.env
elif [ ! -f /app/deer-flow/.env ]; then
  cp /app/deer-flow/.env.example /app/deer-flow/.env
  echo "WARNING: using .env.example — fill in WQB credentials."
fi

# ── NVIDIA Container Toolkit (only if GPU present) ───────────────────────────
if command -v nvidia-smi &>/dev/null && ! command -v nvidia-ctk &>/dev/null; then
  echo "Installing NVIDIA Container Toolkit..."
  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
    | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
  curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
    | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
    | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
  sudo apt-get update -qq
  sudo apt-get install -y nvidia-container-toolkit
  sudo nvidia-ctk runtime configure --runtime=docker
  sudo systemctl restart docker
fi

# ── Ollama (local LLM) ────────────────────────────────────────────────────────
if ! command -v ollama &>/dev/null; then
  echo "Installing Ollama..."
  curl -fsSL https://ollama.com/install.sh | sh
fi
# Configure Ollama to listen on all interfaces so Docker containers can reach it
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo tee /etc/systemd/system/ollama.service.d/env.conf > /dev/null << 'OLLAMA_ENV'
[Service]
Environment="OLLAMA_HOST=0.0.0.0"
OLLAMA_ENV
sudo systemctl daemon-reload
sudo systemctl enable ollama 2>/dev/null || true
sudo systemctl restart ollama

echo "Waiting for Ollama..."
for i in $(seq 1 15); do
  curl -s http://localhost:11434/api/tags >/dev/null 2>&1 && echo "Ollama ready." && break
  sleep 2
done

# Remove local models — using OpenRouter API instead (no RAM needed)
if ollama list 2>/dev/null | grep -q "qwen2.5"; then
  echo "Removing qwen2.5 models to free RAM..."
  ollama rm qwen2.5:14b 2>/dev/null || true
  ollama rm qwen2.5:7b  2>/dev/null || true
fi

# ── Initial data files ────────────────────────────────────────────────────────
mkdir -p /app/alpha-generator/data
if [ ! -f /app/alpha-generator/data/research_status.json ]; then
  cat > /app/alpha-generator/data/research_status.json << 'EOF'
{"agent_state":"idle","status":"idle","current_task":"Waiting for first cycle","current_cycle":0,"last_updated":null}
EOF
fi

# ── Python deps for MCP server ────────────────────────────────────────────────
pip3 install -r /app/alpha-generator/requirements.txt --quiet || echo "WARNING: some pip packages failed to install"

# ── Ensure DeerFlow sub-env files exist (setup wizard normally does this) ────
for example in /app/deer-flow/frontend/.env.example /app/deer-flow/backend/.env.example; do
  target="${example%.example}"
  if [ -f "$example" ] && [ ! -f "$target" ]; then
    cp "$example" "$target"
    echo "Created $target from example"
  fi
done

# ── Inject build-time env vars into frontend/.env (NEXT_PUBLIC_* are baked at build) ──
FRONTEND_ENV=/app/deer-flow/frontend/.env
touch "$FRONTEND_ENV"
# Custom agent management — enables /workspace/agents UI and POST /api/agents
grep -q "NEXT_PUBLIC_ENABLE_CUSTOM_AGENT_MANAGEMENT" "$FRONTEND_ENV" \
  || echo "NEXT_PUBLIC_ENABLE_CUSTOM_AGENT_MANAGEMENT=true" >> "$FRONTEND_ENV"
# Inject backend env vars for gateway build (non-NEXT_PUBLIC)
BACKEND_ENV=/app/deer-flow/backend/.env
touch "$BACKEND_ENV"
grep -q "ENABLE_CUSTOM_AGENT_MANAGEMENT" "$BACKEND_ENV" \
  || echo "ENABLE_CUSTOM_AGENT_MANAGEMENT=true" >> "$BACKEND_ENV"
echo "Frontend/backend .env patched for agent management."

# ── Start DeerFlow via Docker Compose ────────────────────────────────────────
echo "Starting DeerFlow..."
cd /app/deer-flow
# --env-file: compose file is in docker/, so Compose looks for .env in docker/ by default
# override: adds host.docker.internal and skills volume mount
# --force-recreate: ensure all containers pick up new env vars / config
docker compose \
  --env-file /app/deer-flow/.env \
  -f docker/docker-compose.yaml \
  -f /app/alpha-generator/deploy/docker-compose.override.yml \
  up -d --build --force-recreate

sudo docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# ── MCP server (SSE on host port 8765) ───────────────────────────────────────
echo "Starting MCP server (SSE mode)..."

# Load credentials from .env
if [ -f /app/deer-flow/.env ]; then
  set -a
  # shellcheck disable=SC1091
  source /app/deer-flow/.env
  set +a
fi

# ── MCP server (systemd service) ──────────────────────────────────────────────
sudo tee /etc/systemd/system/alpha-mcp.service > /dev/null << 'SYSTEMD_MCP'
[Unit]
Description=Alpha Generator MCP Server (SSE)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/app/alpha-generator
EnvironmentFile=/app/deer-flow/.env
Environment=MCP_TRANSPORT=sse
Environment=MCP_PORT=8765
ExecStart=/usr/bin/python3 /app/alpha-generator/core/mcp/server.py
Restart=always
RestartSec=10
StandardOutput=append:/app/logs/mcp-server.log
StandardError=append:/app/logs/mcp-server.log

[Install]
WantedBy=multi-user.target
SYSTEMD_MCP

# ── Research daemon (systemd service) ─────────────────────────────────────────
sudo tee /etc/systemd/system/alpha-research.service > /dev/null << 'SYSTEMD_RESEARCH'
[Unit]
Description=Alpha Research Daemon (autonomous market rotation)
After=network.target alpha-mcp.service
Requires=alpha-mcp.service

[Service]
Type=simple
User=root
WorkingDirectory=/app/alpha-generator
EnvironmentFile=/app/deer-flow/.env
Environment=DEERFLOW_GATEWAY_URL=http://localhost:8001
ExecStart=/usr/bin/python3 /app/alpha-generator/operation/research_daemon.py
Restart=always
RestartSec=30
StandardOutput=append:/app/logs/research-daemon.log
StandardError=append:/app/logs/research-daemon.log

[Install]
WantedBy=multi-user.target
SYSTEMD_RESEARCH

sudo systemctl daemon-reload
sudo systemctl enable alpha-mcp alpha-research
sudo systemctl restart alpha-mcp
echo "Waiting for MCP SSE..."
for i in $(seq 1 15); do
  curl -s --max-time 2 http://localhost:8765/sse >/dev/null 2>&1 && echo "MCP SSE ready." && break
  sleep 2
done
sudo systemctl restart alpha-research

VM_IP=$(curl -s --max-time 5 ifconfig.me 2>/dev/null || echo "<VM_IP>")
echo ""
echo "===================================================="
echo "  DeerFlow:       http://${VM_IP}/"
echo "  Ollama:         http://${VM_IP}:11434"
echo "  MCP status:     sudo systemctl status alpha-mcp"
echo "  Research status:sudo systemctl status alpha-research"
echo "  MCP logs:       tail -f /app/logs/mcp-server.log"
echo "  Research logs:  tail -f /app/logs/research-daemon.log"
echo "===================================================="
