"""
Health Check API for Financial Data Fetchers
-------------------------------------------
This service provides endpoints to monitor the health and status of the
financial data fetchers.
"""

import os
import json
import time
import psutil
import logging
from datetime import datetime
import requests
from flask import Flask, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("health_api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("health_api")

app = Flask(__name__)

# Get Supabase connection information
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Supabase credentials not found in environment variables")


@app.route('/health')
def health():
    """Main health check endpoint"""
    
    # Check if the scheduler process is running
    scheduler_running = is_scheduler_running()
    
    # Check the timestamp of the last log entry
    log_updated_recently = is_log_updated_recently()
    
    # Check connection to Supabase
    supabase_healthy = is_supabase_healthy()
    
    # Get recent fetch status
    fetchers_status = get_fetchers_status()
    
    # Overall status
    overall_status = "healthy" if scheduler_running and log_updated_recently and supabase_healthy else "unhealthy"
    
    status = {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "components": {
            "scheduler_running": scheduler_running,
            "log_updated_recently": log_updated_recently,
            "supabase_connection": supabase_healthy,
            "fetchers": fetchers_status
        }
    }
    
    return jsonify(status)


@app.route('/health/details')
def health_details():
    """Detailed health check with system metrics"""
    
    # Get basic health status
    basic_health = json.loads(health().get_data(as_text=True))
    
    # Add system metrics
    system_metrics = {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "uptime_seconds": time.time() - psutil.boot_time()
    }
    
    # Combine data
    detailed_status = {
        **basic_health,
        "system_metrics": system_metrics
    }
    
    return jsonify(detailed_status)


@app.route('/health/tables')
def table_health():
    """Check the health of database tables"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return jsonify({"status": "error", "message": "Supabase credentials not configured"})
    
    tables = [
        "analyst_ratings",
        "insider_trades",
        "options_flow",
        "economic_calendar_events",
        "fda_calendar_events",
        "political_trades",
        "dark_pool_data",
        "financial_news"
    ]
    
    table_status = {}
    
    for table in tables:
        try:
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/{table}?select=count&limit=0",
                headers={
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}"
                }
            )
            
            if response.status_code == 200:
                # Get the total count from the Content-Range header
                content_range = response.headers.get('Content-Range', '')
                count = 0
                if content_range:
                    try:
                        count = int(content_range.split('/')[1])
                    except (IndexError, ValueError):
                        count = -1
                
                table_status[table] = {
                    "status": "healthy",
                    "row_count": count,
                    "last_updated": get_last_updated_time(table)
                }
            else:
                table_status[table] = {
                    "status": "error",
                    "message": f"API Error: {response.status_code}",
                    "details": response.text
                }
        except Exception as e:
            table_status[table] = {
                "status": "error",
                "message": str(e)
            }
    
    return jsonify({"tables": table_status})


def is_scheduler_running():
    """Check if the scheduler process is running"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'scheduler.py' in cmdline:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False


def is_log_updated_recently(log_path='../logs/data_fetcher.log', max_age_seconds=3600):
    """Check if the log file has been updated recently"""
    try:
        if os.path.exists(log_path):
            log_mtime = os.path.getmtime(log_path)
            age_seconds = time.time() - log_mtime
            return age_seconds < max_age_seconds
        
        # Try alternate paths
        alt_paths = ['data_fetcher.log', '/app/logs/data_fetcher.log']
        for path in alt_paths:
            if os.path.exists(path):
                log_mtime = os.path.getmtime(path)
                age_seconds = time.time() - log_mtime
                return age_seconds < max_age_seconds
                
        logger.warning(f"Log file not found at {log_path} or alternate locations")
        return False
    except Exception as e:
        logger.error(f"Error checking log file: {e}")
        return False


def is_supabase_healthy():
    """Check if we can connect to Supabase"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return False
    
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/analyst_ratings?limit=1",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}"
            }
        )
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error connecting to Supabase: {e}")
        return False


def get_fetchers_status():
    """Get the status of individual fetchers"""
    fetchers = [
        "analyst_ratings",
        "insider_trades",
        "options_flow",
        "economic_calendar",
        "fda_calendar",
        "political_trades",
        "dark_pool",
        "financial_news"
    ]
    
    results = {}
    
    for fetcher in fetchers:
        # Get the last updated time from the database
        last_updated = get_last_updated_time(fetcher)
        
        # Determine status based on last update time
        status = "unknown"
        if last_updated:
            # Parse the ISO format date
            try:
                last_updated_time = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                age_hours = (datetime.now() - last_updated_time).total_seconds() / 3600
                
                if age_hours < 24:
                    status = "healthy"
                elif age_hours < 48:
                    status = "warning"
                else:
                    status = "critical"
            except Exception as e:
                logger.error(f"Error parsing date {last_updated}: {e}")
        
        results[fetcher] = {
            "status": status,
            "last_updated": last_updated
        }
    
    return results


def get_last_updated_time(table_name):
    """Get the timestamp of the most recent record in a table"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    
    # Map fetcher names to table names if needed
    table_mapping = {
        "analyst_ratings": "analyst_ratings",
        "insider_trades": "insider_trades",
        "options_flow": "options_flow",
        "economic_calendar": "economic_calendar_events",
        "fda_calendar": "fda_calendar_events",
        "political_trades": "political_trades",
        "dark_pool": "dark_pool_data",
        "financial_news": "financial_news"
    }
    
    actual_table = table_mapping.get(table_name, table_name)
    
    try:
        # Look for the most appropriate date field
        date_fields = ["last_updated", "updated_at", "created_at", "rating_date", "transaction_date", "date", "event_date", "end_date", "publish_date"]
        
        for date_field in date_fields:
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/{actual_table}?select={date_field}&order={date_field}.desc&limit=1",
                headers={
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0 and date_field in data[0]:
                    return data[0][date_field]
        
        return None
    except Exception as e:
        logger.error(f"Error getting last updated time for {table_name}: {e}")
        return None


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000) 