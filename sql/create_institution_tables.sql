-- Drop existing tables if they exist
DROP TABLE IF EXISTS institutions;
DROP TABLE IF EXISTS institution_holdings;
DROP TABLE IF EXISTS institution_activity;

-- Create institutions table
CREATE TABLE institutions (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  name text NOT NULL,
  short_name text,
  cik text,
  date date,
  filing_date date,
  is_hedge_fund boolean,
  description text,
  website text,
  logo_url text,
  founder_img_url text,
  people jsonb,
  tags text[],
  buy_value numeric,
  sell_value numeric,
  share_value numeric,
  put_value numeric,
  call_value numeric,
  warrant_value numeric,
  fund_value numeric,
  pfd_value numeric,
  debt_value numeric,
  total_value numeric,
  share_holdings numeric,
  put_holdings numeric,
  call_holdings numeric,
  warrant_holdings numeric,
  fund_holdings numeric,
  pfd_holdings numeric,
  debt_holdings numeric,
  total_holdings numeric,
  timestamp timestamp with time zone,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

-- Create institution_holdings table
CREATE TABLE institution_holdings (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  institution_name text NOT NULL,
  ticker text NOT NULL,
  date date,
  full_name text,
  security_type text,
  put_call text,
  units numeric,
  units_change numeric,
  value numeric,
  avg_price numeric,
  close numeric,
  first_buy date,
  price_first_buy numeric,
  sector text,
  shares_outstanding numeric,
  historical_units jsonb,
  timestamp timestamp with time zone,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

-- Create institution_activity table
CREATE TABLE institution_activity (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  institution_name text NOT NULL,
  ticker text NOT NULL,
  filing_date date,
  report_date date,
  security_type text,
  put_call text,
  units numeric,
  units_change numeric,
  avg_price numeric,
  buy_price numeric,
  sell_price numeric,
  close numeric,
  price_on_filing numeric,
  price_on_report numeric,
  shares_outstanding numeric,
  timestamp timestamp with time zone,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

-- Create hedge_fund_trades table (derived from activity)
CREATE TABLE hedge_fund_trades (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  institution_name text NOT NULL,
  ticker text NOT NULL,
  report_date date,
  filing_date date,
  action text,  -- 'BUY', 'SELL', etc.
  units numeric,
  price numeric,
  value numeric,
  change_percent numeric,
  security_type text,
  put_call text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_institutions_name ON institutions (name);
CREATE INDEX IF NOT EXISTS idx_institution_holdings_institution ON institution_holdings (institution_name);
CREATE INDEX IF NOT EXISTS idx_institution_holdings_ticker ON institution_holdings (ticker);
CREATE INDEX IF NOT EXISTS idx_institution_holdings_date ON institution_holdings (date);
CREATE INDEX IF NOT EXISTS idx_institution_activity_institution ON institution_activity (institution_name);
CREATE INDEX IF NOT EXISTS idx_institution_activity_ticker ON institution_activity (ticker);
CREATE INDEX IF NOT EXISTS idx_institution_activity_date ON institution_activity (report_date);
CREATE INDEX IF NOT EXISTS idx_hedge_fund_trades_institution ON hedge_fund_trades (institution_name);
CREATE INDEX IF NOT EXISTS idx_hedge_fund_trades_ticker ON hedge_fund_trades (ticker);
CREATE INDEX IF NOT EXISTS idx_hedge_fund_trades_date ON hedge_fund_trades (report_date);
CREATE INDEX IF NOT EXISTS idx_hedge_fund_trades_action ON hedge_fund_trades (action);

-- Enable Row Level Security for all tables
ALTER TABLE institutions ENABLE ROW LEVEL SECURITY;
ALTER TABLE institution_holdings ENABLE ROW LEVEL SECURITY;
ALTER TABLE institution_activity ENABLE ROW LEVEL SECURITY;
ALTER TABLE hedge_fund_trades ENABLE ROW LEVEL SECURITY;

-- Create select policies (read access for all)
CREATE POLICY institutions_select_policy ON institutions FOR SELECT USING (true);
CREATE POLICY institution_holdings_select_policy ON institution_holdings FOR SELECT USING (true);
CREATE POLICY institution_activity_select_policy ON institution_activity FOR SELECT USING (true);
CREATE POLICY hedge_fund_trades_select_policy ON hedge_fund_trades FOR SELECT USING (true);

-- Create insert policies (authenticated users and service role only)
CREATE POLICY institutions_insert_policy ON institutions
    FOR INSERT WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');
CREATE POLICY institution_holdings_insert_policy ON institution_holdings
    FOR INSERT WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');
CREATE POLICY institution_activity_insert_policy ON institution_activity
    FOR INSERT WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');
CREATE POLICY hedge_fund_trades_insert_policy ON hedge_fund_trades
    FOR INSERT WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');
    
-- Create update policies (authenticated users and service role only)
CREATE POLICY institutions_update_policy ON institutions
    FOR UPDATE USING (auth.role() = 'authenticated' OR auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');
CREATE POLICY institution_holdings_update_policy ON institution_holdings
    FOR UPDATE USING (auth.role() = 'authenticated' OR auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');
CREATE POLICY institution_activity_update_policy ON institution_activity
    FOR UPDATE USING (auth.role() = 'authenticated' OR auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');
CREATE POLICY hedge_fund_trades_update_policy ON hedge_fund_trades
    FOR UPDATE USING (auth.role() = 'authenticated' OR auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');

-- Set up trigger to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for each table
CREATE TRIGGER update_institutions_updated_at
BEFORE UPDATE ON institutions
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_institution_holdings_updated_at
BEFORE UPDATE ON institution_holdings
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_institution_activity_updated_at
BEFORE UPDATE ON institution_activity
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_hedge_fund_trades_updated_at
BEFORE UPDATE ON hedge_fund_trades
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column(); 