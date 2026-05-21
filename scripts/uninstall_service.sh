#!/bin/bash
# Script để gỡ cài đặt Alpha Queue Worker service

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Uninstalling Alpha Queue Worker Service ===${NC}\n"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

SERVICE_FILE="/etc/systemd/system/alpha-queue-worker.service"

# Check if service exists
if [ ! -f "$SERVICE_FILE" ]; then
    echo -e "${YELLOW}Service file not found. Nothing to uninstall.${NC}"
    exit 0
fi

# Stop service if running
echo -e "${YELLOW}Stopping service...${NC}"
systemctl stop alpha-queue-worker.service 2>/dev/null || true
echo -e "${GREEN}✓ Service stopped${NC}"

# Disable service
echo -e "\n${YELLOW}Disabling service...${NC}"
systemctl disable alpha-queue-worker.service 2>/dev/null || true
echo -e "${GREEN}✓ Service disabled${NC}"

# Remove service file
echo -e "\n${YELLOW}Removing service file...${NC}"
rm -f "$SERVICE_FILE"
echo -e "${GREEN}✓ Service file removed${NC}"

# Reload systemd
echo -e "\n${YELLOW}Reloading systemd daemon...${NC}"
systemctl daemon-reload
echo -e "${GREEN}✓ Systemd reloaded${NC}"

echo -e "\n${GREEN}=== Uninstallation Complete ===${NC}\n"
