-- Drop existing tables if they exist
DROP TABLE IF EXISTS economic_indicators;
DROP TABLE IF EXISTS economic_news;
DROP TABLE IF EXISTS fred_observations;
DROP TABLE IF EXISTS fred_metadata;
DROP TABLE IF EXISTS fred_user_series;
DROP TABLE IF EXISTS fred_economic_events;

-- Create economic_indicators table
CREATE TABLE economic_indicators (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  indicator_name text NOT NULL,
  indicator_value numeric,
  previous_value numeric,
  change_value numeric,
  change_percent numeric,
  date date,
  source text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

-- Create economic_news table
CREATE TABLE economic_news (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  title text NOT NULL,
  content text,
  source text,
  url text,
  published_date timestamp with time zone,
  sentiment numeric,
  relevance numeric,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

-- Create fred_observations table
CREATE TABLE fred_observations (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  series_id text NOT NULL,
  date date NOT NULL,
  value numeric,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  UNIQUE(series_id, date)
);

-- Create fred_metadata table
CREATE TABLE fred_metadata (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  series_id text NOT NULL UNIQUE,
  title text,
  description text,
  frequency text,
  units text,
  seasonal_adjustment text,
  last_updated timestamp with time zone,
  last_fetch_time timestamp with time zone,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

-- Create fred_user_series table
CREATE TABLE fred_user_series (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES auth.users(id),
  series_id text NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  UNIQUE(user_id, series_id)
);

-- Create fred_economic_events table
CREATE TABLE fred_economic_events (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  series_id text,
  title text NOT NULL,
  event_type text,
  content text,
  event_date timestamp with time zone DEFAULT now(),
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

-- Create indexes for faster lookups
CREATE INDEX idx_economic_indicators_name ON economic_indicators (indicator_name);
CREATE INDEX idx_economic_indicators_date ON economic_indicators (date);
CREATE INDEX idx_economic_news_date ON economic_news (published_date);
CREATE INDEX idx_fred_observations_series ON fred_observations (series_id);
CREATE INDEX idx_fred_observations_date ON fred_observations (date);
CREATE INDEX idx_fred_metadata_series ON fred_metadata (series_id);
CREATE INDEX idx_fred_user_series_user ON fred_user_series (user_id);
CREATE INDEX idx_fred_user_series_series ON fred_user_series (series_id);
CREATE INDEX idx_fred_economic_events_series ON fred_economic_events (series_id);
CREATE INDEX idx_fred_economic_events_date ON fred_economic_events (event_date);

-- Enable row level security
ALTER TABLE economic_indicators ENABLE ROW LEVEL SECURITY;
ALTER TABLE economic_news ENABLE ROW LEVEL SECURITY;
ALTER TABLE fred_observations ENABLE ROW LEVEL SECURITY;
ALTER TABLE fred_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE fred_user_series ENABLE ROW LEVEL SECURITY;
ALTER TABLE fred_economic_events ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to read data
CREATE POLICY "Allow authenticated users to read economic_indicators"
ON economic_indicators FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow authenticated users to read economic_news"
ON economic_news FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow authenticated users to read fred_observations"
ON fred_observations FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow authenticated users to read fred_metadata"
ON fred_metadata FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow authenticated users to read fred_user_series"
ON fred_user_series FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow authenticated users to read fred_economic_events"
ON fred_economic_events FOR SELECT TO authenticated USING (true);

-- Allow service role to insert and update data
CREATE POLICY "Allow service role to insert economic_indicators"
ON economic_indicators FOR INSERT TO service_role WITH CHECK (true);

CREATE POLICY "Allow service role to update economic_indicators"
ON economic_indicators FOR UPDATE TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Allow service role to insert economic_news"
ON economic_news FOR INSERT TO service_role WITH CHECK (true);

CREATE POLICY "Allow service role to update economic_news"
ON economic_news FOR UPDATE TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Allow service role to insert fred_observations"
ON fred_observations FOR INSERT TO service_role WITH CHECK (true);

CREATE POLICY "Allow service role to update fred_observations"
ON fred_observations FOR UPDATE TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Allow service role to insert fred_metadata"
ON fred_metadata FOR INSERT TO service_role WITH CHECK (true);

CREATE POLICY "Allow service role to update fred_metadata"
ON fred_metadata FOR UPDATE TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Allow service role to insert fred_user_series"
ON fred_user_series FOR INSERT TO service_role WITH CHECK (true);

CREATE POLICY "Allow service role to update fred_user_series"
ON fred_user_series FOR UPDATE TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Allow service role to insert fred_economic_events"
ON fred_economic_events FOR INSERT TO service_role WITH CHECK (true);

CREATE POLICY "Allow service role to update fred_economic_events"
ON fred_economic_events FOR UPDATE TO service_role USING (true) WITH CHECK (true);

-- Allow users to manage their own series
CREATE POLICY "Allow users to manage their own series"
ON fred_user_series FOR ALL TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id); 