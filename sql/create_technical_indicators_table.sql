-- Create technical indicators table
CREATE TABLE IF NOT EXISTS technical_indicators (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    interval TEXT NOT NULL DEFAULT 'daily',
    date TEXT,
    macd FLOAT,
    macd_signal FLOAT,
    macd_hist FLOAT,
    rsi FLOAT,
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(symbol, interval, date)
);

-- Create index on symbol for faster lookups
CREATE INDEX IF NOT EXISTS technical_indicators_symbol_idx ON technical_indicators (symbol);

-- Create index on date for faster lookups
CREATE INDEX IF NOT EXISTS technical_indicators_date_idx ON technical_indicators (date);

-- Create index on interval for faster lookups
CREATE INDEX IF NOT EXISTS technical_indicators_interval_idx ON technical_indicators (interval); 