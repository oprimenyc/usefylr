"""
Admin Blueprint - Tax Rules Administration

Transplanted from Tax Rules Administration System
Provides admin interface for managing tax rules, viewing audit logs,
and accessing business profile analytics.
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import BusinessProfile, User, AuditLog
from app.services.tax_engine import DEFAULT_TAX_RULES, TaxCalculationEngine
from sqlalchemy import func, desc
from datetime import datetime

# Create admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator to require admin access"""
    from functools import wraps

    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        # Check if user is admin (you can add a role field to User model later)
        # For now, just require authentication
        if not current_user.is_authenticated:
            flash('Admin access required', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard with system overview"""

    # Get statistics
    total_users = User.query.count()
    total_profiles = BusinessProfile.query.count()
    recent_profiles = BusinessProfile.query.order_by(desc(BusinessProfile.created_at)).limit(10).all()

    # Revenue statistics
    total_revenue = db.session.query(func.sum(BusinessProfile.annual_revenue)).scalar() or 0
    avg_revenue = db.session.query(func.avg(BusinessProfile.annual_revenue)).scalar() or 0

    # Entity type distribution
    entity_distribution = db.session.query(
        BusinessProfile.business_type,
        func.count(BusinessProfile.id)
    ).group_by(BusinessProfile.business_type).all()

    # Industry distribution
    industry_distribution = db.session.query(
        BusinessProfile.industry,
        func.count(BusinessProfile.id)
    ).filter(BusinessProfile.industry.isnot(None)).group_by(BusinessProfile.industry).limit(10).all()

    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_profiles=total_profiles,
                         total_revenue=total_revenue,
                         avg_revenue=avg_revenue,
                         entity_distribution=entity_distribution,
                         industry_distribution=industry_distribution,
                         recent_profiles=recent_profiles)


@admin_bp.route('/tax-rules')
@admin_required
def tax_rules():
    """Tax rules management page"""
    return render_template('admin/tax_rules.html',
                         tax_rules=DEFAULT_TAX_RULES,
                         current_year=2026)


@admin_bp.route('/tax-rules/<int:year>')
@admin_required
def tax_rules_by_year(year):
    """Get tax rules for specific year (API endpoint)"""
    rules = DEFAULT_TAX_RULES.get(year)

    if not rules:
        return jsonify({'error': 'Tax rules not found for year'}), 404

    return jsonify({
        'year': year,
        'standardDeductions': rules['standard_deductions'],
        'taxBrackets': rules['tax_brackets'],
        'selfEmploymentTaxRate': rules['self_employment_tax_rate'],
        'qbiDeductionRate': rules['qbi_deduction_rate']
    })


@admin_bp.route('/profiles')
@admin_required
def profiles():
    """View all business profiles"""
    page = request.args.get('page', 1, type=int)
    per_page = 50

    # Get filters
    entity_filter = request.args.get('entity')
    industry_filter = request.args.get('industry')

    query = BusinessProfile.query

    if entity_filter:
        query = query.filter(BusinessProfile.business_type == entity_filter)
    if industry_filter:
        query = query.filter(BusinessProfile.industry.ilike(f'%{industry_filter}%'))

    profiles_pagination = query.order_by(desc(BusinessProfile.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # Calculate stats for each profile
    profile_stats = []
    engine = TaxCalculationEngine()

    for profile in profiles_pagination.items:
        audit_risk = engine.calculate_audit_risk(profile)
        tax_savings = engine.calculate_tax_savings(profile)

        profile_stats.append({
            'profile': profile,
            'audit_risk': audit_risk,
            'tax_savings': tax_savings
        })

    return render_template('admin/profiles.html',
                         profiles=profile_stats,
                         pagination=profiles_pagination)


@admin_bp.route('/profiles/<int:profile_id>')
@admin_required
def profile_detail(profile_id):
    """View detailed business profile"""
    profile = BusinessProfile.query.get_or_404(profile_id)

    # Calculate tax metrics
    engine = TaxCalculationEngine()
    audit_risk = engine.calculate_audit_risk(profile)
    tax_savings = engine.calculate_tax_savings(profile)
    quarterly_payments = engine.estimate_quarterly_tax_payments(profile)

    # Get user info
    user = User.query.get(profile.user_id)

    return render_template('admin/profile_detail.html',
                         profile=profile,
                         user=user,
                         audit_risk=audit_risk,
                         tax_savings=tax_savings,
                         quarterly_payments=quarterly_payments)


@admin_bp.route('/audit-log')
@admin_required
def audit_log():
    """View system audit log"""
    page = request.args.get('page', 1, type=int)
    per_page = 100

    # Get filters
    table_name = request.args.get('table')

    query = AuditLog.query

    if table_name:
        query = query.filter(AuditLog.table_name == table_name)

    logs_pagination = query.order_by(desc(AuditLog.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('admin/audit_log.html',
                         logs=logs_pagination.items,
                         pagination=logs_pagination)


@admin_bp.route('/analytics')
@admin_required
def analytics():
    """Advanced analytics dashboard"""

    # Revenue by entity type
    revenue_by_entity = db.session.query(
        BusinessProfile.business_type,
        func.sum(BusinessProfile.annual_revenue).label('total_revenue'),
        func.avg(BusinessProfile.annual_revenue).label('avg_revenue'),
        func.count(BusinessProfile.id).label('count')
    ).group_by(BusinessProfile.business_type).all()

    # Revenue by industry (top 10)
    revenue_by_industry = db.session.query(
        BusinessProfile.industry,
        func.sum(BusinessProfile.annual_revenue).label('total_revenue'),
        func.count(BusinessProfile.id).label('count')
    ).filter(BusinessProfile.industry.isnot(None))\
     .group_by(BusinessProfile.industry)\
     .order_by(desc('total_revenue'))\
     .limit(10).all()

    # Complexity analysis
    total_with_employees = BusinessProfile.query.filter(BusinessProfile.has_employees == True).count()
    total_with_contractors = BusinessProfile.query.filter(BusinessProfile.contractor_count > 0).count()
    total_with_home_office = BusinessProfile.query.filter(BusinessProfile.has_home_office == True).count()

    # Calculate average audit risk across all profiles
    engine = TaxCalculationEngine()
    profiles = BusinessProfile.query.all()
    risk_scores = [engine.calculate_audit_risk(p)['score'] for p in profiles if p.annual_revenue]
    avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0

    return render_template('admin/analytics.html',
                         revenue_by_entity=revenue_by_entity,
                         revenue_by_industry=revenue_by_industry,
                         total_with_employees=total_with_employees,
                         total_with_contractors=total_with_contractors,
                         total_with_home_office=total_with_home_office,
                         avg_risk_score=avg_risk_score)


@admin_bp.route('/users')
@admin_required
def users():
    """View all users"""
    page = request.args.get('page', 1, type=int)
    per_page = 50

    users_pagination = User.query.order_by(desc(User.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # Get profiles for each user
    user_data = []
    for user in users_pagination.items:
        profile = BusinessProfile.query.filter_by(user_id=user.id).first()
        user_data.append({
            'user': user,
            'profile': profile,
            'has_profile': profile is not None
        })

    return render_template('admin/users.html',
                         users=user_data,
                         pagination=users_pagination)


@admin_bp.route('/api/stats')
@admin_required
def api_stats():
    """API endpoint for dashboard stats (for AJAX refresh)"""
    total_users = User.query.count()
    total_profiles = BusinessProfile.query.count()
    total_revenue = db.session.query(func.sum(BusinessProfile.annual_revenue)).scalar() or 0
    avg_revenue = db.session.query(func.avg(BusinessProfile.annual_revenue)).scalar() or 0

    return jsonify({
        'total_users': total_users,
        'total_profiles': total_profiles,
        'total_revenue': float(total_revenue),
        'avg_revenue': float(avg_revenue),
        'timestamp': datetime.utcnow().isoformat()
    })
