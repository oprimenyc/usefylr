import os
import logging
import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, redirect, url_for, render_template, flash, current_app
from flask_login import login_required, current_user

# Import with try-except to handle missing Stripe API key
try:
    import stripe
    stripe_available = True
except (ImportError, ModuleNotFoundError):
    stripe_available = False

from app.app import db
from app.models import Payment, Subscription, AuditLog

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
        payment = Payment(
            user_id=current_user.id,
            stripe_payment_id="demo_" + datetime.now().strftime("%Y%m%d%H%M%S"),
            amount=price,
            feature=product_id,
            status='demo'
        )
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
        payment = Payment(
            user_id=current_user.id,
            stripe_payment_id=checkout_session.id,
            amount=price,
            feature=product_id,
            status='pending'
        )
        db.session.add(payment)
        
        # Log checkout initiation
        log = AuditLog(
            user_id=current_user.id,
            action="checkout_initiated",
            details=f"Checkout initiated for {product['name']}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        # Redirect to Stripe checkout
        return redirect(checkout_session.url)
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
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logging.error(f"Invalid signature: {e}")
        return jsonify({'status': 'error', 'message': 'Invalid signature'}), 400
    
    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Call the appropriate function based on the event type
        fulfill_order(session)
    
    return jsonify({'status': 'success'})

def fulfill_order(session):
    """Process a successful payment"""
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
            
            # Log payment completion
            log = AuditLog(
                user_id=user_id,
                action="payment_completed",
                details=f"Payment completed for {product_id}",
                ip_address=request.remote_addr if request else None
            )
            db.session.add(log)
            db.session.commit()
    except Exception as e:
        logging.error(f"Error fulfilling order: {e}")
        db.session.rollback()