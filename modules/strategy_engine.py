from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
import json
import logging
from app.app import db
from app.models import TaxStrategy, AuditLog
from app.session import FormSession
from app.access_control import requires_access_level
from ai.analyzer import analyze_tax_answers, generate_tax_strategies

strategy_bp = Blueprint('strategy', __name__)

# Strategy questions from uploaded document
strategy_questions = [
    "Do you have any employees besides yourself?",
    "Did you purchase any new equipment this year?",
    "Do you rent or own your office/workspace?",
    "Did you earn income from software, consulting, or digital services?",
    "Do you have a retirement plan through your business?",
    "Do you work from home at least 20 hours a week?",
    "Was your net income above $50,000 this year?",
    "Did you pay yourself via payroll or owner draws?"
]

@strategy_bp.route('/strategy')
@login_required
def strategy_home():
    """Strategy module home page"""
    # Get user's saved strategies
    strategies = TaxStrategy.query.filter_by(user_id=current_user.id).all()
    
    return render_template(
        'strategy_home.html',
        strategies=strategies
    )

@strategy_bp.route('/strategy/questionnaire', methods=['GET', 'POST'])
@login_required
@requires_access_level('strategy_unlock')
def strategy_questionnaire():
    """Tax strategy questionnaire"""
    if request.method == 'POST':
        # Process questionnaire answers
        answers = {}
        for question in strategy_questions:
            # Generate a key by taking first few words of question
            key = "_".join(question.lower().split()[:3]).replace('?', '')
            value = request.form.get(key, 'no') == 'yes'
            answers[key] = value
        
        # Save answers to session
        FormSession.save_strategy_answers(answers)
        
        # Redirect to analysis page
        return redirect(url_for('strategy.strategy_analysis'))
    
    # Show questionnaire
    return render_template(
        'strategy_questionnaire.html',
        questions=strategy_questions
    )

@strategy_bp.route('/strategy/analysis')
@login_required
@requires_access_level('strategy_unlock')
def strategy_analysis():
    """Tax strategy analysis based on questionnaire answers"""
    # Get saved answers
    answers = FormSession.get_strategy_answers()
    if not answers:
        flash('Please complete the questionnaire first', 'warning')
        return redirect(url_for('strategy.strategy_questionnaire'))
    
    # Get AI-generated strategies or use fallback logic
    try:
        strategies = generate_tax_strategies(answers)
        
        # If API fails, fall back to simple logic
        if not strategies:
            strategies = suggest_strategies(answers)
    except Exception as e:
        logging.error(f"Error generating strategies: {str(e)}")
        strategies = suggest_strategies(answers)
    
    # Store strategies in database
    for strategy in strategies:
        new_strategy = TaxStrategy(
            user_id=current_user.id,
            strategy_name=strategy['name'],
            description=strategy['description'],
            estimated_savings=strategy.get('estimated_savings'),
            answers=answers
        )
        db.session.add(new_strategy)
    
    try:
        # Log the action
        log = AuditLog(
            user_id=current_user.id,
            action="strategy_generated",
            ip_address=request.remote_addr,
            details=f"Generated {len(strategies)} tax strategies"
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error saving strategies: {str(e)}")
    
    return render_template(
        'strategy_analysis.html',
        strategies=strategies,
        answers=answers
    )

@strategy_bp.route('/strategy/view/<int:strategy_id>')
@login_required
def view_strategy(strategy_id):
    """View a specific tax strategy"""
    strategy = TaxStrategy.query.filter_by(id=strategy_id, user_id=current_user.id).first_or_404()
    
    return render_template(
        'view_strategy.html',
        strategy=strategy
    )

def suggest_strategies(answers):
    """Fallback function to suggest strategies based on questionnaire answers"""
    strategies = []
    
    # Home office deduction
    if answers.get('do_you_work', False):
        strategies.append({
            'name': 'Home Office Deduction',
            'description': 'You may qualify for the home office deduction since you work from home at least 20 hours per week. This could allow you to deduct a portion of your home expenses including rent/mortgage, utilities, and insurance.',
            'estimated_savings': 1200
        })
    
    # Section 179 or Bonus Depreciation
    if answers.get('did_you_purchase', False):
        strategies.append({
            'name': 'Section 179 or Bonus Depreciation',
            'description': 'Since you purchased new equipment this year, you might qualify for Section 179 deduction or bonus depreciation, allowing you to immediately expense the full cost of qualifying equipment rather than depreciating it over several years.',
            'estimated_savings': 5000
        })
    
    # Retirement plan deductions
    if answers.get('do_you_have', False):
        strategies.append({
            'name': 'Retirement Plan Deductions',
            'description': 'Consider maximizing contributions to your business retirement plan such as a SEP IRA or Solo 401(k). These contributions are tax-deductible and allow you to build retirement savings.',
            'estimated_savings': 4000
        })
    
    # QBI Deduction
    if answers.get('did_you_earn', False):
        strategies.append({
            'name': 'Qualified Business Income (QBI) Deduction',
            'description': 'As a provider of software, consulting, or digital services, you may qualify for the QBI deduction, which allows eligible business owners to deduct up to 20% of their qualified business income.',
            'estimated_savings': 5000
        })
    
    # S Corporation strategy
    if answers.get('was_your_net', False) and not answers.get('did_you_pay', False):
        strategies.append({
            'name': 'S Corporation Tax Strategy',
            'description': 'With your income level, you might benefit from operating as an S Corporation, which could reduce self-employment taxes by allowing you to pay yourself a reasonable salary plus distributions.',
            'estimated_savings': 3000
        })
    
    return strategies
