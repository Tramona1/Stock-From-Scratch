import { Webhook } from 'svix';
import { WebhookEvent } from '@clerk/nextjs/server';
import { headers } from 'next/headers';
import { NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';

export async function POST(req: Request) {
  const WEBHOOK_SECRET = process.env.CLERK_WEBHOOK_SECRET;

  if (!WEBHOOK_SECRET) {
    throw new Error('Please add CLERK_WEBHOOK_SECRET from Clerk Dashboard to .env or .env.local');
  }

  // Get the headers
  const headerPayload = headers();
  const svix_id = headerPayload.get('svix-id');
  const svix_timestamp = headerPayload.get('svix-timestamp');
  const svix_signature = headerPayload.get('svix-signature');

  // If there are no headers, error out
  if (!svix_id || !svix_timestamp || !svix_signature) {
    return new Response('Error occured -- no svix headers', {
      status: 400,
    });
  }

  // Get the body
  const payload = await req.json();
  const body = JSON.stringify(payload);

  // Create a new Svix instance with your secret.
  const wh = new Webhook(WEBHOOK_SECRET);

  let evt: WebhookEvent;

  // Verify the payload with the headers
  try {
    evt = wh.verify(body, {
      'svix-id': svix_id,
      'svix-timestamp': svix_timestamp,
      'svix-signature': svix_signature,
    }) as WebhookEvent;
  } catch (err) {
    console.error('Error verifying webhook:', err);
    return new Response('Error occured', {
      status: 400,
    });
  }

  // Get the ID and type
  const { id } = evt.data;
  const eventType = evt.type;

  console.log(`Webhook with ID: ${id} and type: ${eventType}`);
  console.log('Webhook body:', body);

  const supabase = createClient();

  // Process based on the event type
  if (eventType === 'user.created') {
    const { id, email_addresses, first_name, last_name, primary_email_address_id } = evt.data;

    // Get primary email address from Clerk data
    const primaryEmail = email_addresses?.find(
      (email: any) => email.id === primary_email_address_id
    )?.email_address;

    if (!primaryEmail) {
      console.error('No primary email found for user:', id);
      return new Response(JSON.stringify({ error: 'No primary email found' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    console.log(`Creating user in Supabase: ${id}, email: ${primaryEmail}`);

    // First check if user already exists
    const { data: existingUser, error: checkError } = await supabase
      .from('users')
      .select('id')
      .eq('id', id)
      .single();
      
    if (existingUser) {
      console.log(`User ${id} already exists in Supabase, skipping creation`);
      return new Response(
        JSON.stringify({ message: 'User already exists in Supabase' }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Add user to Supabase
    const { error } = await supabase.from('users').insert({
      id: id,
      email: primaryEmail,
      first_name: first_name || null,
      last_name: last_name || null,
      subscription_status: 'inactive',
      plan_type: 'free',
      is_annual: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      cancel_at_period_end: false
    });

    if (error) {
      console.error('Error adding user to Supabase:', error);
      return new Response(
        JSON.stringify({ error: 'Error adding user to Supabase', details: error }),
        { status: 500, headers: { 'Content-Type': 'application/json' } }
      );
    }

    console.log(`Successfully created user ${id} in Supabase`);
    return new Response(
      JSON.stringify({ message: 'User created in Supabase successfully' }),
      { status: 201, headers: { 'Content-Type': 'application/json' } }
    );
  }

  return new Response('Event processed', { status: 200 });
} 