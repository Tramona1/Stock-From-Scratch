# Stock Analytics Dashboard

A modern financial data platform that combines real-time market data, AI-powered insights, and personalized watchlists in a user-friendly interface.

![Stock Analytics Dashboard](https://example.com/dashboard-screenshot.png)

## Overview

The Stock Analytics Dashboard integrates multiple financial data sources to provide users with personalized insights about stocks they're interested in. The platform features a sophisticated data pipeline, intuitive UI, and AI-powered query capabilities.

### Key Features

- **Personalized Watchlist**: Track specific stocks you're interested in
- **Financial Data Integration**: View analyst ratings, insider trades, options activity, and more
- **AI-Powered Insights**: Ask natural language questions about your watchlist stocks
- **Clean, Modern UI**: Intuitive interface built with Next.js and Tailwind CSS
- **Real-time Updates**: Fresh data pulled from multiple financial APIs

## Architecture

The system consists of three main components:

1. **Next.js Frontend**: React-based user interface
2. **Python Data Fetchers**: Services that collect and process financial data
3. **Supabase Database**: Centralized storage for all financial information

These components work together to provide a seamless user experience with personalized financial data.

## Database Structure

The Supabase database includes the following key tables:

- **users**: Stores user information and subscription details
- **watchlists**: Tracks which stocks each user is following
- **insider_trades**: Contains insider trading activity data
- **analyst_ratings**: Stores analyst recommendations and price targets
- **options_flow**: Records options activity and sentiment
- **dark_pool_data**: Tracks dark pool trading activity
- **stock_info**: Contains basic information about stocks
- **market_indicators**: Stores various market metrics and indicators
- **alerts**: Manages user-specific notifications

Each table is properly indexed and configured with row-level security to ensure data integrity and access control.

## Data Pipeline

The data pipeline automatically keeps the database up-to-date through:

- **Scheduled Updates**: Different data types update at varying frequencies based on volatility
- **Watchlist Optimization**: Prioritizes data collection for stocks users are watching
- **Incremental Updates**: Only fetches new data to respect API limits
- **Error Handling**: Includes retry logic and failure notifications
- **Health Monitoring**: Provides visibility into system status

For more details, see [Data Pipeline Documentation](Documentation/data_pipeline.md).

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.10+
- Docker & Docker Compose (for production deployment)
- Supabase account
- Clerk account (for authentication)
- API keys for financial data sources

### Environment Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/stock-analytics-dashboard.git
   cd stock-analytics-dashboard
   ```

2. Create `.env` file from the template:
   ```bash
   cp .env.example .env
   ```

3. Fill in the environment variables in the `.env` file.

### Development Setup

#### Frontend (Next.js)

1. Install dependencies:
   ```bash
   npm install
   ```

2. Run the development server:
   ```bash
   npm run dev
   ```

3. Open [http://localhost:3000](http://localhost:3000) to view the app.

#### Backend (Python)

1. Set up a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the data fetchers:
   ```bash
   python python/scheduler.py --once
   ```

### Supabase Setup

1. Create required tables in Supabase using the SQL scripts provided in the `sql/` directory
2. Enable relevant PostgreSQL extensions (uuid-ossp, etc.)
3. Verify Row-Level Security policies are properly configured

### Production Deployment

For production deployment, use Docker Compose:

```bash
docker-compose up -d
```

This will start all services, including:
- Next.js frontend app
- Python data fetcher services
- Health check API
- Nginx reverse proxy

## Documentation

For more detailed information, see the following documentation:

- [Data Integration Architecture](Documentation/data_integration_architecture.md)
- [Integration Guide](Documentation/integration_guide.md)
- [Data Pipeline Documentation](Documentation/data_pipeline.md)
- [Project Summary](Documentation/project_summary.md)
- [Launch Checklist](Documentation/launch_checklist.md)
- [Next Steps Implementation](Documentation/next_steps_implementation.md)

## Project Structure

```
/
├── src/                   # Next.js application source
│   ├── app/               # Next.js app router
│   ├── components/        # React components
│   ├── context/           # React context providers
│   ├── lib/               # Utility functions and libraries
│   ├── services/          # Service layer for API interactions
│   └── types/             # TypeScript type definitions
├── python/                # Python data fetcher scripts
│   ├── fetch_*.py         # Individual data fetchers
│   ├── scheduler.py       # Scheduler for running fetchers
│   └── health_api.py      # Health monitoring API
├── Documentation/         # Project documentation
├── sql/                   # SQL scripts for database setup
├── docker-compose.yml     # Docker Compose configuration
├── Dockerfile.nextjs      # Next.js application Dockerfile
├── Dockerfile.python      # Python services Dockerfile
└── Dockerfile.health      # Health API Dockerfile
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Next.js](https://nextjs.org/) for the frontend framework
- [Supabase](https://supabase.io/) for the database
- [Clerk](https://clerk.dev/) for authentication
- [Tailwind CSS](https://tailwindcss.com/) for styling
- [Unusual Whales](https://unusualwhales.com/) for financial data
- [Google Gemini](https://ai.google.dev/) for AI capabilities 