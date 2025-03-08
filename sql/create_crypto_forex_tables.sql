-- Create cryptocurrency table
CREATE TABLE IF NOT EXISTS crypto_info (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    market TEXT NOT NULL DEFAULT 'USD',
    name TEXT,
    current_price FLOAT,
    bid_price FLOAT,
    ask_price FLOAT,
    open_price FLOAT,
    daily_high FLOAT,
    daily_low FLOAT,
    daily_volume FLOAT,
    market_cap FLOAT,
    price_change_24h FLOAT,
    price_change_percentage_24h FLOAT,
    market_cap_rank INTEGER,
    price_updated_at TIMESTAMP WITH TIME ZONE,
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(symbol, market)
);

-- Create index on symbol for faster lookups
CREATE INDEX IF NOT EXISTS crypto_info_symbol_idx ON crypto_info (symbol);

-- Create forex (FX) rates table
CREATE TABLE IF NOT EXISTS forex_info (
    id SERIAL PRIMARY KEY,
    from_currency TEXT NOT NULL,
    to_currency TEXT NOT NULL,
    currency_pair TEXT NOT NULL,
    exchange_rate FLOAT,
    bid_price FLOAT,
    ask_price FLOAT,
    open_price FLOAT,
    daily_high FLOAT,
    daily_low FLOAT,
    daily_close FLOAT,
    weekly_open FLOAT,
    weekly_high FLOAT,
    weekly_low FLOAT,
    weekly_close FLOAT,
    last_refreshed TEXT,
    price_updated_at TIMESTAMP WITH TIME ZONE,
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(from_currency, to_currency)
);

-- Create index on currency pair for faster lookups
CREATE INDEX IF NOT EXISTS forex_info_pair_idx ON forex_info (currency_pair);

-- Create commodities table
CREATE TABLE IF NOT EXISTS commodity_info (
    id SERIAL PRIMARY KEY,
    function TEXT NOT NULL,
    name TEXT NOT NULL,
    daily_value FLOAT,
    daily_date TEXT,
    weekly_value FLOAT,
    weekly_date TEXT,
    monthly_value FLOAT,
    monthly_date TEXT,
    unit TEXT,
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(function)
);

-- Create index on function for faster lookups
CREATE INDEX IF NOT EXISTS commodity_info_function_idx ON commodity_info (function); 