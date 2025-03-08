# Data Points Inventory

This document provides a comprehensive inventory of all data points being collected by the system's various fetchers and stored in the database.

## Basic Stock Information

### From Alpha Vantage API (`fetch_stock_info_alpha.py`)
- **Ticker Symbol**
- **Company Name**
- **Current Price**
- **Open Price**
- **Daily High**
- **Daily Low**
- **Daily Volume**
- **Previous Close**
- **Price Change**
- **Price Change Percentage**
- **52-Week High**
- **52-Week Low**
- **Market Cap**
- **PE Ratio**
- **Dividend Yield**
- **Last Updated Timestamp**

### From Unusual Whales API (`fetch_stock_info.py`, `fetch_stock_details.py`)
- **Ticker Symbol**
- **Company Name**
- **Short Name**
- **Sector**
- **Industry**
- **Exchange**
- **Market Cap**
- **Market Cap Size** (Small/Mid/Large)
- **Shares Outstanding**
- **Float**
- **Average Volume**
- **Beta**
- **Description** (Company profile text)
- **Logo URL**
- **Company Website**
- **Headquarters**
- **CEO Name**
- **Employee Count**
- **Founded Year**
- **Issue Type** (Common Stock, ETF, etc.)
- **Has Dividend** (Boolean)
- **Has Earnings History** (Boolean)
- **Has Investment Arm** (Boolean)
- **Has Options** (Boolean)
- **Next Earnings Date**
- **Earnings Announce Time** (Before/After Market)
- **Tags** (Array of company tags)

## Technical Indicators (`fetch_technical_indicators.py`)

- **Symbol**
- **Interval** (daily, weekly, monthly)
- **Date**
- **MACD** (Moving Average Convergence Divergence)
- **MACD Signal Line**
- **MACD Histogram**
- **RSI** (Relative Strength Index)
- **Moving Averages** (Simple and Exponential)
- **Bollinger Bands**
- **ADX** (Average Directional Index)
- **Stochastic Oscillator**
- **OBV** (On-Balance Volume)

## Options Data (`fetch_options_flow.py`)

### Options Flow
- **Ticker Symbol**
- **Contract ID**
- **Strike Price**
- **Expiration Date**
- **Option Type** (Call/Put)
- **Sentiment** (Bullish/Bearish/Neutral)
- **Volume**
- **Open Interest**
- **Implied Volatility**
- **Premium** (Dollar value)
- **Time of Trade**

### Options Flow Analysis
- **Ticker Symbol**
- **Analysis Date**
- **Flow Count** (Total number of trades)
- **Bullish Count**
- **Bearish Count**
- **High Premium Count**
- **Pre-Earnings Count**
- **Overall Sentiment**
- **Total Premium** (Sum of all premiums)
- **Bullish Premium** (Sum of bullish trade premiums)
- **Bearish Premium** (Sum of bearish trade premiums)

## Insider Trading (`insider_trades_fetcher.py`, `fetch_insider_trades.py`)

- **Ticker Symbol**
- **Insider Name**
- **Insider Position** (CEO, CFO, Director, etc.)
- **Transaction Date**
- **Filing Date**
- **Transaction Type** (Buy, Sell, etc.)
- **Price Per Share**
- **Shares Traded**
- **Value** (Total transaction value)
- **Shares Owned After Transaction**
- **Filing URL**
- **Sentiment** (Positive/Negative)

## Analyst Ratings (`fetch_analyst_ratings.py`)

- **Ticker Symbol**
- **Analyst Firm**
- **Analyst Name**
- **Rating** (Buy, Sell, Hold, etc.)
- **Previous Rating**
- **Price Target**
- **Previous Price Target**
- **Price Target Change** (Percentage)
- **Date**
- **Notes/Commentary**
- **Rating URL**

## Dark Pool Data (`fetch_dark_pool_data.py`)

- **Ticker Symbol**
- **Exchange**
- **Price**
- **Size** (Number of shares)
- **Total Value** (Price * Size)
- **Time of Trade**
- **Reference Number**
- **Trade Conditions**
- **Off-Exchange Volume Percentage**
- **Significance** (Standard/Significant/Notable)

## Crypto Information (`fetch_crypto_info.py`)

- **Symbol** (BTC, ETH, etc.)
- **Name** (Bitcoin, Ethereum, etc.)
- **Exchange Rate** (to USD)
- **Bid Price**
- **Ask Price**
- **24h Open**
- **24h High**
- **24h Low**
- **24h Close**
- **24h Volume**
- **Market Cap**
- **Last Updated Timestamp**

## Forex Information (`fetch_forex_info.py`)

- **From Currency**
- **To Currency**
- **Currency Pair** (e.g., EUR/USD)
- **Exchange Rate**
- **Bid Price**
- **Ask Price**
- **Open Price**
- **Daily High**
- **Daily Low**
- **Daily Close**
- **Weekly Open/High/Low/Close**
- **Last Refreshed Timestamp**

## Commodity Information (`fetch_commodity_info.py`)

- **Commodity Type** (WTI Crude, Brent Crude, Natural Gas, etc.)
- **Unit** (Barrel, MMBtu, etc.)
- **Daily Value**
- **Daily Date**
- **Weekly Value**
- **Weekly Date**
- **Monthly Value**
- **Monthly Date**

