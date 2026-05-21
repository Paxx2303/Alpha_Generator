#!/bin/bash
# Script để quản lý Alpha Queue Worker

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Function to show usage
show_usage() {
    echo -e "${GREEN}Alpha Queue Worker Control${NC}\n"
    echo "Usage: $0 {start|stop|restart|status|logs|monitor|add-job|queue-status}"
    echo ""
    echo "Commands:"
    echo "  start         - Start the worker"
    echo "  stop          - Stop the worker"
    echo "  restart       - Restart the worker"
    echo "  status        - Show worker status"
    echo "  logs          - Show worker logs (tail -f)"
    echo "  monitor       - Monitor worker (real-time)"
    echo "  add-job       - Add a job to queue (interactive)"
    echo "  queue-status  - Show queue status"
    echo ""
}

# Function to start worker
start_worker() {
    echo -e "${YELLOW}Starting worker...${NC}"
    
    # Check if systemd service exists
    if systemctl list-unit-files | grep -q alpha-queue-worker.service; then
        sudo systemctl start alpha-queue-worker.service
        echo -e "${GREEN}✓ Worker started (systemd service)${NC}"
    else
        # Start as background process
        cd "$PROJECT_DIR"
        nohup python3 main.py --queue-worker > logs/queue_worker.log 2>&1 &
        echo $! > runtime/worker.pid
        echo -e "${GREEN}✓ Worker started (PID: $(cat runtime/worker.pid))${NC}"
    fi
}

# Function to stop worker
stop_worker() {
    echo -e "${YELLOW}Stopping worker...${NC}"
    
    # Check if systemd service exists
    if systemctl list-unit-files | grep -q alpha-queue-worker.service; then
        sudo systemctl stop alpha-queue-worker.service
        echo -e "${GREEN}✓ Worker stopped (systemd service)${NC}"
    else
        # Stop background process
        if [ -f "$PROJECT_DIR/runtime/worker.pid" ]; then
            PID=$(cat "$PROJECT_DIR/runtime/worker.pid")
            kill -TERM $PID 2>/dev/null || true
            rm -f "$PROJECT_DIR/runtime/worker.pid"
            echo -e "${GREEN}✓ Worker stopped (PID: $PID)${NC}"
        else
            echo -e "${YELLOW}Worker PID file not found${NC}"
        fi
    fi
}

# Function to restart worker
restart_worker() {
    stop_worker
    sleep 2
    start_worker
}

# Function to show status
show_status() {
    echo -e "${BLUE}=== Worker Status ===${NC}\n"
    
    # Check if systemd service exists
    if systemctl list-unit-files | grep -q alpha-queue-worker.service; then
        systemctl status alpha-queue-worker.service --no-pager
    else
        if [ -f "$PROJECT_DIR/runtime/worker.pid" ]; then
            PID=$(cat "$PROJECT_DIR/runtime/worker.pid")
            if ps -p $PID > /dev/null 2>&1; then
                echo -e "Status: ${GREEN}RUNNING${NC}"
                echo -e "PID: ${GREEN}$PID${NC}"
                ps -p $PID -o %cpu,%mem,rss,cmd --no-headers
            else
                echo -e "Status: ${RED}STOPPED${NC} (stale PID file)"
                rm -f "$PROJECT_DIR/runtime/worker.pid"
            fi
        else
            echo -e "Status: ${RED}STOPPED${NC}"
        fi
    fi
}

# Function to show logs
show_logs() {
    echo -e "${BLUE}=== Worker Logs ===${NC}\n"
    
    if [ -f "$PROJECT_DIR/logs/queue_worker.log" ]; then
        tail -f "$PROJECT_DIR/logs/queue_worker.log"
    else
        echo -e "${YELLOW}No logs found${NC}"
    fi
}

# Function to monitor worker
monitor_worker() {
    bash "$SCRIPT_DIR/monitor_worker.sh"
}

# Function to add job (interactive)
add_job_interactive() {
    echo -e "${GREEN}=== Add Job to Queue ===${NC}\n"
    
    # Job type
    echo "Select job type:"
    echo "  1) pipeline"
    echo "  2) bruteforce"
    echo "  3) continuous"
    read -p "Enter choice [1-3]: " job_type_choice
    
    case $job_type_choice in
        1) JOB_TYPE="pipeline" ;;
        2) JOB_TYPE="bruteforce" ;;
        3) JOB_TYPE="continuous" ;;
        *) echo -e "${RED}Invalid choice${NC}"; return 1 ;;
    esac
    
    # Strategy type
    echo ""
    echo "Select strategy type:"
    echo "  1) momentum"
    echo "  2) mean-reversion"
    echo "  3) volume"
    read -p "Enter choice [1-3]: " strategy_choice
    
    case $strategy_choice in
        1) STRATEGY="momentum" ;;
        2) STRATEGY="mean-reversion" ;;
        3) STRATEGY="volume" ;;
        *) echo -e "${RED}Invalid choice${NC}"; return 1 ;;
    esac
    
    # Count
    read -p "Number of alphas to generate [default: 8]: " COUNT
    COUNT=${COUNT:-8}
    
    # Submit enabled
    read -p "Enable submission? [Y/n]: " SUBMIT
    SUBMIT=${SUBMIT:-Y}
    if [[ $SUBMIT =~ ^[Yy]$ ]]; then
        SUBMIT_FLAG=""
    else
        SUBMIT_FLAG="--no-submit"
    fi
    
    # Dry run
    read -p "Dry run mode? [y/N]: " DRY_RUN
    DRY_RUN=${DRY_RUN:-N}
    if [[ $DRY_RUN =~ ^[Yy]$ ]]; then
        DRY_RUN_FLAG="--dry-run"
    else
        DRY_RUN_FLAG=""
    fi
    
    # Add job
    echo ""
    echo -e "${YELLOW}Adding job...${NC}"
    cd "$PROJECT_DIR"
    python3 scripts/queue_manager_cli.py add-job \
        --type "$JOB_TYPE" \
        --strategy "$STRATEGY" \
        --count "$COUNT" \
        $SUBMIT_FLAG \
        $DRY_RUN_FLAG
    
    echo -e "\n${GREEN}✓ Job added to queue${NC}"
}

# Function to show queue status
show_queue_status() {
    cd "$PROJECT_DIR"
    python3 scripts/queue_manager_cli.py status
}

# Main
case "$1" in
    start)
        start_worker
        ;;
    stop)
        stop_worker
        ;;
    restart)
        restart_worker
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    monitor)
        monitor_worker
        ;;
    add-job)
        add_job_interactive
        ;;
    queue-status)
        show_queue_status
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
