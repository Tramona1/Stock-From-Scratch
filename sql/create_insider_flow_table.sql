-- Create insider_flow table
CREATE TABLE IF NOT EXISTS insider_flow (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticker TEXT NOT NULL,
    date DATE NOT NULL,
    transactions INTEGER NOT NULL,
    volume BIGINT NOT NULL,
    buy_sell TEXT NOT NULL,
    avg_price NUMERIC(15, 2),
    premium NUMERIC(15, 2),
    unique_insiders INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_insider_flow_ticker ON insider_flow (ticker);
CREATE INDEX IF NOT EXISTS idx_insider_flow_date ON insider_flow (date);
CREATE INDEX IF NOT EXISTS idx_insider_flow_buy_sell ON insider_flow (buy_sell);

-- Enable Row Level Security
ALTER TABLE insider_flow ENABLE ROW LEVEL SECURITY;

-- Create policies for access control
CREATE POLICY insider_flow_select_policy ON insider_flow
    FOR SELECT USING (true);

CREATE POLICY insider_flow_insert_policy ON insider_flow
    FOR INSERT WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');
    
CREATE POLICY insider_flow_update_policy ON insider_flow
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

CREATE TRIGGER update_insider_flow_updated_at
BEFORE UPDATE ON insider_flow
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column(); 