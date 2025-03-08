import { NextRequest, NextResponse } from 'next/server';
import { getAuth } from '@clerk/nextjs/server';
import { createClient } from '@/lib/supabase/server';
import { GoogleGenerativeAI } from '@google/generative-ai';

// Force dynamic to prevent caching
export const dynamic = 'force-dynamic';

// Initialize Gemini AI
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || '');

// Define allowed data types
const ALLOWED_DATA_TYPES = [
  'insider_trades',
  'analyst_ratings',
  'options_flow',
  'economic_calendar_events',
  'fda_calendar_events',
  'political_trades',
  'dark_pool_data',
  'financial_news'
];

export async function POST(req: NextRequest) {
  try {
    // Get authentication details
    const { userId } = getAuth(req);
    
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    
    // Parse request body
    const { query, watchlistSymbols, history } = await req.json();
    
    if (!query || typeof query !== 'string') {
      return NextResponse.json({ error: 'Query is required and must be a string' }, { status: 400 });
    }
    
    // Initialize Supabase client
    const supabase = createClient();
    
    // Extract relevant data based on query and watchlist
    const relevantData = await getRelevantData(supabase, query, watchlistSymbols || []);
    
    // Generate AI response using Gemini
    const response = await generateAIResponse(query, relevantData, history || []);
    
    return NextResponse.json(response);
  } catch (error: any) {
    console.error('Error in AI query endpoint:', error);
    return NextResponse.json(
      { error: 'Failed to process AI query', message: error.message },
      { status: 500 }
    );
  }
}

async function getRelevantData(supabase: any, query: string, watchlistSymbols: string[]) {
  // Extract entities from query (e.g., stock symbols, data types)
  const dataTypes = extractDataTypes(query);
  const symbols = extractSymbols(query) || watchlistSymbols;
  
  // Don't proceed if no symbols are available
  if (!symbols || symbols.length === 0) {
    return [{
      type: 'no_data',
      message: 'No stocks found in watchlist or query. Please add stocks to your watchlist or specify stock symbols in your query.'
    }];
  }
  
  // Initialize results array
  const results = [];
  
  // Query relevant data based on extracted entities
  if (dataTypes.includes('insider_trades') || dataTypes.length === 0) {
    try {
      const { data: insiderTrades, error } = await supabase
        .from('insider_trades')
        .select('*')
        .in('symbol', symbols)
        .order('transaction_date', { ascending: false })
        .limit(10);
        
      if (error) {
        console.error('Error fetching insider trades:', error);
      } else if (insiderTrades?.length > 0) {
        results.push({
          type: 'insider_trades',
          data: insiderTrades
        });
      }
    } catch (error) {
      console.error('Exception fetching insider trades:', error);
    }
  }
  
  // Add similar logic for other data types
  if (dataTypes.includes('analyst_ratings') || dataTypes.length === 0) {
    try {
      const { data: analystRatings, error } = await supabase
        .from('analyst_ratings')
        .select('*')
        .in('symbol', symbols)
        .order('rating_date', { ascending: false })
        .limit(10);
        
      if (error) {
        console.error('Error fetching analyst ratings:', error);
      } else if (analystRatings?.length > 0) {
        results.push({
          type: 'analyst_ratings',
          data: analystRatings
        });
      }
    } catch (error) {
      console.error('Exception fetching analyst ratings:', error);
    }
  }
  
  // Check for options flow data
  if (dataTypes.includes('options_flow') || dataTypes.length === 0) {
    try {
      const { data: optionsFlow, error } = await supabase
        .from('options_flow')
        .select('*')
        .in('ticker', symbols)
        .order('date', { ascending: false })
        .limit(10);
        
      if (error) {
        console.error('Error fetching options flow:', error);
      } else if (optionsFlow?.length > 0) {
        results.push({
          type: 'options_flow',
          data: optionsFlow
        });
      }
    } catch (error) {
      console.error('Exception fetching options flow:', error);
    }
  }
  
  // Check for economic calendar events
  if (dataTypes.includes('economic_calendar') || dataTypes.length === 0) {
    try {
      const today = new Date();
      const oneMonthAgo = new Date();
      oneMonthAgo.setMonth(today.getMonth() - 1);
      
      const { data: economicEvents, error } = await supabase
        .from('economic_calendar_events')
        .select('*')
        .gte('event_date', oneMonthAgo.toISOString())
        .order('event_date', { ascending: false })
        .limit(10);
        
      if (error) {
        console.error('Error fetching economic calendar:', error);
      } else if (economicEvents?.length > 0) {
        results.push({
          type: 'economic_calendar_events',
          data: economicEvents
        });
      }
    } catch (error) {
      console.error('Exception fetching economic calendar:', error);
    }
  }
  
  // Check for FDA calendar events
  if (dataTypes.includes('fda_calendar') || dataTypes.length === 0) {
    try {
      const { data: fdaEvents, error } = await supabase
        .from('fda_calendar_events')
        .select('*')
        .in('ticker', symbols)
        .order('end_date', { ascending: false })
        .limit(10);
        
      if (error) {
        console.error('Error fetching FDA calendar:', error);
      } else if (fdaEvents?.length > 0) {
        results.push({
          type: 'fda_calendar_events',
          data: fdaEvents
        });
      }
    } catch (error) {
      console.error('Exception fetching FDA calendar:', error);
    }
  }
  
  // If no data was found in any category, return empty result
  if (results.length === 0) {
    results.push({
      type: 'no_data',
      message: `No relevant data found for the specified stocks: ${symbols.join(', ')}`
    });
  }
  
  return results;
}

