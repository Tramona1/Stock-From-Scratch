#!/bin/bash
# Script to run the data fetcher scheduler as a background process

# Create logs directory if it doesn't exist
mkdir -p logs

# Define log file
LOG_FILE="logs/scheduler_output.log"

# Function to start the scheduler
start_scheduler() {
    echo "Starting scheduler at $(date)"
    
    # Check if scheduler is already running
    if pgrep -f "python3 python/scheduler.py" > /dev/null; then
        echo "Error: Scheduler already running."
        exit 1
    fi
    
    # Run the scheduler with nohup
    nohup python3 python/scheduler.py --interval 5 > "$LOG_FILE" 2>&1 &
    
    # Get the PID
    PID=$!
    echo "Scheduler started with PID: $PID"
    echo "$PID" > logs/scheduler.pid
}

# Function to stop the scheduler
stop_scheduler() {
    echo "Stopping scheduler at $(date)"
    
    # Check if PID file exists
    if [ -f logs/scheduler.pid ]; then
        PID=$(cat logs/scheduler.pid)
        
        # Check if process is running
        if ps -p $PID > /dev/null; then
            echo "Stopping scheduler process (PID: $PID)"
            kill $PID
            rm logs/scheduler.pid
        else
            echo "Scheduler process not running (PID: $PID)"
            rm logs/scheduler.pid
        fi
    else
        # Try to find and kill all scheduler processes
        PIDS=$(pgrep -f "python3 python/scheduler.py")
        if [ -n "$PIDS" ]; then
            echo "Stopping scheduler processes: $PIDS"
            kill $PIDS
        else
            echo "No scheduler processes found"
        fi
    fi
}

# Function to check scheduler status
status_scheduler() {
    if [ -f logs/scheduler.pid ]; then
        PID=$(cat logs/scheduler.pid)
        if ps -p $PID > /dev/null; then
            echo "Scheduler is running with PID: $PID"
            
            # Show the last few lines of the log
            echo "--- Last 20 lines of log ---"
            tail -n 20 "$LOG_FILE"
        else
            echo "Scheduler is not running (stale PID file found)"
        fi
    else
        echo "Scheduler is not running (no PID file found)"
    fi
}

# Function to view logs
view_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo "--- Last 50 lines of log ---"
        tail -n 50 "$LOG_FILE"
    else
        echo "No log file found at $LOG_FILE"
    fi
}

# Show usage if no arguments provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 {start|stop|restart|status|logs}"
    exit 1
fi

# Process arguments
case "$1" in
    start)
        start_scheduler
        ;;
    stop)
        stop_scheduler
        ;;
    restart)
        stop_scheduler
        sleep 2
        start_scheduler
        ;;
    status)
        status_scheduler
        ;;
    logs)
        view_logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac

exit 0 