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
mkdir -p /app/deer-flow/skills/alpha-research
cp /app/alpha-generator/operation/deerflow/skills/alpha-research/SKILL.md \
   /app/deer-flow/skills/alpha-research/SKILL.md

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
sudo systemctl enable ollama 2>/dev/null || true
sudo systemctl start ollama  2>/dev/null || true

echo "Waiting for Ollama..."
for i in $(seq 1 15); do
  curl -s http://localhost:11434/api/tags >/dev/null 2>&1 && echo "Ollama ready." && break
  sleep 2
done

if ! ollama list 2>/dev/null | grep -q "qwen2.5:14b"; then
  echo "Pulling qwen2.5:14b in background (~9GB)..."
  nohup ollama pull qwen2.5:14b >> /app/logs/ollama-pull.log 2>&1 &
else
  echo "qwen2.5:14b already present."
fi

# ── Initial data files ────────────────────────────────────────────────────────
mkdir -p /app/alpha-generator/data
if [ ! -f /app/alpha-generator/data/research_status.json ]; then
  cat > /app/alpha-generator/data/research_status.json << 'EOF'
{"agent_state":"idle","status":"idle","current_task":"Waiting for first cycle","current_cycle":0,"last_updated":null}
EOF
fi

# ── Python deps for runner.py ─────────────────────────────────────────────────
pip3 install requests python-dotenv --quiet 2>/dev/null || true

# ── Cronjob: research cycle every 6 hours ────────────────────────────────────
CRON_JOB="0 */6 * * * cd /app/alpha-generator && python3 operation/runner.py >> /app/logs/runner.log 2>&1"
( crontab -l 2>/dev/null | grep -v "runner.py"; echo "$CRON_JOB" ) | crontab -

# ── Ensure DeerFlow sub-env files exist (setup wizard normally does this) ────
for example in /app/deer-flow/frontend/.env.example /app/deer-flow/backend/.env.example; do
  target="${example%.example}"
  if [ -f "$example" ] && [ ! -f "$target" ]; then
    cp "$example" "$target"
    echo "Created $target from example"
  fi
done

# ── Start DeerFlow via Docker Compose ────────────────────────────────────────
echo "Starting DeerFlow..."
cd /app/deer-flow
# --env-file: compose file is in docker/, so Compose looks for .env in docker/ by default
# override: adds host.docker.internal so containers can reach Ollama on host
docker compose \
  --env-file /app/deer-flow/.env \
  -f docker/docker-compose.yaml \
  -f /app/alpha-generator/deploy/docker-compose.override.yml \
  up -d --build

docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

VM_IP=$(curl -s --max-time 5 ifconfig.me 2>/dev/null || echo "<VM_IP>")
echo ""
echo "===================================================="
echo "  DeerFlow:   http://${VM_IP}/"
echo "  Ollama:     http://${VM_IP}:11434"
echo "  Logs:       docker compose -f /app/deer-flow/docker/docker-compose.yaml logs -f"
echo "  Runner:     cd /app/alpha-generator && python3 operation/runner.py --dry-run"
echo "===================================================="
