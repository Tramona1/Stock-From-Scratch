import { NextResponse, NextRequest } from 'next/server';
import { getAuth } from '@clerk/nextjs/server';

export async function GET(req: NextRequest) {
  try {
    // Get auth using the request object
    const auth = getAuth(req);
    const userId = auth.userId;
    
    console.log("Auth check in test API - userId:", userId);
    
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized', auth: auth }, { status: 401 });
    }
    
    return NextResponse.json({ 
      success: true, 
      userId: userId
    });
  } catch (error: any) {
    console.error('Error in test API:', error);
    return NextResponse.json(
      { error: 'Server error', message: error?.message || 'Unknown error' },
      { status: 500 }
    );
  }
} 