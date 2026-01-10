"""
Onboarding Blueprint - Smart Entry Point

Progressive onboarding that shows AI value before requiring registration.
"""

from flask import Blueprint, render_template, redirect, url_for, session, request, jsonify
from flask_login import current_user

# Create blueprint
onboarding_bp = Blueprint('onboarding', __name__)


@onboarding_bp.route('/onboarding')
def start():
    """
    Onboarding entry point - Welcome screen with AI Buy Box demo

    Shows the AI parsing in action BEFORE requiring registration.
    This creates immediate value and hooks the user.
    """
    # If already authenticated, skip onboarding
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    # Track that user has seen onboarding
    session['onboarding_started'] = True

    return render_template('onboarding/welcome.html')


@onboarding_bp.route('/onboarding/try-ai', methods=['POST'])
def try_ai():
    """
    Let anonymous users try the AI parser before registering

    Returns JSON for dynamic glass card updates
    """
    from app.modules.intake import parse_expense_string

    data = request.get_json()
    description = data.get('description', '')

    if not description:
        return jsonify({
            'success': False,
            'error': 'Please describe a business expense'
        }), 400

    # Parse the expense
    result = parse_expense_string(description)

    # Track demo usage in session
    if 'demo_expenses' not in session:
        session['demo_expenses'] = []

    session['demo_expenses'].append({
        'description': description,
        'amount': result['expense'].get('amount'),
        'category': result['expense'].get('irs_category')
    })

    # Add CTA after first demo
    result['show_signup_prompt'] = len(session.get('demo_expenses', [])) >= 1

    return jsonify(result), 200


@onboarding_bp.route('/onboarding/get-started')
def continue_to_signup():
    """
    Continue to signup after trying the AI

    Pre-fills demo data to personalize the signup experience
    """
    # Store intent to continue after signup
    session['return_to_onboarding'] = True

    # Redirect to signup with demo context
    return redirect(url_for('auth.register', source='onboarding'))


@onboarding_bp.route('/onboarding/skip')
def skip():
    """
    Skip onboarding and go straight to signup
    """
    session['onboarding_skipped'] = True
    return redirect(url_for('auth.register'))
