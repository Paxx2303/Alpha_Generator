#!/bin/bash
# Script để cài đặt Alpha Queue Worker như systemd service

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Installing Alpha Queue Worker Service ===${NC}\n"

# Get current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Project directory: $PROJECT_DIR"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

# Get Python path
PYTHON_PATH=$(which python3)
if [ -z "$PYTHON_PATH" ]; then
    echo -e "${RED}Python3 not found${NC}"
    exit 1
fi
echo "Python path: $PYTHON_PATH"

# Get current user
CURRENT_USER=${SUDO_USER:-$USER}
echo "Service will run as user: $CURRENT_USER"

# Create logs directory
mkdir -p "$PROJECT_DIR/logs"
chown -R $CURRENT_USER:$CURRENT_USER "$PROJECT_DIR/logs"

# Create service file
SERVICE_FILE="/etc/systemd/system/alpha-queue-worker.service"
echo -e "\n${YELLOW}Creating service file: $SERVICE_FILE${NC}"

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Alpha Queue Worker - Process alpha generation jobs from queue
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"

# Main command
ExecStart=$PYTHON_PATH $PROJECT_DIR/main.py --queue-worker --poll-interval 5.0

# Restart policy
Restart=always
RestartSec=10
StartLimitInterval=200
StartLimitBurst=5

# Logging
StandardOutput=append:$PROJECT_DIR/logs/queue_worker.log
StandardError=append:$PROJECT_DIR/logs/queue_worker_error.log

# Resource limits
LimitNOFILE=65536

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✓ Service file created${NC}"

# Reload systemd
echo -e "\n${YELLOW}Reloading systemd daemon...${NC}"
systemctl daemon-reload
echo -e "${GREEN}✓ Systemd reloaded${NC}"

# Enable service
echo -e "\n${YELLOW}Enabling service...${NC}"
systemctl enable alpha-queue-worker.service
echo -e "${GREEN}✓ Service enabled${NC}"

echo -e "\n${GREEN}=== Installation Complete ===${NC}\n"
echo "Service commands:"
echo "  Start:   sudo systemctl start alpha-queue-worker"
echo "  Stop:    sudo systemctl stop alpha-queue-worker"
echo "  Restart: sudo systemctl restart alpha-queue-worker"
echo "  Status:  sudo systemctl status alpha-queue-worker"
echo "  Logs:    sudo journalctl -u alpha-queue-worker -f"
echo ""
echo "To start the service now, run:"
echo "  sudo systemctl start alpha-queue-worker"
