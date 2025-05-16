from flask import Blueprint, render_template, flash, redirect, url_for, request, session
from flask_login import login_required, current_user
from app.app import db
from app.models import User, AuditLog, LegalAcknowledgment
from datetime import datetime

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
    # Check if the user has acknowledged the legal disclaimer
    if not current_user.has_acknowledged_disclaimer:
        flash('You must acknowledge the legal disclaimer before accessing the tax tools.', 'warning')
        return redirect(url_for('main.legal_disclaimer'))
    
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

@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page"""
    return render_template('profile.html')

@main_bp.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile information"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if username already exists (excluding current user)
        if username != current_user.username:
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already exists.', 'danger')
                return redirect(url_for('main.profile'))
        
        # Check if email already exists (excluding current user)
        if email != current_user.email:
            existing_email = User.query.filter_by(email=email).first()
            if existing_email:
                flash('Email already exists.', 'danger')
                return redirect(url_for('main.profile'))
        
        # Update user information
        current_user.username = username
        current_user.email = email
        
        # Update password if provided
        if password and password.strip():
            current_user.set_password(password)
        
        # Log the profile update
        log = AuditLog()
        log.user_id = current_user.id
        log.action = "profile_update"
        log.details = "User profile updated"
        log.ip_address = request.remote_addr
        db.session.add(log)
        
        # Commit changes
        db.session.commit()
        
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('main.profile'))
    
    return redirect(url_for('main.profile'))

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

@main_bp.route('/legal-disclaimer')
@login_required
def legal_disclaimer():
    """Legal disclaimer page required before using services"""
    # Check if user has already acknowledged
    if current_user.has_acknowledged_disclaimer:
        flash('You have already completed the legal disclaimer.', 'info')
        return redirect(url_for('main.dashboard'))
    
    return render_template('legal_disclaimer.html')

@main_bp.route('/process-disclaimer', methods=['POST'])
@login_required
def process_disclaimer():
    """Process legal disclaimer form submission"""
    if request.method == 'POST':
        # Check if all required fields are present
        required_fields = [
            'acknowledged_accuracy', 
            'acknowledged_not_professional',
            'acknowledged_no_liability',
            'accuracy_initials',
            'professional_initials',
            'liability_initials',
            'full_name'
        ]
        
        # Verify all fields are present
        missing_fields = [field for field in required_fields if field not in request.form]
        if missing_fields:
            flash('Please complete all required fields.', 'danger')
            return redirect(url_for('main.legal_disclaimer'))
        
        # Create new acknowledgment record
        legal_ack = LegalAcknowledgment()
        legal_ack.user_id = current_user.id
        legal_ack.acknowledged_accuracy = True
        legal_ack.acknowledged_not_professional = True
        legal_ack.acknowledged_no_liability = True
        legal_ack.full_name = request.form.get('full_name')
        legal_ack.ip_address = request.remote_addr
        legal_ack.created_at = datetime.utcnow()
        
        # Update user record to mark acknowledgment as complete
        current_user.has_acknowledged_disclaimer = True
        
        # Log the acknowledgment 
        log = AuditLog()
        log.user_id = current_user.id
        log.action = "legal_disclaimer_accepted" 
        log.details = f"User acknowledged legal disclaimer. Full name: {request.form.get('full_name')}"
        log.ip_address = request.remote_addr
        log.created_at = datetime.utcnow()
        
        # Save to database
        db.session.add(legal_ack)
        db.session.add(log)
        db.session.commit()
        
        flash('Thank you for acknowledging our legal disclaimer. You may now use the services.', 'success')
        return redirect(url_for('main.dashboard'))
        
    return redirect(url_for('main.legal_disclaimer'))

@main_bp.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@main_bp.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return render_template('500.html'), 500