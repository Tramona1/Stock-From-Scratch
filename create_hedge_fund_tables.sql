-- Drop existing tables if they exist
DROP TABLE IF EXISTS institutions;
DROP TABLE IF EXISTS institution_holdings;
DROP TABLE IF EXISTS institution_activity;
DROP TABLE IF EXISTS hedge_fund_trades;

-- Create institutions table
CREATE TABLE institutions (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  name text NOT NULL UNIQUE,
  cik text,
  manager text,
  total_value numeric,
  total_securities integer,
  top_holdings jsonb,
  tags text[],
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

-- Create institution_holdings table
CREATE TABLE institution_holdings (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  institution_name text NOT NULL,
  ticker text NOT NULL,
  company_name text,
  cusip text,
  shares numeric,
  value numeric,
  weight numeric,
  report_date date,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  UNIQUE(institution_name, ticker, report_date)
);

-- Create institution_activity table
CREATE TABLE institution_activity (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  institution_name text NOT NULL,
  ticker text NOT NULL,
  company_name text,
  cusip text,
  action text,
  shares_changed numeric,
  percent_changed numeric,
  current_shares numeric,
  current_value numeric,
  report_date date,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  UNIQUE(institution_name, ticker, report_date)
);

-- Create hedge_fund_trades table
CREATE TABLE hedge_fund_trades (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  institution_name text NOT NULL,
  ticker text NOT NULL,
  company_name text,
  action text NOT NULL,
  shares numeric,
  value numeric,
  report_date date,
  source text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

-- Create indexes for faster lookups
CREATE INDEX idx_institutions_name ON institutions (name);
CREATE INDEX idx_institution_holdings_institution ON institution_holdings (institution_name);
CREATE INDEX idx_institution_holdings_ticker ON institution_holdings (ticker);
CREATE INDEX idx_institution_holdings_date ON institution_holdings (report_date);
CREATE INDEX idx_institution_activity_institution ON institution_activity (institution_name);
CREATE INDEX idx_institution_activity_ticker ON institution_activity (ticker);
CREATE INDEX idx_institution_activity_date ON institution_activity (report_date);
CREATE INDEX idx_hedge_fund_trades_institution ON hedge_fund_trades (institution_name);
CREATE INDEX idx_hedge_fund_trades_ticker ON hedge_fund_trades (ticker);
CREATE INDEX idx_hedge_fund_trades_date ON hedge_fund_trades (report_date);
CREATE INDEX idx_hedge_fund_trades_action ON hedge_fund_trades (action);

-- Enable row level security
ALTER TABLE institutions ENABLE ROW LEVEL SECURITY;
ALTER TABLE institution_holdings ENABLE ROW LEVEL SECURITY;
ALTER TABLE institution_activity ENABLE ROW LEVEL SECURITY;
ALTER TABLE hedge_fund_trades ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to read data
CREATE POLICY "Allow authenticated users to read institutions"
ON institutions FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow authenticated users to read institution_holdings"
ON institution_holdings FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow authenticated users to read institution_activity"
ON institution_activity FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow authenticated users to read hedge_fund_trades"
ON hedge_fund_trades FOR SELECT TO authenticated USING (true);

-- Allow service role to insert and update data
CREATE POLICY "Allow service role to insert institutions"
ON institutions FOR INSERT TO service_role WITH CHECK (true);

CREATE POLICY "Allow service role to update institutions"
ON institutions FOR UPDATE TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Allow service role to insert institution_holdings"
ON institution_holdings FOR INSERT TO service_role WITH CHECK (true);

CREATE POLICY "Allow service role to update institution_holdings"
ON institution_holdings FOR UPDATE TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Allow service role to insert institution_activity"
ON institution_activity FOR INSERT TO service_role WITH CHECK (true);

CREATE POLICY "Allow service role to update institution_activity"
ON institution_activity FOR UPDATE TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Allow service role to insert hedge_fund_trades"
ON hedge_fund_trades FOR INSERT TO service_role WITH CHECK (true);

CREATE POLICY "Allow service role to update hedge_fund_trades"
ON hedge_fund_trades FOR UPDATE TO service_role USING (true) WITH CHECK (true); 