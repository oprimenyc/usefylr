from flask import Blueprint, render_template, flash, redirect, url_for, request, abort
from flask_login import login_required, current_user
from app.app import db
from app.models import TaxStrategy, AuditLog
from app.access_control import requires_access_level

# Create blueprint
strategy_bp = Blueprint('strategy', __name__, url_prefix='/strategies')

@strategy_bp.route('/')
@login_required
def home():
    """Strategy module home page"""
    strategies = TaxStrategy.query.filter_by(user_id=current_user.id).all()
    return render_template('strategies/home.html', strategies=strategies)

@strategy_bp.route('/questionnaire')
@login_required
def questionnaire():
    """Tax strategy questionnaire"""
    # This is a placeholder for the strategy questionnaire page
    return render_template('strategies/questionnaire.html')

@strategy_bp.route('/analysis')
@login_required
def analysis():
    """Tax strategy analysis based on questionnaire answers"""
    # Placeholder for strategy analysis page
    return render_template('strategies/analysis.html')

@strategy_bp.route('/view/<int:strategy_id>')
@login_required
def view_strategy(strategy_id):
    """View a specific tax strategy"""
    strategy = TaxStrategy.query.filter_by(id=strategy_id, user_id=current_user.id).first_or_404()
    return render_template('strategies/view.html', strategy=strategy)