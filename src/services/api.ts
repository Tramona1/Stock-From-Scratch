// Base configuration for external APIs
const ALPHA_VANTAGE_API_KEY = process.env.NEXT_PUBLIC_API_KEY_ALPHA_VANTAGE;
const UNUSUAL_WHALES_API_KEY = process.env.NEXT_PUBLIC_API_KEY_UNUSUAL_WHALES;
const FRED_API_KEY = process.env.NEXT_PUBLIC_FRED_API_KEY;

// Generic fetch function with error handling
async function fetchData<T>(url: string): Promise<T> {
  const response = await fetch(url);
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(`API Error (${response.status}): ${JSON.stringify(errorData) || response.statusText}`);
  }
  
  return response.json();
}

// ======== Alpha Vantage API ========
export async function getStockQuote(symbol: string) {
  const url = `https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=${symbol}&apikey=${ALPHA_VANTAGE_API_KEY}`;
  return fetchData(url);
}

export async function getStockOverview(symbol: string) {
  const url = `https://www.alphavantage.co/query?function=OVERVIEW&symbol=${symbol}&apikey=${ALPHA_VANTAGE_API_KEY}`;
  return fetchData(url);
}

export async function getDailyStockData(symbol: string, outputSize: 'compact' | 'full' = 'compact') {
  const url = `https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=${symbol}&outputsize=${outputSize}&apikey=${ALPHA_VANTAGE_API_KEY}`;
  return fetchData(url);
}

// ======== FRED API ========
export async function getEconomicIndicator(seriesId: string) {
  const url = `https://api.stlouisfed.org/fred/series/observations?series_id=${seriesId}&api_key=${FRED_API_KEY}&file_type=json`;
  return fetchData(url);
}

// ======== Unusual Whales API ========
export async function getOptionsFlow() {
  const url = `https://unusualwhales.com/api/flow/all?api_key=${UNUSUAL_WHALES_API_KEY}`;
  return fetchData(url);
}

export async function getDarkPoolData() {
  const url = `https://unusualwhales.com/api/dark_pool/all?api_key=${UNUSUAL_WHALES_API_KEY}`;
  return fetchData(url);
} 