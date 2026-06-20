#!/bin/bash
# GCE VM initial setup script for alpha-vm (e2-standard-4, Ubuntu 22.04)
# Run once after VM creation:
#   gcloud compute ssh alpha-vm --zone=us-central1-a -- 'bash -s' < deploy/vm-setup.sh

set -e

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose plugin
sudo apt-get install -y docker-compose-plugin

# Install gcloud (for backup GCS uploads)
sudo apt-get install -y apt-transport-https ca-certificates gnupg
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
    | sudo tee /etc/apt/sources.list.d/google-cloud-sdk.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg \
    | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
sudo apt-get update && sudo apt-get install -y google-cloud-cli

# Clone DeerFlow
mkdir -p /app
cd /app
git clone https://github.com/bytedance/deer-flow.git deer-flow

# Clone Alpha Generator
git clone https://github.com/Paxx2303/Alpha_Generator.git alpha-generator

# Copy DeerFlow configs
cp /app/alpha-generator/operation/deerflow/config.yaml          /app/deer-flow/config.yaml
cp /app/alpha-generator/operation/deerflow/extensions_config.json /app/deer-flow/extensions_config.json
mkdir -p /app/deer-flow/skills/alpha-research
cp /app/alpha-generator/operation/deerflow/skills/alpha-research/SKILL.md \
   /app/deer-flow/skills/alpha-research/SKILL.md

# Set up .env (fill in manually after setup)
cp /app/alpha-generator/operation/deerflow/.env.example /app/deer-flow/.env
echo ""
echo "===================================================="
echo "  VM setup complete!"
echo "  Next steps:"
echo "  1. Edit /app/deer-flow/.env with real credentials"
echo "  2. cd /app/deer-flow && make setup"
echo "  3. docker compose -f docker-compose.yml \\"
echo "       -f ../alpha-generator/deploy/docker-compose.override.yml up -d"
echo "===================================================="
