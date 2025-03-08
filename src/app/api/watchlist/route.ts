import { NextRequest, NextResponse } from 'next/server';
import { getAuth } from '@clerk/nextjs/server';
import { createClient } from '@/lib/supabase/server';
import { getUserWatchlist, addToWatchlist, removeFromWatchlist } from '@/services/database';
import { createUserIfNotExists } from '@/services/users';

// Force dynamic to avoid caching issues
export const dynamic = 'force-dynamic';

// GET: Get user's watchlist
export async function GET(req: NextRequest) {
  try {
    const { userId } = getAuth(req);
    
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    console.log(`API: Fetching watchlist for user: ${userId}`);
    
    // Ensure user exists in Supabase
    await createUserIfNotExists(userId);
    
    try {
      // Get watchlist from Supabase
      const watchlistItems = await getUserWatchlist(userId);
      
      // Temporarily generate mock price data for each ticker
      // Until we set up the stock_info table or use a real market data API
      const transformedWatchlist = watchlistItems.map(item => ({
        id: item.id,
        symbol: item.ticker,
        price: generateMockPrice(item.ticker),
        change: generateMockChange(),
        volume: generateMockVolume(),
        watching: true
      }));
  
      return NextResponse.json({ 
        success: true, 
        watchlist: transformedWatchlist
      });
    } catch (fetchError) {
      console.error('Error fetching watchlist items:', fetchError);
      // Return empty watchlist instead of error
      return NextResponse.json({ 
        success: true, 
        watchlist: []
      });
    }
  } catch (error: any) {
    console.error('Error in watchlist API:', error);
    // Return empty watchlist rather than error
    return NextResponse.json({ 
      success: true, 
      watchlist: [] 
    });
  }
}

// POST: Add ticker to watchlist
export async function POST(req: NextRequest) {
  try {
    const { userId } = getAuth(req);
    
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const data = await req.json();
    const { ticker } = data;
    
    if (!ticker) {
      return NextResponse.json({ error: 'Ticker is required' }, { status: 400 });
    }

    console.log(`API: Adding ticker ${ticker} for user: ${userId}`);

    // Ensure user exists in Supabase
    await createUserIfNotExists(userId);
    
    try {
      // Add ticker to watchlist
      console.log(`Calling addToWatchlist with userId: ${userId}, ticker: ${ticker.toUpperCase()}`);
      await addToWatchlist(userId, ticker.toUpperCase());
      console.log(`Successfully added ticker ${ticker.toUpperCase()} to watchlist`);
      
      // Get updated watchlist
      const watchlistItems = await getUserWatchlist(userId);
      console.log(`Retrieved updated watchlist with ${watchlistItems.length} items`);
      
      // Return mock data for now
      const transformedWatchlist = watchlistItems.map(item => ({
        id: item.id,
        symbol: item.ticker,
        price: generateMockPrice(item.ticker),
        change: generateMockChange(),
        volume: generateMockVolume(),
        watching: true
      }));
  
      return NextResponse.json({ 
        success: true, 
        message: `Added ${ticker.toUpperCase()} to watchlist`,
        watchlist: transformedWatchlist
      });
    } catch (addError) {
      console.error('Error adding ticker to watchlist:', addError);
      // Return 200 with current watchlist instead of throwing an error
      // This prevents navigation on error but still shows the error in logs
      const currentWatchlist = await getUserWatchlist(userId);
      const transformedWatchlist = currentWatchlist.map(item => ({
        id: item.id,
        symbol: item.ticker,
        price: generateMockPrice(item.ticker),
        change: generateMockChange(),
        volume: generateMockVolume(),
        watching: true
      }));
      
      return NextResponse.json({
        success: false,
        message: `Failed to add ${ticker.toUpperCase()} to watchlist`,
        error: (addError as Error).message,
        watchlist: transformedWatchlist
      }, { status: 200 }); // Still return 200 to prevent page navigation
    }
  } catch (error: any) {
    console.error('Error in POST /api/watchlist:', error);
    // Return 200 with error message to prevent page navigation
    return NextResponse.json(
      { 
        success: false, 
        error: 'Server error', 
        message: error?.message || 'Unknown error',
        watchlist: [] 
      },
      { status: 200 }
    );
  }
}

// DELETE: Remove ticker from watchlist
export async function DELETE(req: NextRequest) {
  try {
    const { userId } = getAuth(req);
    
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(req.url);
    const ticker = searchParams.get('ticker');
    
    if (!ticker) {
      return NextResponse.json({ error: 'Ticker is required' }, { status: 400 });
    }

    try {
      // Remove ticker from watchlist
      await removeFromWatchlist(userId, ticker.toUpperCase());
      
      // Get updated watchlist
      const watchlistItems = await getUserWatchlist(userId);
      
      // Return mock data for now
      const transformedWatchlist = watchlistItems.map(item => ({
        id: item.id,
        symbol: item.ticker,
        price: generateMockPrice(item.ticker),
        change: generateMockChange(),
        volume: generateMockVolume(),
        watching: true
      }));
  
      return NextResponse.json({ 
        success: true, 
        message: `Removed ${ticker.toUpperCase()} from watchlist`,
        watchlist: transformedWatchlist
      });
    } catch (removeError) {
      console.error('Error removing ticker from watchlist:', removeError);
      throw removeError;
    }
  } catch (error: any) {
    console.error('Error removing from watchlist:', error);
    return NextResponse.json(
      { error: 'Server error', message: error?.message || 'Unknown error' },
      { status: 500 }
    );
  }
}

// Helper functions to generate mock data
function generateMockPrice(ticker: string): number {
  // Generate a pseudo-random but consistent price based on ticker string
  const sum = ticker.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return Math.floor(50 + (sum % 450)) + Math.random() * 10;
}

function generateMockChange(): number {
  // Generate a random percent change between -5% and +5%
  return (Math.random() * 10 - 5).toFixed(2) as unknown as number;
}

function generateMockVolume(): string {
  // Generate a random volume string
  const volume = Math.floor(Math.random() * 20) + 1;
  const decimal = Math.floor(Math.random() * 9);
  return `${volume}.${decimal}M`;
} 