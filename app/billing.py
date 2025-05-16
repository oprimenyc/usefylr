import os
import logging
import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, redirect, url_for, render_template, flash, current_app
from flask_login import login_required, current_user
import stripe

# Import with try-except to handle missing Stripe API key
try:
    import stripe
    stripe_available = True
except (ImportError, ModuleNotFoundError):
    stripe_available = False

from app.app import db
from app.models import User, Payment, Subscription, AuditLog, UserPlan, SubscriptionType

# Create blueprint
billing_bp = Blueprint('billing', __name__, url_prefix='/billing')

# Initialize Stripe if available
if stripe_available:
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '')
    if not stripe.api_key:
        logging.warning("STRIPE_SECRET_KEY environment variable is not set. Stripe features will be limited.")

# Pricing data for the new tiered structure
pricing_tiers = {
    # Basic tier (free or minimal cost)
    "basic_plan": {
        "name": ".fylr Basic",
        "price": 0,
        "plan_type": "basic",
        "billing_type": "one_time",
        "features": ["Guided AI-based data input", "Auto-fill IRS form fields", "Generate IRS-ready documents", 
                    "PDF export of generated files", "Optional tooltips/educational guidance"],
        "stripe_price_id": "price_basic_plan"
    },
    
    # .fylr+ tier options
    "fylr_plus_monthly": {
        "name": ".fylr+ Monthly",
        "price": 47,
        "plan_type": "fylr_plus",
        "billing_type": "recurring",
        "billing_period": "monthly",
        "features": ["All Basic features", "Save and resume tax data progress", "Smart form logic",
                    "Enhanced AI support with explanations", "Dynamic checklist generation",
                    "Export clean, ready-to-file forms"],
        "stripe_price_id": "price_fylr_plus_monthly"
    },
    "fylr_plus_onetime": {
        "name": ".fylr+ One-time",
        "price": 47,
        "plan_type": "fylr_plus",
        "billing_type": "one_time",
        "features": ["All Basic features", "Save and resume tax data progress", "Smart form logic",
                    "Enhanced AI support with explanations", "Dynamic checklist generation",
                    "Export clean, ready-to-file forms"],
        "stripe_price_id": "price_fylr_plus_onetime"
    },
    
    # Pro tier options
    "pro_basic": {
        "name": ".fylr Pro Basic",
        "price": 97,
        "plan_type": "pro",
        "billing_type": "one_time",
        "features": ["All .fylr+ features", "AI-enhanced deduction detection", "AI-sorted uploads",
                    "Filing export support"],
        "stripe_price_id": "price_pro_basic"
    },
    "pro_standard": {
        "name": ".fylr Pro Standard",
        "price": 147,
        "plan_type": "pro",
        "billing_type": "one_time",
        "features": ["All .fylr+ features", "AI-enhanced deduction detection", "AI-sorted uploads",
                    "Filing export support", "Basic audit protection"],
        "stripe_price_id": "price_pro_standard"
    },
    "pro_premium": {
        "name": ".fylr Pro Premium",
        "price": 197,
        "plan_type": "pro",
        "billing_type": "one_time",
        "features": ["All .fylr+ features", "AI-enhanced deduction detection", "AI-sorted uploads",
                    "Filing export support", "Premium audit protection", "Priority support"],
        "stripe_price_id": "price_pro_premium"
    }
}

@billing_bp.route('/checkout/<product_id>', methods=['GET', 'POST'])
@login_required
def create_checkout_session(product_id):
    """Create a Stripe checkout session for a product"""
    # Verify that the product ID is valid
    if product_id not in pricing_tiers:
        flash('Invalid product.', 'danger')
        return redirect(url_for('main.pricing'))
    
    # Get product information
    product = pricing_tiers[product_id]
    
    # Apply discount if user is a subscription member
    price = product['price']
    if current_user.subscription_member:
        price = price * 0.5  # 50% discount
    
    # Check if Stripe is available and configured
    if not stripe_available or not os.environ.get('STRIPE_SECRET_KEY'):
        flash('Payment processing is currently unavailable. Please try again later.', 'warning')
        # Create record for demo purposes
        payment = Payment()
        payment.user_id = current_user.id
        payment.stripe_payment_id = "demo_" + datetime.now().strftime("%Y%m%d%H%M%S")
        payment.amount = price
        payment.feature = product_id
        payment.status = 'demo'
        db.session.add(payment)
        db.session.commit()
        
        # For demo purposes, redirect to success page
        flash('Demo mode: Payment would be processed here in production.', 'info')
        return redirect(url_for('billing.success', product_id=product_id))
    
    try:
        # Determine domain for success/cancel URLs
        domain_url = request.host_url.rstrip('/')
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer_email=current_user.email,
            client_reference_id=str(current_user.id),
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': product['name'],
                            'description': ', '.join(product['features'])
                        },
                        'unit_amount': int(price * 100)  # Convert to cents
                    },
                    'quantity': 1,
                }
            ],
            metadata={
                'product_id': product_id,
                'user_id': str(current_user.id)
            },
            mode='payment',
            success_url=domain_url + url_for('billing.success', product_id=product_id),
            cancel_url=domain_url + url_for('main.pricing')
        )
        
        # Create payment record
        payment = Payment()
        payment.user_id = current_user.id
        payment.stripe_payment_id = checkout_session.id
        payment.amount = price
        payment.feature = product_id
        payment.status = 'pending'
        db.session.add(payment)
        
        # Log checkout initiation
        log = AuditLog()
        log.user_id = current_user.id
        log.action = "checkout_initiated"
        log.details = f"Checkout initiated for {product['name']}"
        log.ip_address = request.remote_addr
        log.created_at = datetime.utcnow()
        db.session.add(log)
        db.session.commit()
        
        # Redirect to Stripe checkout
        if hasattr(checkout_session, 'url') and checkout_session.url is not None:
            return redirect(checkout_session.url)
        else:
            # Fallback if URL is not available
            flash('Unable to create checkout session. Please try again.', 'danger')
            return redirect(url_for('main.pricing'))
    except Exception as e:
        logging.error(f"Error creating checkout session: {e}")
        flash('An error occurred while processing your payment. Please try again.', 'danger')
        return redirect(url_for('main.pricing'))