function extractDataTypes(query: string): string[] {
  const dataTypeKeywords: Record<string, string> = {
    'insider': 'insider_trades',
    'insider trade': 'insider_trades',
    'buying': 'insider_trades',
    'selling': 'insider_trades',
    'purchase': 'insider_trades',
    'bought': 'insider_trades',
    'sold': 'insider_trades',
    'analyst': 'analyst_ratings',
    'rating': 'analyst_ratings',
    'upgrade': 'analyst_ratings',
    'downgrade': 'analyst_ratings',
    'price target': 'analyst_ratings',
    'recommendation': 'analyst_ratings',
    'options': 'options_flow',
    'option flow': 'options_flow',
    'call': 'options_flow',
    'put': 'options_flow',
    'option activity': 'options_flow',
    'economic': 'economic_calendar',
    'gdp': 'economic_calendar',
    'inflation': 'economic_calendar',
    'fed': 'economic_calendar',
    'interest rate': 'economic_calendar',
    'employment': 'economic_calendar',
    'event': 'economic_calendar',
    'fda': 'fda_calendar',
    'approval': 'fda_calendar',
    'drug': 'fda_calendar',
    'clinical': 'fda_calendar',
    'trial': 'fda_calendar',
    'phase': 'fda_calendar',
    'politician': 'political_trades',
    'congress': 'political_trades',
    'senator': 'political_trades',
    'representative': 'political_trades',
    'dark pool': 'dark_pool_data',
    'off exchange': 'dark_pool_data',
    'block trade': 'dark_pool_data',
    'news': 'financial_news',
    'article': 'financial_news',
    'headline': 'financial_news'
  };
  
  const queryLower = query.toLowerCase();
  const matchedTypes = new Set<string>();
  
  for (const [keyword, dataType] of Object.entries(dataTypeKeywords)) {
    if (queryLower.includes(keyword.toLowerCase())) {
      matchedTypes.add(dataType);
    }
  }
  
  return Array.from(matchedTypes);
}

function extractSymbols(query: string): string[] | null {
  // Simple regex to extract ticker symbols (could be enhanced)
  const tickerRegex = /\b[A-Z]{1,5}\b/g;
  const matches = query.match(tickerRegex);
  
  // Filter out common English words that might match the pattern
  const commonWords = new Set([
    'I', 'A', 'THE', 'FOR', 'AND', 'OR', 'TO', 'IN', 'OF', 'AT', 'BY', 'AS', 'IS', 
    'IT', 'BE', 'AM', 'PM', 'IF', 'MY', 'WE', 'US', 'NO', 'ME', 'HE', 'SHE', 'AN'
  ]);
  
  return matches?.filter(match => !commonWords.has(match)) || null;
}

