-- Update stock_info table to add columns for Alpha Vantage data
ALTER TABLE IF EXISTS stock_info
ADD COLUMN IF NOT EXISTS open_price FLOAT,
ADD COLUMN IF NOT EXISTS daily_high FLOAT,
ADD COLUMN IF NOT EXISTS daily_low FLOAT,
ADD COLUMN IF NOT EXISTS daily_volume BIGINT,
ADD COLUMN IF NOT EXISTS fifty_two_week_high FLOAT,
ADD COLUMN IF NOT EXISTS fifty_two_week_low FLOAT,
ADD COLUMN IF NOT EXISTS pe_ratio FLOAT,
ADD COLUMN IF NOT EXISTS eps FLOAT; 