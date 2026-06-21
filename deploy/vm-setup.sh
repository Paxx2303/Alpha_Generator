#!/bin/bash
# GCE VM setup script — fully automated, idempotent.
# Called by GitHub Actions deploy job on first boot and on every push.
#
# First-run:  installs Docker, clones repos, runs DeerFlow make setup, starts compose
# Update-run: git pull, syncs configs, restarts observation container
#
# .env MUST exist at /app/deer-flow/.env before this script runs.
# The GitHub Actions job writes it from Secrets before calling this script.

set -e

echo "=== Alpha VM Setup $(date) ==="

# ── Docker ────────────────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  echo "Installing Docker..."
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker "$USER"
  # Re-exec with docker group active
  exec sg docker "bash $0 $*"
fi

if ! docker compose version &>/dev/null; then
  sudo apt-get install -y docker-compose-plugin
fi

# ── Directories ───────────────────────────────────────────────────────────────
sudo mkdir -p /app && sudo chown "$USER":"$USER" /app
mkdir -p /app/logs

# ── Clone / update repos ──────────────────────────────────────────────────────
if [ ! -d /app/deer-flow ]; then
  echo "Cloning DeerFlow..."
  git clone https://github.com/bytedance/deer-flow.git /app/deer-flow
fi

if [ ! -d /app/alpha-generator ]; then
  echo "Cloning Alpha Generator..."
  git clone https://github.com/Paxx2303/Alpha_Generator.git /app/alpha-generator
else
  echo "Updating Alpha Generator..."
  cd /app/alpha-generator && git pull
fi

# ── Sync DeerFlow configs ─────────────────────────────────────────────────────
echo "Syncing DeerFlow configs..."
cp /app/alpha-generator/operation/deerflow/config.yaml          /app/deer-flow/config.yaml
cp /app/alpha-generator/operation/deerflow/extensions_config.json /app/deer-flow/extensions_config.json
mkdir -p /app/deer-flow/skills/alpha-research
cp /app/alpha-generator/operation/deerflow/skills/alpha-research/SKILL.md \
   /app/deer-flow/skills/alpha-research/SKILL.md

# ── .env guard ───────────────────────────────────────────────────────────────
# Deploy job writes /tmp/alpha-deerflow.env before this script runs.
# Move it into place after deer-flow is cloned.
if [ -f /tmp/alpha-deerflow.env ]; then
  cp /tmp/alpha-deerflow.env /app/deer-flow/.env
  rm /tmp/alpha-deerflow.env
elif [ ! -f /app/deer-flow/.env ]; then
  cp /app/alpha-generator/operation/deerflow/.env.example /app/deer-flow/.env
  echo "WARNING: /app/deer-flow/.env missing — copied from example. Fill in real credentials."
fi

# ── NVIDIA Container Toolkit (Docker GPU support) ────────────────────────────
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
  echo "NVIDIA Container Toolkit installed."
fi

# ── Ollama (local LLM — Qwen2.5:14b) ─────────────────────────────────────────
if ! command -v ollama &>/dev/null; then
  echo "Installing Ollama..."
  curl -fsSL https://ollama.com/install.sh | sh
fi

# Enable and start Ollama service
sudo systemctl enable ollama 2>/dev/null || true
sudo systemctl start ollama  2>/dev/null || true

# Wait for Ollama to be ready
echo "Waiting for Ollama to start..."
for i in $(seq 1 15); do
  if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "Ollama ready."
    break
  fi
  sleep 2
done

# Pull Qwen2.5:14b (non-blocking on first run — model is ~9GB)
# Subsequent runs skip if already present.
if ! ollama list 2>/dev/null | grep -q "qwen2.5:14b"; then
  echo "Pulling qwen2.5:14b in background (~9GB, takes 5-10 min)..."
  nohup ollama pull qwen2.5:14b >> /app/logs/ollama-pull.log 2>&1 &
  echo "Pull running. Monitor: tail -f /app/logs/ollama-pull.log"
else
  echo "qwen2.5:14b already present — skipping pull."
fi

# ── DeerFlow Python environment ───────────────────────────────────────────────
command -v make &>/dev/null || sudo apt-get install -y make
# uv is required by DeerFlow's Makefile
if ! command -v uv &>/dev/null; then
  echo "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
fi
cd /app/deer-flow
if [ ! -d .venv ]; then
  echo "Installing DeerFlow dependencies (uv sync)..."
  # make setup has an interactive wizard that exits in non-TTY environments.
  # uv sync is all we need — config.yaml and .env are already in place.
  uv sync
fi

# ── Initial data files ────────────────────────────────────────────────────────
mkdir -p /app/alpha-generator/data
if [ ! -f /app/alpha-generator/data/research_status.json ]; then
  cat > /app/alpha-generator/data/research_status.json << 'EOF'
{
  "agent_state": "idle",
  "status": "idle",
  "current_task": "Waiting for first cycle",
  "current_cycle": 0,
  "last_updated": null
}
EOF
fi

# ── Python deps for runner.py ─────────────────────────────────────────────────
pip3 install requests python-dotenv --quiet 2>/dev/null || true

# ── Cronjob: research cycle every 6 hours ────────────────────────────────────
CRON_JOB="0 */6 * * * cd /app/alpha-generator && python3 operation/runner.py >> /app/logs/runner.log 2>&1"
( crontab -l 2>/dev/null | grep -v "runner.py"; echo "$CRON_JOB" ) | crontab -

# ── Start services ────────────────────────────────────────────────────────────
echo "Starting Docker Compose..."
cd /app/deer-flow
docker compose \
  -f docker-compose.yml \
  -f ../alpha-generator/deploy/docker-compose.override.yml \
  up -d --build

docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

PUBLIC_IP=$(curl -s --max-time 5 ifconfig.me 2>/dev/null || echo "<VM_IP>")
echo ""
echo "===================================================="
echo "  VM deploy complete!"
echo "  DeerFlow UI:  http://${PUBLIC_IP}/"
echo "  Dashboard:    http://${PUBLIC_IP}/observe/"
echo "  Logs:         docker compose -f /app/deer-flow/docker-compose.yml logs -f"
echo "  Runner test:  cd /app/alpha-generator && python3 operation/runner.py --dry-run"
echo "===================================================="