## Market News (`fetch_market_news.py`)

- **Title**
- **Summary**
- **URL**
- **Time Published**
- **Source** (Publisher name)
- **Authors**
- **Category**
- **Tickers** (Related stock symbols)
- **Sentiment** (Positive/Negative/Neutral)
- **Sentiment Score** (Numerical score)

## Political Trades (`fetch_political_trades.py`)

- **Politician Name**
- **Office/Position**
- **Transaction Date**
- **Filing Date**
- **Ticker Symbol**
- **Asset Name**
- **Asset Type**
- **Transaction Type** (Purchase, Sale)
- **Amount** (Value range or exact amount)
- **Owner** (Self, Spouse, Child, etc.)
- **Source URL**
- **Comments**

## Economic Data (`economic_indicators_fetcher.py`, `fetch_economic_reports.py`)

### Economic Reports
- **Title**
- **Release Date**
- **Release Time**
- **Source** (Federal Reserve, BLS, etc.)
- **Importance** (High/Medium/Low)
- **Previous Value**
- **Forecast Value**
- **Actual Value**
- **Impact** (Positive/Negative/Neutral)
- **Description**
- **URL**

### FRED Economic Data
- **Series ID**
- **Series Name**
- **Frequency** (Daily, Monthly, Quarterly, Annual)
- **Units**
- **Data Value**
- **Date**
- **Notes**
- **Source**

## FDA Calendar (`fetch_fda_calendar.py`)

- **Company Name**
- **Ticker Symbol**
- **Drug/Product Name**
- **FDA Event Type** (PDUFA, AdCom, etc.)
- **Date**
- **Description**
- **Indication** (Medical condition)
- **Status** (Pending, Approved, Rejected)
- **Phase** (I, II, III, NDA)
- **URL**

## Hedge Fund Data (`hedge_fund_fetcher.py`)

### Institutions
- **Institution Name**
- **Institution ID**
- **Website**
- **Location**
- **CEO/Manager**
- **Type** (Hedge Fund, Mutual Fund, etc.)
- **AUM** (Assets Under Management)
- **Portfolio Value**
- **Number of Holdings**

### Institution Holdings
- **Institution ID**
- **Ticker Symbol**
- **Company Name**
- **Shares Held**
- **Value** (Dollar amount)
- **Portfolio Percentage**
- **Change in Shares** (From previous filing)
- **Change Percentage**
- **Filing Date**
- **Quarter End**

### Institution Activity
- **Institution ID**
- **Ticker Symbol**
- **Company Name**
- **Activity Type** (New, Add, Reduce, Exit)
- **Shares Changed**
- **Value Changed** (Dollar amount)
- **Filing Date**

## Alerts (`options_flow_schema.sql`)

- **Alert ID**
- **Related Ticker**
- **Alert Type**
- **Message**
- **Source**
- **Created At**
- **Is Read** (Boolean)
- **Priority** (Low/Medium/High)
- **Expires At**

## Data Sources

The system collects data from the following external APIs:

1. **Alpha Vantage API** (`API_KEY_ALPHA_VANTAGE`)
   - Basic stock info
   - Technical indicators
   - Crypto data
   - Forex rates
   - Commodity prices

2. **Unusual Whales API** (`API_KEY_UNUSUAL_WHALES`)
   - Options flow
   - Dark pool trades
   - Insider transactions
   - Analyst ratings
   - Political trades
   - Detailed company information

3. **FRED API** (`FRED_API_KEY`)
   - Economic indicators
   - Economic data series

4. **News APIs** (Various)
   - Market news
   - Sentiment analysis

## Database Tables

The system stores data in the following key tables:

1. **Stock Information Tables**
   - `stock_info` - Basic stock data
   - `stock_details` - Comprehensive company information

2. **Technical Analysis Tables**
   - `technical_indicators` - Technical indicators like MACD, RSI

3. **Options Flow Tables**
   - `options_flow` - Individual options transactions
   - `option_flow_data` - Analyzed options flow

4. **Trading Activity Tables**
   - `insider_trades` - Insider buying/selling
   - `dark_pool_data` - Off-exchange transactions
   - `political_trades` - Congressional trades

5. **Market Analysis Tables**
   - `analyst_ratings` - Analyst recommendations
   - `market_news` - Financial news and articles

6. **Financial Instrument Tables**
   - `crypto_info` - Cryptocurrency data
   - `forex_info` - Foreign exchange rates
   - `commodity_info` - Commodity prices

7. **Economic Data Tables**
   - `economic_reports` - Economic releases
   - `economic_events` - Economic calendar events
   - `fred_observations` - FRED economic series data

8. **User Data Tables**
   - `watchlists` - User watchlist entries
   - `alerts` - User alerts configuration

9. **Institutional Data Tables**
   - `institutions` - Fund and institution profiles
   - `institution_holdings` - 13F holdings
   - `institution_activity` - Position changes
   - `hedge_fund_trades` - Notable hedge fund trades

10. **Biotech Calendar Tables**
    - `fda_calendar` - FDA decision dates 