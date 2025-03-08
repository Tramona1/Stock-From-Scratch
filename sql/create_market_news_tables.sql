-- Create the market_news table
CREATE TABLE IF NOT EXISTS market_news (
    id SERIAL PRIMARY KEY,
    ticker_query TEXT NOT NULL,
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    items_count INTEGER,
    query_metadata JSONB
);

-- Create index on ticker_query for faster lookups
CREATE INDEX IF NOT EXISTS market_news_ticker_query_idx ON market_news (ticker_query);

-- Create the news_sentiment table with a foreign key reference
CREATE TABLE IF NOT EXISTS news_sentiment (
    id SERIAL PRIMARY KEY,
    news_id INTEGER REFERENCES market_news(id) ON DELETE CASCADE,
    title TEXT,
    url TEXT,
    time_published TEXT,
    authors JSONB,
    summary TEXT,
    source TEXT,
    category_within_source TEXT,
    source_domain TEXT,
    overall_sentiment_score FLOAT,
    overall_sentiment_label TEXT,
    ticker_sentiment JSONB
);

-- Create index on news_id for faster lookups
CREATE INDEX IF NOT EXISTS news_sentiment_news_id_idx ON news_sentiment (news_id); 