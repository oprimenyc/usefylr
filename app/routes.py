from flask import Blueprint, render_template, flash, redirect, url_for, request, session
from flask_login import login_required, current_user

# Create blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Landing page for the tax tool"""
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard after login"""
    # Get user's access level
    access_level = current_user.get_access_level()
    
    # Get user's forms, letters, and strategies
    forms = current_user.tax_forms
    letters = current_user.irs_letters
    strategies = current_user.tax_strategies
    
    return render_template(
        'dashboard.html',
        access_level=access_level,
        forms=forms,
        letters=letters,
        strategies=strategies
    )

@main_bp.route('/pricing')
def pricing():
    """Show pricing plans for various features"""
    pricing_data = {
        "basic_diy": {
            "name": "Basic DIY Filing",
            "price": 25,
            "features": ["Zero-activity return generator", "PDF download", "Email support"]
        },
        "guided_filing": {
            "name": "Guided Filing",
            "price": 99,
            "features": ["Step-by-step input", "Form 1120/1065/Schedule C generation", "State filing add-on"]
        },
        "strategy_unlock": {
            "name": "Strategy Unlock",
            "price": 149,
            "features": ["QBI deduction check", "Entity optimization guide", "Section 179 & R&D credits", "S Corp vs C Corp modeling"]
        },
        "irs_letter_pack": {
            "name": "IRS Letter Generator",
            "price": 39,
            "features": ["Penalty abatement letters", "Reasonable cause templates", "Late filing relief letter"]
        }
    }
    
    # Determine which plans the user has access to
    user_plans = {}
    if current_user.is_authenticated:
        for plan_id, plan_data in pricing_data.items():
            user_plans[plan_id] = current_user.has_paid(plan_id)
    else:
        user_plans = {plan_id: False for plan_id in pricing_data}
        
    return render_template('pricing.html', pricing=pricing_data, user_plans=user_plans)

@main_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('profile.html')

@main_bp.route('/success')
def success():
    """Payment success page"""
    return render_template('success.html')

@main_bp.route('/terms')
def terms():
    """Terms of use page"""
    return render_template('legal/terms.html')

@main_bp.route('/privacy')
def privacy():
    """Privacy policy page"""
    return render_template('legal/privacy.html')

@main_bp.route('/acknowledgment')
def acknowledgment():
    """Legal acknowledgment page"""
    return render_template('legal/acknowledgment.html')

@main_bp.route('/process-acknowledgment', methods=['POST'])
def process_acknowledgment():
    """Process legal acknowledgment form"""
    if request.method == 'POST':
        # Store acknowledgment in session
        session['legal_acknowledged'] = True
        
        # Get the acknowledgments that were checked
        acknowledgments = request.form.getlist('acknowledgments[]')
        
        # Check if all required acknowledgments were made
        required_acks = ['accurate_info', 'not_advice', 'responsible_filings', 'not_liable', 'due_diligence', 'terms_accepted']
        if all(ack in acknowledgments for ack in required_acks):
            flash('Thank you for acknowledging our legal terms.', 'success')
            
            # Redirect based on where they were going
            next_page = session.get('next_after_acknowledgment', url_for('main.dashboard'))
            session.pop('next_after_acknowledgment', None)
            return redirect(next_page)
        else:
            flash('You must acknowledge all terms to proceed.', 'danger')
            return redirect(url_for('main.acknowledgment'))
    
    return redirect(url_for('main.acknowledgment'))

@main_bp.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@main_bp.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return render_template('500.html'), 500