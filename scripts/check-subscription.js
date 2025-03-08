/**
 * Script to check a subscription status in Stripe
 * Run with: node scripts/check-subscription.js <subscription_id>
 */

// Load environment variables from .env file
require('dotenv').config();

const Stripe = require('stripe');
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);

async function checkSubscription(subscriptionId) {
  try {
    console.log(`Checking subscription: ${subscriptionId}`);
    
    const subscription = await stripe.subscriptions.retrieve(subscriptionId);
    
    console.log(`\nSubscription Details:`);
    console.log(`---------------------------------`);
    console.log(`Status: ${subscription.status}`);
    console.log(`Cancel at period end: ${subscription.cancel_at_period_end}`);
    console.log(`Current period end: ${new Date(subscription.current_period_end * 1000)}`);
    console.log(`Customer: ${subscription.customer}`);
    console.log(`Plan: ${subscription.items.data[0].plan.nickname || subscription.items.data[0].plan.id}`);
    
    // Check if it's going to cancel
    if (subscription.cancel_at_period_end) {
      console.log(`\nThis subscription WILL CANCEL at the end of the billing period.`);
      console.log(`No future invoices will be generated after ${new Date(subscription.current_period_end * 1000)}.`);
    } else {
      console.log(`\nThis subscription will automatically renew at the end of the billing period.`);
      
      // Check for upcoming invoice
      const upcomingInvoice = await stripe.invoices.retrieveUpcoming({
        subscription: subscriptionId,
      });
      
      console.log(`Next invoice amount: $${(upcomingInvoice.amount_due / 100).toFixed(2)}`);
      console.log(`Next invoice date: ${new Date(upcomingInvoice.next_payment_attempt * 1000)}`);
    }
    
  } catch (error) {
    console.error('Error checking subscription:', error.message);
  }
}

// Get subscription ID from command line argument
const subscriptionId = process.argv[2];

if (!subscriptionId) {
  console.error('Please provide a subscription ID as an argument.');
  console.error('Usage: node scripts/check-subscription.js <subscription_id>');
  process.exit(1);
}

checkSubscription(subscriptionId); 