"""
Main application routes
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import BusinessProfile, BusinessType
from app.services.tax_engine import calculate_audit_risk, calculate_tax_savings

# Create blueprint
main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    """Home page route"""
    # Use premium homepage for landing page
    return render_template("premium_homepage.html")

@main_bp.route("/dashboard")
@login_required
def dashboard():
    """User dashboard route"""
    return render_template("dashboard.html")

@main_bp.route("/profile")
@login_required
def profile():
    """User profile route"""
    return render_template("profile.html")

@main_bp.route("/plans")
def plans():
    """Pricing plans route"""
    from app.pricing import TIERS, BUSINESS_TYPES, AUDIT_PROTECTION
    return render_template(
        "pricing.html",
        tiers=TIERS, 
        business_types=BUSINESS_TYPES,
        audit_protection=AUDIT_PROTECTION
    )

@main_bp.route("/pricing")
def pricing():
    """Redirect to plans page"""
    return redirect(url_for("main.plans"))

@main_bp.route("/terms")
def terms():
    """Terms of use page"""
    return render_template("legal/terms.html")

@main_bp.route("/privacy")
def privacy():
    """Privacy policy page"""
    return render_template("legal/privacy.html")

@main_bp.route("/legal-disclaimer")
def legal_disclaimer():
    """Legal disclaimer page"""
    return render_template("legal/legal_disclaimer.html")

@main_bp.route("/export")
def export():
    """Export tax documents page"""
    return render_template("export.html")

@main_bp.route('/intake', methods=['GET', 'POST'])
@login_required
def intake():
    """Premium 5-step intake flow for business profile"""
    if request.method == 'POST':
        step = request.json.get('step')
        data = request.json.get('data')

        # Save to session incrementally
        if f'intake_step_{step}' not in session:
            session[f'intake_step_{step}'] = {}
        session[f'intake_step_{step}'] = data
        session.modified = True

        if step == 5:  # Final step - commit all data to BusinessProfile
            # Get or create BusinessProfile
            profile = BusinessProfile.query.filter_by(user_id=current_user.id).first()
            if not profile:
                profile = BusinessProfile(user_id=current_user.id)

            # Map entity type string to enum
            entity_type_str = session.get('intake_step_2', {}).get('entity_type', 'sole_proprietor')
            entity_type_map = {
                'sole_proprietor': BusinessType.SOLE_PROPRIETOR,
                'llc': BusinessType.LLC,
                's_corp': BusinessType.S_CORP,
                'c_corp': BusinessType.C_CORP
            }

            # Update profile fields
            profile.business_type = entity_type_map.get(entity_type_str, BusinessType.SOLE_PROPRIETOR)
            profile.annual_revenue = session.get('intake_step_3', {}).get('revenue', 0)
            profile.industry = session.get('intake_step_1', {}).get('industry', '')

            # Handle complexity flags
            complexity_flags = session.get('intake_step_4', {}).get('complexity', [])
            profile.has_employees = 'employees' in complexity_flags
            profile.contractor_count = 1 if 'contractors' in complexity_flags else 0

            # Store additional complexity flags in data JSON field
            if not profile.data:
                profile.data = {}
            profile.data['complexity_flags'] = complexity_flags
            profile.data['full_name'] = session.get('intake_step_1', {}).get('name', '')

            db.session.add(profile)
            db.session.commit()

            # Clear intake session data
            for i in range(1, 6):
                session.pop(f'intake_step_{i}', None)

            return jsonify({'redirect': '/portal'})

        return jsonify({'success': True, 'next_step': step + 1})

    # GET request - show intake form
    # Check for ?start parameter for Quick Actions
    start_param = request.args.get('start', '1')
    step_map = {'volume': 3, 'entity': 2, 'complexity': 4}
    initial_step = step_map.get(start_param, 1)

    return render_template('intake.html', initial_step=initial_step)

@main_bp.route('/portal')
@login_required
def portal():
    """User portal with metrics and recommendations"""
    profile = BusinessProfile.query.filter_by(user_id=current_user.id).first()

    # Route guard: force incomplete profiles back to intake
    if not profile or not profile.business_type:
        flash('Please complete your business profile first.', 'info')
        return redirect(url_for('main.intake'))

    # Calculate metrics from saved data
    audit_risk = calculate_audit_risk(profile)
    tax_intelligence = calculate_tax_savings(profile)

    return render_template('portal.html',
                         audit_risk=audit_risk,
                         tax_intelligence=tax_intelligence,
                         profile=profile)

# Error handlers
def page_not_found(e):
    """Handle 404 errors"""
    return render_template("404.html"), 404

def server_error(e):
    """Handle 500 errors - no stack trace exposed"""
    return render_template("500.html"), 500
