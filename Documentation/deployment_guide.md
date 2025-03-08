# Deployment Guide for Financial Data Fetchers

This document outlines the deployment strategies and configuration for the financial data fetchers that power the Stock Analytics Dashboard.

## Table of Contents

1. [Deployment Options](#deployment-options)
2. [System Requirements](#system-requirements)
3. [Environment Setup](#environment-setup)
4. [Deployment Methods](#deployment-methods)
   - [Systemd Service](#systemd-service)
   - [Docker Container](#docker-container)
   - [Cloud Functions](#cloud-functions)
5. [Monitoring and Logging](#monitoring-and-logging)
6. [Alerts and Notifications](#alerts-and-notifications)
7. [Scaling Considerations](#scaling-considerations)
8. [Troubleshooting](#troubleshooting)

## Deployment Options

There are several ways to deploy the financial data fetchers, each with its own advantages and trade-offs:

1. **Systemd Service (Linux)**: Best for dedicated servers or VPS instances. Provides robust process management with auto-restart capabilities.

2. **Docker Container**: Ideal for containerized environments or microservices architecture. Ensures consistency across different environments and simplifies dependency management.

3. **Cloud Functions/Serverless**: Good for cost optimization in low-volume environments. Eliminates the need to manage servers but introduces cold start latency.

4. **Scheduled Tasks (Cron/Windows Task Scheduler)**: Simple option for basic deployments. Lower overhead but less robust monitoring and recovery options.

## System Requirements

- Python 3.10+ (3.11 recommended)
- 1 GB RAM minimum (2 GB recommended)
- 10 GB storage for logs and data
- Network connectivity to Supabase and API providers
- Operating System: Linux (preferred), macOS, or Windows

## Environment Setup

### Required Environment Variables

Create a `.env` file in the project root with the following variables:

```
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# API Keys
API_KEY_UNUSUAL_WHALES=your_unusual_whales_api_key
API_KEY_ALPHA_VANTAGE=your_alpha_vantage_key

# Notification Settings
ADMIN_EMAIL=alerts@yourdomain.com
SENDGRID_API_KEY=your_sendgrid_key
```

### Python Dependencies

Install required Python packages:

```bash
pip install -r requirements.txt
```

The `requirements.txt` file should contain:

```
requests==2.31.0
python-dotenv==1.0.0
schedule==1.2.0
psycopg2-binary==2.9.6
supabase==1.0.3
sendgrid==6.10.0
```

## Deployment Methods

### Systemd Service

1. Create a systemd service file `/etc/systemd/system/financial-data-fetcher.service`:

```ini
[Unit]
Description=Financial Data Fetcher Service
After=network.target

[Service]
User=appuser
WorkingDirectory=/path/to/your/project
ExecStart=/usr/bin/python3 /path/to/your/project/python/scheduler.py
Restart=always
RestartSec=5
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=financial-data-fetcher
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=/path/to/your/project/.env

[Install]
WantedBy=multi-user.target
```

2. Enable and start the service:

```bash
sudo systemctl enable financial-data-fetcher
sudo systemctl start financial-data-fetcher
sudo systemctl status financial-data-fetcher
```

### Docker Container

1. Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY python/ ./python/
COPY .env .

CMD ["python", "python/scheduler.py"]
```

2. Build and run the Docker container:

```bash
docker build -t financial-data-fetcher .
docker run -d --name financial-data-fetcher financial-data-fetcher
```

For production, consider using Docker Compose with environment variables:

```yaml
version: '3'
services:
  financial-data-fetcher:
    build: .
    container_name: financial-data-fetcher
    restart: always
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
```

### Cloud Functions

For AWS Lambda:

1. Create a lambda function handler:

```python
import os
import importlib.util
import sys

# Import the scheduler module
spec = importlib.util.spec_from_file_location("scheduler", "/tmp/scheduler.py")
scheduler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scheduler)

def lambda_handler(event, context):
    fetcher_name = event.get('fetcher', 'all')
    
    if fetcher_name == 'all':
        return scheduler.run_all_once()
    else:
        return scheduler.run_fetcher(f"python/{fetcher_name}.py")
```

2. Set up an AWS CloudWatch Events rule to trigger the Lambda function on schedule.

For Google Cloud Functions:

```python
import os
from scheduler import run_all_once, run_fetcher

def fetch_financial_data(request):
    request_json = request.get_json(silent=True)
    fetcher_name = request_json.get('fetcher', 'all') if request_json else 'all'
    
    if fetcher_name == 'all':
        return run_all_once()
    else:
        return run_fetcher(f"python/{fetcher_name}.py")
```

Set up a Cloud Scheduler job to trigger the function at regular intervals.

## Monitoring and Logging

### Logging Configuration

The fetchers are already configured with built-in logging. By default, logs are written to `data_fetcher.log` in the project directory.

For production, consider:

1. Rotating logs to prevent disk space issues:
   - Install `logrotate` on Linux systems
   - Create a logrotate configuration file
   
2. Centralized logging with ELK Stack (Elasticsearch, Logstash, Kibana) or a service like Datadog or New Relic.

3. Adding structured logging with JSON formatting for better parsing.

### Health Checks

Implement a health check endpoint to monitor the status of the fetchers:

```python
from flask import Flask
import psutil
import os
import json

app = Flask(__name__)

@app.route('/health')
def health_check():
    # Check if the scheduler process is running
    scheduler_running = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if 'scheduler.py' in ' '.join(proc.info['cmdline']):
            scheduler_running = True
            break
    
    # Check the timestamp of the last log entry
    log_path = 'data_fetcher.log'
    log_updated_recently = False
    if os.path.exists(log_path):
        log_mtime = os.path.getmtime(log_path)
        if (time.time() - log_mtime) < 3600:  # Updated in the last hour
            log_updated_recently = True
    
    status = {
        'status': 'healthy' if scheduler_running and log_updated_recently else 'unhealthy',
        'scheduler_running': scheduler_running,
        'log_updated_recently': log_updated_recently,
        'timestamp': datetime.now().isoformat()
    }
    
    return json.dumps(status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

Run this as a separate service or include it in the main scheduler.

## Alerts and Notifications

The scheduler already includes a function to send error notifications via SendGrid. Additional alert channels to consider:

1. **Slack Notifications**:

```python
def send_slack_notification(message, webhook_url):
    data = {
        'text': message
    }
    try:
        response = requests.post(
            webhook_url,
            data=json.dumps(data),
            headers={'Content-Type': 'application/json'}
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending Slack notification: {e}")
        return False
```

2. **SMS Notifications with Twilio**:

```python
from twilio.rest import Client

def send_sms_notification(message, to_number):
    client = Client(os.environ['TWILIO_ACCOUNT_SID'], os.environ['TWILIO_AUTH_TOKEN'])
    try:
        message = client.messages.create(
            body=message,
            from_=os.environ['TWILIO_PHONE_NUMBER'],
            to=to_number
        )
        return True
    except Exception as e:
        print(f"Error sending SMS notification: {e}")
        return False
```

## Scaling Considerations

### Horizontal Scaling

For high-volume deployments, consider distributing fetchers across multiple instances:

1. **Shared Database Approach**:
   - Run different fetchers on different servers
   - All instances write to the same Supabase database
   - Use locking mechanisms to prevent duplicate processing

2. **Queue-Based Architecture**:
   - Implement a message queue (RabbitMQ, SQS)
   - Producer service schedules fetch jobs
   - Worker nodes process jobs from the queue

### API Rate Limit Management

The fetchers should implement backoff strategies to handle API rate limits:

```python
def fetch_with_backoff(url, headers, max_retries=5):
    retry_count = 0
    while retry_count < max_retries:
        try:
            response = requests.get(url, headers=headers)
            
            # Check for rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited. Waiting {retry_after} seconds")
                time.sleep(retry_after)
                retry_count += 1
                continue
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            
            # Exponential backoff
            sleep_time = 2 ** retry_count
            logger.info(f"Retrying in {sleep_time} seconds")
            time.sleep(sleep_time)
            retry_count += 1
    
    raise Exception(f"Failed after {max_retries} retries")
```

## Troubleshooting

### Common Issues and Solutions

1. **API Connection Failures**:
   - Check API key validity
   - Verify network connectivity
   - Inspect API rate limits and quotas

2. **Database Connection Issues**:
   - Verify Supabase credentials
   - Check IP allowlisting for Supabase
   - Test connection with a simple query

3. **Process Termination**:
   - Check system resources (memory, CPU)
   - Review logs for exceptions
   - Verify service configuration

### Diagnostic Commands

```bash
# Check if the scheduler process is running
ps aux | grep scheduler.py

# View the most recent log entries
tail -n 100 data_fetcher.log

# Check service status (if using systemd)
sudo systemctl status financial-data-fetcher

# Test database connectivity
python -c "from supabase import create_client; import os; client = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_ROLE_KEY']); print(client.table('analyst_ratings').select('id').limit(1).execute())"
```

### Restarting Services

```bash
# Systemd service
sudo systemctl restart financial-data-fetcher

# Docker container
docker restart financial-data-fetcher

# Manual restart
pkill -f scheduler.py
nohup python python/scheduler.py > scheduler.out 2>&1 &
```