function formatDataForContext(type: string, data: any[]): string {
  if (type === 'no_data') {
    return `No Data: ${data[0]?.message || 'No relevant financial data was found.'}`;
  }
  
  switch (type) {
    case 'insider_trades':
      return `Insider Trading Data:\n${data.map(item => 
        `- ${item.insider_name} (${item.insider_title}) ${item.transaction_type} ${item.shares.toLocaleString()} shares of ${item.symbol} at $${item.price.toFixed(2)} on ${new Date(item.transaction_date).toLocaleDateString()}, total value: $${(item.shares * item.price).toLocaleString()}`
      ).join('\n')}`;
      
    case 'analyst_ratings':
      return `Analyst Ratings:\n${data.map(item => 
        `- ${item.analyst_firm} ${item.rating_action} ${item.symbol} to "${item.rating}" with price target $${item.price_target} on ${new Date(item.rating_date).toLocaleDateString()}`
      ).join('\n')}`;
      
    case 'options_flow':
      return `Options Flow Activity:\n${data.map(item => 
        `- ${item.ticker} ${item.option_type} ${item.strike_price} ${item.expiration_date} purchased for $${item.premium} with volume of ${item.volume.toLocaleString()} on ${new Date(item.date).toLocaleDateString()}`
      ).join('\n')}`;
      
    case 'economic_calendar_events':
      return `Economic Calendar Events:\n${data.map(item => 
        `- ${item.event_name} on ${new Date(item.event_date).toLocaleDateString()}: Previous: ${item.previous}, Forecast: ${item.forecast}, Actual: ${item.actual}, Impact: ${item.impact}`
      ).join('\n')}`;
      
    case 'fda_calendar_events':
      return `FDA Calendar Events:\n${data.map(item => 
        `- ${item.ticker}: ${item.drug_name} (${item.event_type}) for ${item.indication} on ${new Date(item.end_date).toLocaleDateString()}`
      ).join('\n')}`;
      
    case 'political_trades':
      return `Political Trading Activity:\n${data.map(item => 
        `- ${item.representative_name} (${item.party}-${item.state}) ${item.transaction_type} $${item.amount_range} of ${item.symbol} on ${new Date(item.transaction_date).toLocaleDateString()}`
      ).join('\n')}`;
      
    case 'dark_pool_data':
      return `Dark Pool Trading Activity:\n${data.map(item => 
        `- ${item.ticker}: ${item.volume.toLocaleString()} shares at $${item.price.toFixed(2)} (${item.percent_of_daily_volume}% of daily volume) on ${new Date(item.executed_at).toLocaleDateString()}`
      ).join('\n')}`;
      
    case 'financial_news':
      return `Financial News:\n${data.map(item => 
        `- ${item.title} (${new Date(item.publish_date).toLocaleDateString()}): ${item.summary}`
      ).join('\n')}`;
      
    default:
      return `${type} data: ${JSON.stringify(data).substring(0, 1000)}...`;
  }
}

async function generateAIResponse(query: string, relevantData: any[], history: any[]) {
  try {
    // Format data for the AI model
    let context = "I'll help you analyze financial data from your watchlist. ";
    
    if (!relevantData || relevantData.length === 0 || relevantData[0].type === 'no_data') {
      context += "I don't have any specific data matching your query. ";
      if (relevantData && relevantData[0]?.type === 'no_data') {
        context += relevantData[0].message;
      }
    } else {
      context += "Here's what I know based on your query:\n\n";
      
      relevantData.forEach(item => {
        if (item.type && item.data && Array.isArray(item.data)) {
          context += `${formatDataForContext(item.type, item.data)}\n\n`;
        }
      });
    }
    
    // Initialize Gemini model
    const model = genAI.getGenerativeModel({ model: "gemini-1.5-pro" });
    
    // Format history for Gemini
    const formattedHistory = history?.map(msg => ({
      role: msg.role === 'user' ? 'user' : 'model',
      parts: [{ text: msg.content }]
    })) || [];
    
    // Create chat session with history
    const chat = model.startChat({
      history: formattedHistory,
      generationConfig: {
        temperature: 0.4,
        topP: 0.8,
        topK: 40,
        maxOutputTokens: 1024,
      }
    });
    
    // Generate response
    const result = await chat.sendMessage(
      `${context}\n\nUser query: ${query}\n\nPlease provide a helpful, accurate response based on the financial data provided. If you don't have data to answer the question directly, provide general advice but make it clear when you are not using specific data from our database.`
    );
    
    return {
      answer: result.response.text(),
      sources: relevantData.map(item => ({
        type: item.type,
        count: item.data?.length || 0
      }))
    };
  } catch (error: any) {
    console.error('Error generating AI response:', error);
    throw new Error(`Failed to generate AI response: ${error.message}`);
  }
} 