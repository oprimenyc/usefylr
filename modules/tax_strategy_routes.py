"""
Tax Strategy Routes Module

This module provides routes for displaying and generating tax strategies
based on user data and questionnaire responses.
"""

from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify, current_app
from flask_login import login_required, current_user
from app.app import db
from app.models import User, TaxForm, TaxStrategy, UserPlan
from app.access_control import requires_access_level
from ai.tax_strategy import generate_detailed_strategies, get_entity_optimization
from modules.upgrade_prompts import should_show_upgrade_prompt, get_upgrade_prompt_message
from modules.export_utils import export_strategy_as_pdf, export_strategy_as_json, export_strategy_as_html
import json
from datetime import datetime

# Create blueprint
tax_strategy_bp = Blueprint('tax_strategy', __name__, url_prefix='/tax-strategy')

@tax_strategy_bp.route('/')
@login_required
def index():
    """Tax strategy dashboard showing personalized recommendations"""
    # Get user's strategies
    strategies = TaxStrategy.query.filter_by(user_id=current_user.id).order_by(TaxStrategy.created_at.desc()).all()
    
    # Get business data for the current user
    business_data = get_user_business_data(current_user.id)
    
    # Determine if we should show an upgrade prompt
    show_prompt = should_show_upgrade_prompt(current_user, business_data)
    prompt_message = ""
    prompt_title = ""
    prompt_cta = ""
    
    if show_prompt:
        prompt_message, prompt_title, prompt_cta = get_upgrade_prompt_message(
            current_user, business_data, context='tax_strategy'
        )
    
    return render_template('tax_strategy/index.html',
                          strategies=strategies,
                          user_plan=current_user.plan.name.lower(),
                          show_prompt=show_prompt,
                          prompt_message=prompt_message,
                          prompt_title=prompt_title,
                          prompt_cta=prompt_cta)

@tax_strategy_bp.route('/generate')
@login_required
def generate_new():
    """Generate a new tax strategy"""
    # Get business data and questionnaire answers
    business_data = get_user_business_data(current_user.id)
    questionnaire_answers = get_user_questionnaire_answers(current_user.id)
    
    # Determine current tax year (for a real application, this would be more sophisticated)
    tax_year = datetime.now().year - 1  # Previous tax year
    
    # Generate strategies based on user's subscription level
    user_plan = current_user.plan.name.lower()
    
    try:
        # Generate strategies using the AI module
        strategies = generate_detailed_strategies(
            business_data, questionnaire_answers, tax_year, user_plan
        )
        
        # Save strategies to database
        for strategy in strategies:
            # Create a new strategy record
            new_strategy = TaxStrategy(
                user_id=current_user.id,
                strategy_name=strategy.get('strategy_name', 'Tax Strategy'),
                description=strategy.get('description', ''),
                estimated_savings=strategy.get('estimated_savings'),
                implementation_steps=strategy.get('implementation_steps', []),
                qualifications=strategy.get('qualifications', []),
                tax_year=tax_year,
                tier=strategy.get('tier', user_plan),
                data={
                    'business_data': business_data,
                    'questionnaire_answers': questionnaire_answers
                }
            )
            db.session.add(new_strategy)
        
        db.session.commit()
        flash("Successfully generated new tax strategies.", "success")
    except Exception as e:
        current_app.logger.error(f"Error generating tax strategies: {str(e)}")
        flash("An error occurred while generating tax strategies. Please try again later.", "danger")
    
    return redirect(url_for('tax_strategy.index'))

@tax_strategy_bp.route('/entity-optimization')
@login_required
@requires_access_level('pro')
def entity_optimization():
    """Show entity structure optimization recommendations"""
    # Get business data and questionnaire answers
    business_data = get_user_business_data(current_user.id)
    questionnaire_answers = get_user_questionnaire_answers(current_user.id)
    
    try:
        # Generate entity optimization recommendations
        optimization_data = get_entity_optimization(business_data, questionnaire_answers)
        
        return render_template('tax_strategy/entity_optimization.html',
                              optimization=optimization_data,
                              business_data=business_data)
    except Exception as e:
        current_app.logger.error(f"Error generating entity optimization: {str(e)}")
        flash("An error occurred while generating entity recommendations. Please try again later.", "danger")
        return redirect(url_for('tax_strategy.index'))

@tax_strategy_bp.route('/export/<int:strategy_id>')
@login_required
@requires_access_level('export_forms')
def export_strategy(strategy_id):
    """Export a tax strategy in the specified format"""
    # Get the requested strategy
    strategy = TaxStrategy.query.filter_by(id=strategy_id, user_id=current_user.id).first_or_404()
    
    # Get the requested format
    export_format = request.args.get('format', 'pdf')
    
    if export_format == 'pdf':
        return export_strategy_as_pdf(strategy)
    elif export_format == 'json':
        return export_strategy_as_json(strategy)
    elif export_format == 'html':
        return export_strategy_as_html(strategy)
    else:
        flash(f"Unsupported export format: {export_format}", "danger")
        return redirect(url_for('tax_strategy.index'))

@tax_strategy_bp.route('/delete/<int:strategy_id>', methods=['POST'])
@login_required
def delete_strategy(strategy_id):
    """Delete a tax strategy"""
    strategy = TaxStrategy.query.filter_by(id=strategy_id, user_id=current_user.id).first_or_404()
    
    db.session.delete(strategy)
    db.session.commit()
    
    flash("Strategy deleted successfully.", "success")
    return redirect(url_for('tax_strategy.index'))

# Helper functions
def get_user_business_data(user_id):
    """Get business data for a user"""
    # In a real application, this would retrieve data from a database
    # For prototype purposes, we'll return simulated data
    
    return {
        'business_name': 'Sample Business',
        'entity_type': 'llc_single',
        'annual_revenue': 125000,
        'industry': 'professional_services',
        'has_employees': True,
        'employee_count': 2,
        'states': ['CA', 'NY'],
        'has_home_office': True,
        'has_vehicle': True,
        'has_travel_expenses': True,
        'has_equipment_purchases': True
    }

def get_user_questionnaire_answers(user_id):
    """Get questionnaire answers for a user"""
    # In a real application, this would retrieve data from a database
    # For prototype purposes, we'll return simulated data
    
    return {
        'risk_level': 'moderate',
        'tax_preferences': {
            'prioritize_current_savings': True,
            'interested_in_retirement': True,
            'considering_entity_change': False
        },
        'business_goals': {
            'growth': True,
            'stability': True,
            'exit_planning': False
        },
        'expense_patterns': {
            'high_travel': True,
            'home_office': True,
            'vehicle_usage': True,
            'equipment_investment': True
        }
    }