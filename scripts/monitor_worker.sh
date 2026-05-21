#!/bin/bash
# Script để monitor Alpha Queue Worker

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

clear

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         Alpha Queue Worker Monitor                        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}\n"

# Function to show service status
show_service_status() {
    echo -e "${BLUE}=== Service Status ===${NC}"
    if systemctl is-active --quiet alpha-queue-worker.service; then
        echo -e "Status: ${GREEN}RUNNING${NC}"
        PID=$(systemctl show -p MainPID --value alpha-queue-worker.service)
        echo -e "PID: ${GREEN}$PID${NC}"
        
        # Get uptime
        UPTIME=$(systemctl show -p ActiveEnterTimestamp --value alpha-queue-worker.service)
        echo -e "Started: ${GREEN}$UPTIME${NC}"
    else
        echo -e "Status: ${RED}STOPPED${NC}"
    fi
    echo ""
}

# Function to show queue status
show_queue_status() {
    echo -e "${BLUE}=== Queue Status ===${NC}"
    cd "$PROJECT_DIR"
    python3 scripts/queue_manager_cli.py status 2>/dev/null || echo -e "${RED}Failed to get queue status${NC}"
    echo ""
}

# Function to show recent logs
show_recent_logs() {
    echo -e "${BLUE}=== Recent Logs (last 10 lines) ===${NC}"
    if [ -f "$PROJECT_DIR/logs/queue_worker.log" ]; then
        tail -n 10 "$PROJECT_DIR/logs/queue_worker.log"
    else
        echo -e "${YELLOW}No logs found${NC}"
    fi
    echo ""
}

# Function to show resource usage
show_resource_usage() {
    echo -e "${BLUE}=== Resource Usage ===${NC}"
    if systemctl is-active --quiet alpha-queue-worker.service; then
        PID=$(systemctl show -p MainPID --value alpha-queue-worker.service)
        if [ "$PID" != "0" ]; then
            # CPU and Memory
            ps -p $PID -o %cpu,%mem,rss,vsz,cmd --no-headers | while read line; do
                echo -e "CPU: ${GREEN}$(echo $line | awk '{print $1}')%${NC}"
                echo -e "Memory: ${GREEN}$(echo $line | awk '{print $2}')%${NC}"
                echo -e "RSS: ${GREEN}$(echo $line | awk '{print $3}')${NC} KB"
                echo -e "VSZ: ${GREEN}$(echo $line | awk '{print $4}')${NC} KB"
            done
        fi
    else
        echo -e "${YELLOW}Service not running${NC}"
    fi
    echo ""
}

# Main loop
while true; do
    clear
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║         Alpha Queue Worker Monitor                        ║${NC}"
    echo -e "${GREEN}║         $(date '+%Y-%m-%d %H:%M:%S')                              ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}\n"
    
    show_service_status
    show_resource_usage
    show_queue_status
    show_recent_logs
    
    echo -e "${YELLOW}Press Ctrl+C to exit. Refreshing in 5 seconds...${NC}"
    sleep 5
done
