-- Schema for stock_details table to store comprehensive stock information from Unusual Whales API

-- Drop table if it exists
DROP TABLE IF EXISTS stock_details;

-- Create the stock_details table
CREATE TABLE stock_details (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticker TEXT NOT NULL UNIQUE,
    company_name TEXT,
    short_name TEXT,
    sector TEXT,
    market_cap NUMERIC(20, 2),
    market_cap_size TEXT,
    avg_volume NUMERIC(20, 2),
    description TEXT,
    logo_url TEXT,
    issue_type TEXT,
    has_dividend BOOLEAN DEFAULT FALSE,
    has_earnings_history BOOLEAN DEFAULT FALSE,
    has_investment_arm BOOLEAN DEFAULT FALSE,
    has_options BOOLEAN DEFAULT FALSE,
    next_earnings_date DATE,
    earnings_announce_time TEXT,
    tags JSONB DEFAULT '[]'::jsonb,
    fetched_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX stock_details_ticker_idx ON stock_details (ticker);
CREATE INDEX stock_details_sector_idx ON stock_details (sector);
CREATE INDEX stock_details_market_cap_size_idx ON stock_details (market_cap_size);
CREATE INDEX stock_details_issue_type_idx ON stock_details (issue_type);
CREATE INDEX stock_details_next_earnings_date_idx ON stock_details (next_earnings_date);

-- Add a trigger for updated_at
CREATE OR REPLACE FUNCTION update_stock_details_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_stock_details_updated_at_trigger
BEFORE UPDATE ON stock_details
FOR EACH ROW
EXECUTE FUNCTION update_stock_details_updated_at();

-- Add a comment to the table
COMMENT ON TABLE stock_details IS 'Comprehensive stock information from Unusual Whales API'; 