@billing_bp.route('/success/<product_id>')
@login_required
def success(product_id):
    """Handle successful payment"""
    if product_id not in pricing_tiers:
        flash('Invalid product.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    product = pricing_tiers[product_id]
    
    flash(f'Thank you for purchasing {product["name"]}!', 'success')
    return render_template('billing/success.html', product=product)

@billing_bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle Stripe webhook events"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    # Verify webhook signature and extract the event
    try:
        endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError as e:
        # Invalid payload
        logging.error(f"Invalid payload: {e}")
        return jsonify({'status': 'error', 'message': 'Invalid payload'}), 400
    except Exception as e:
        # Invalid signature or other error
        logging.error(f"Webhook error: {e}")
        return jsonify({'status': 'error', 'message': 'Invalid signature or other error'}), 400
    
    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Call the appropriate function based on the event type
        fulfill_order(session)
    
    return jsonify({'status': 'success'})

def fulfill_order(session):
    """Process a successful payment and update the user's plan"""
    try:
        # Get metadata from session
        metadata = session.get('metadata', {})
        product_id = metadata.get('product_id')
        user_id = int(metadata.get('user_id', 0))
        
        if not product_id or not user_id:
            logging.error("Missing product_id or user_id in session metadata")
            return
        
        # Update payment record
        payment = Payment.query.filter_by(stripe_payment_id=session.id).first()
        if payment:
            payment.status = 'completed'
            
            # Get product information
            product = pricing_tiers.get(product_id)
            if not product:
                logging.error(f"Unknown product_id: {product_id}")
                db.session.commit()
                return
            
            # Get the user
            user = db.session.get(User, user_id)
            if not user:
                logging.error(f"User not found: {user_id}")
                db.session.commit()
                return
            
            # Get plan type from product
            plan_type = product.get('plan_type')
            billing_type = product.get('billing_type')
            
            # Update user's plan based on the purchase
            if plan_type == 'pro':
                user.plan = UserPlan.PRO
            elif plan_type == 'fylr_plus':
                user.plan = UserPlan.FYLR_PLUS
            elif plan_type == 'basic':
                user.plan = UserPlan.BASIC
                
            # Create subscription record for recurring payments
            if billing_type == 'recurring':
                # For subscription, create a Subscription record
                subscription_type = None
                if product_id == 'fylr_plus_monthly':
                    subscription_type = SubscriptionType.FYLR_PLUS_MONTHLY
                
                if subscription_type:
                    # Calculate end date for monthly subscription (1 month from now)
                    end_date = datetime.utcnow() + timedelta(days=30)
                    
                    # Create new subscription
                    subscription = Subscription()
                    subscription.user_id = user_id
                    subscription.subscription_type = subscription_type
                    subscription.price = product.get('price', 0)
                    subscription.is_recurring = True
                    subscription.billing_period = product.get('billing_period', 'monthly')
                    subscription.starts_at = datetime.utcnow()
                    subscription.ends_at = end_date
                    subscription.status = 'active'
                    
                    db.session.add(subscription)
            
            # For one-time purchases, we just need to update the user's plan
            # which was already done above
            
            # Log payment completion with more details
            log = AuditLog()
            log.user_id = user_id
            log.action = "payment_completed"
            log.details = f"Payment completed for {product.get('name')}. Plan upgraded to {plan_type}."
            log.ip_address = request.remote_addr if request else None
            log.created_at = datetime.utcnow()
            
            db.session.add(log)
            db.session.commit()
    except Exception as e:
        logging.error(f"Error fulfilling order: {e}")
        db.session.rollback()