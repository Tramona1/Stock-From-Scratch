# Data Fetcher Scheduler

This scheduler manages the execution of all data fetching scripts while respecting API rate limits. It prioritizes critical data fetching during market hours and efficiently manages API usage to prevent rate limiting.

## Features

- **Intelligent Scheduling**: Runs scripts at appropriate intervals (5 min, 15 min, hourly, daily, weekly)
- **API Rate Limiting**: Tracks and respects API usage limits for Alpha Vantage (75 req/min) and Unusual Whales (120 req/min)
- **Priority-Based Execution**: Critical data is fetched first when API capacity is limited
- **Market Hours Awareness**: Recognizes market trading hours, weekends, and holidays
- **Comprehensive Logging**: Detailed logs with emoji markers for easy scanning
- **Error Handling**: Robust error tracking with dedicated error logs for each failed script

## Configuration

The scheduler has several configuration parameters in the code:

- **API Rate Limits**:
  - `ALPHA_VANTAGE_RATE_LIMIT`: 75 requests per minute (premium tier, 5 for free tier)
  - `UNUSUAL_WHALES_RATE_LIMIT`: 120 requests per minute

- **Script API Mapping**:
  - Defines which API each script uses (Alpha Vantage, Unusual Whales, or other)

- **Script Priority Levels**:
  - Priority 1 (highest): Critical real-time data (stock prices, options flow)
  - Priority 2: Important data (technical indicators, forex, commodities)
  - Priority 3: Regular updates (market news, analyst ratings)
  - Priority 4: Background data (political trades, economic reports)
  - Priority 5 (lowest): Infrequent updates (company metadata)

- **Scheduled Intervals**:
  - 5 minutes: Real-time data (stock prices, technical indicators, crypto)
  - 15 minutes: Medium-frequency data (options flow, forex, commodities)
  - 60 minutes: Hourly data (dark pool data, market news)
  - Daily: Low-frequency data (analyst ratings, insider trades, economic data)
  - Weekly: Infrequent data (hedge fund data)

## Usage

### Using the Shell Script

For ease of use, a shell script is provided to manage the scheduler as a background process:

```bash
# Start the scheduler as a background process
./python/run_scheduler.sh start

# Check the scheduler status
./python/run_scheduler.sh status

# View the scheduler logs
./python/run_scheduler.sh logs

# Stop the scheduler
./python/run_scheduler.sh stop

# Restart the scheduler
./python/run_scheduler.sh restart
```

### Using Python Directly

You can also run the scheduler directly using Python:

```bash
# Run with default settings (5-minute interval)
python3 python/scheduler.py

# Run with custom interval (e.g., 3 minutes)
python3 python/scheduler.py --interval 3

# Run in dry-run mode (logs what would run but doesn't execute scripts)
python3 python/scheduler.py --dry-run

# Run a specific script immediately
python3 python/scheduler.py --run-now fetch_stock_info.py
```

## Logging

The scheduler produces several log files:

- `logs/scheduler.log`: Main log file with all events
- `logs/scheduler_failures.log`: Dedicated log for script failures
- `logs/script_errors/`: Directory containing detailed error logs for each failed script
- `logs/scheduler_output.log`: Output log when running as a background process

## Market Hours Detection

The scheduler is aware of US market trading hours (9:30 AM - 4:00 PM ET) and will skip market-hours-only scripts outside these times. It also detects:

- Weekends (Saturday and Sunday)
- US market holidays (configured for 2025)
- Pre-market and after-hours periods

## Modifying Scripts Schedule

To change when scripts run:

1. Modify the `get_scripts_for_interval()` function to adjust which scripts run at each interval
2. Update `MARKET_HOURS_ONLY_SCRIPTS` to control which scripts only run during market hours
3. For special schedules (like company metadata on Mondays/Thursdays), adjust the logic in `run_scheduler()`

## Troubleshooting

If scripts are failing:

1. Check `logs/scheduler_failures.log` for detailed error information
2. Look in `logs/script_errors/` for full error output from specific scripts
3. Use `python3 python/scheduler.py --run-now failing_script.py` to test a specific script
4. Verify API keys are properly set in the .env file
5. Check if you're hitting API rate limits (the logs will show current usage) 