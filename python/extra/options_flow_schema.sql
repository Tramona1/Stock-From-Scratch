-- Drop existing tables if they exist (clean start)
DROP TABLE IF EXISTS options_flow CASCADE;
DROP TABLE IF EXISTS option_flow_data CASCADE;
DROP TABLE IF EXISTS alerts CASCADE;

-- Options Flow Table Schema
CREATE TABLE options_flow (
    id UUID PRIMARY KEY,
    ticker TEXT NOT NULL,
    date TIMESTAMPTZ,
    contract_id TEXT,
    strike_price DECIMAL,
    expiration_date DATE,
    option_type TEXT CHECK (option_type IN ('call', 'put')),
    sentiment TEXT CHECK (sentiment IN ('bullish', 'bearish', 'neutral')),
    volume INTEGER,
    open_interest INTEGER,
    implied_volatility DECIMAL,
    premium DECIMAL,
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for options_flow
CREATE INDEX options_flow_ticker_idx ON options_flow (ticker);
CREATE INDEX options_flow_date_idx ON options_flow (date);
CREATE INDEX options_flow_sentiment_idx ON options_flow (sentiment);
CREATE INDEX options_flow_contract_id_idx ON options_flow (contract_id);

-- Option Flow Data (Analysis) Table Schema
CREATE TABLE option_flow_data (
    id UUID PRIMARY KEY,
    ticker TEXT NOT NULL,
    analysis_date DATE NOT NULL,
    flow_count INTEGER DEFAULT 0,
    bullish_count INTEGER DEFAULT 0,
    bearish_count INTEGER DEFAULT 0,
    high_premium_count INTEGER DEFAULT 0,
    pre_earnings_count INTEGER DEFAULT 0,
    sentiment TEXT CHECK (sentiment IN ('bullish', 'bearish', 'neutral')),
    total_premium DECIMAL DEFAULT 0,
    bullish_premium DECIMAL DEFAULT 0,
    bearish_premium DECIMAL DEFAULT 0,
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (ticker, analysis_date)
);

-- Create indexes for option_flow_data
CREATE INDEX option_flow_data_ticker_idx ON option_flow_data (ticker);
CREATE INDEX option_flow_data_analysis_date_idx ON option_flow_data (analysis_date);
CREATE INDEX option_flow_data_sentiment_idx ON option_flow_data (sentiment);

-- Alerts Table Schema
CREATE TABLE alerts (
    id UUID PRIMARY KEY,
    related_ticker TEXT,
    alert_type TEXT,
    message TEXT,
    source TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_read BOOLEAN DEFAULT FALSE,
    priority TEXT CHECK (priority IN ('low', 'medium', 'high')),
    expires_at TIMESTAMPTZ  -- Changed from 'expiry' to 'expires_at' for clarity
);

-- Create indexes for alerts
CREATE INDEX alerts_related_ticker_idx ON alerts (related_ticker);
CREATE INDEX alerts_is_read_idx ON alerts (is_read);
CREATE INDEX alerts_created_at_idx ON alerts (created_at);
CREATE INDEX alerts_expires_at_idx ON alerts (expires_at);  -- Changed from 'expiry' to 'expires_at' 