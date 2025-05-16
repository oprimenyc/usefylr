"""
Tax Questionnaire Module for .fylr

This module handles the business tax questionnaire functionality,
including form recommendations based on user input.
"""
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app.models import TaxFormType
from app.access_control import requires_legal_acknowledgment

# Create blueprint
questionnaire_bp = Blueprint('questionnaire', __name__, url_prefix='/questionnaire')

# Define business types
BUSINESS_TYPES = {
    'sole_proprietor': 'Sole Proprietor',
    'llc_single': 'LLC (Single Member)',
    'llc_multi': 'LLC (Multiple Members)',
    's_corp': 'S Corporation',
    'c_corp': 'C Corporation',
    'partnership': 'Partnership'
}

# Define states
STATES = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
    'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
    'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
    'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri',
    'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
    'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
    'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
    'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming',
    'DC': 'District of Columbia'
}

# Define tax years
TAX_YEARS = list(range(2023, 2026))  # 2023-2025

@questionnaire_bp.route('/', methods=['GET'])
@login_required
@requires_legal_acknowledgment
def index():
    """Main questionnaire page"""
    return render_template('questionnaire/index.html')

@questionnaire_bp.route('/start', methods=['GET', 'POST'])
@login_required
@requires_legal_acknowledgment
def start():
    """Start the tax questionnaire"""
    if request.method == 'POST':
        # Process form submission
        business_type = request.form.get('business_type')
        state = request.form.get('state')
        tax_year = request.form.get('tax_year')
        has_revenue = request.form.get('has_revenue') == 'yes'
        has_expenses = request.form.get('has_expenses') == 'yes'
        has_employees = request.form.get('has_employees') == 'yes'
        has_ein = request.form.get('has_ein') == 'yes'
        
        # Save questionnaire answers to session
        session['questionnaire_answers'] = {
            'business_type': business_type,
            'state': state,
            'tax_year': tax_year,
            'has_revenue': has_revenue,
            'has_expenses': has_expenses,
            'has_employees': has_employees,
            'has_ein': has_ein
        }
        
        # Redirect to results page
        return redirect(url_for('questionnaire.results'))
    
    # GET request - display the form
    return render_template('questionnaire/start.html', 
                          business_types=BUSINESS_TYPES,
                          states=STATES,
                          tax_years=TAX_YEARS)

@questionnaire_bp.route('/results', methods=['GET'])
@login_required
@requires_legal_acknowledgment
def results():
    """Show tax form recommendations based on questionnaire answers"""
    # Get answers from session
    answers = session.get('questionnaire_answers', {})
    
    if not answers:
        flash('Please complete the questionnaire first.', 'warning')
        return redirect(url_for('questionnaire.start'))
    
    # Determine complexity level
    complexity = determine_complexity(answers)
    
    # Get required forms
    required_forms = determine_required_forms(answers, complexity)
    
    # Determine next steps based on user plan
    next_steps = []
    if current_user.plan.name == 'PRO':
        next_steps = [
            "Use our AI-enhanced deduction detection to find potential tax savings",
            "Upload your documents for AI-assisted organization",
            "Access enhanced audit protection features"
        ]
    elif current_user.plan.name == 'FYLR_PLUS':
        next_steps = [
            "Save your progress and continue later",
            "Get enhanced AI explanations about your tax forms",
            "Use our smart form logic for easier completion"
        ]
    else:
        next_steps = [
            "Generate the recommended tax forms",
            "Add your business income and expense information",
            "Consider upgrading to .fylr+ for enhanced features"
        ]
    
    # Check if we should suggest an upgrade
    should_upgrade = complexity == 'complex' and current_user.plan.name == 'BASIC'
    
    return render_template('questionnaire/results.html',
                          answers=answers,
                          complexity=complexity,
                          required_forms=required_forms,
                          business_types=BUSINESS_TYPES,
                          states=STATES,
                          next_steps=next_steps,
                          should_upgrade=should_upgrade)

def determine_complexity(answers):
    """Determine the complexity level of the tax return"""
    # Complex: Has employees or both revenue and expenses
    if answers.get('has_employees'):
        return 'complex'
    
    # Basic activity: Has either revenue or expenses, but not both
    if answers.get('has_revenue') or answers.get('has_expenses'):
        return 'basic'
    
    # Zero activity: No revenue, no expenses
    return 'zero'

def determine_required_forms(answers, complexity):
    """Determine the required tax forms based on answers and complexity"""
    business_type = answers.get('business_type')
    state = answers.get('state')
    forms = []
    
    # Federal forms based on business type
    if business_type in ['sole_proprietor', 'llc_single']:
        forms.append({
            'id': 'schedule_c',
            'name': 'Schedule C (Form 1040)',
            'description': 'Profit or Loss From Business (Sole Proprietorship)',
            'deadline': 'April 15'
        })
    elif business_type in ['partnership', 'llc_multi']:
        forms.append({
            'id': '1065',
            'name': 'Form 1065',
            'description': 'U.S. Return of Partnership Income',
            'deadline': 'March 15'
        })
    elif business_type == 's_corp':
        forms.append({
            'id': '1120s',
            'name': 'Form 1120-S',
            'description': 'U.S. Income Tax Return for an S Corporation',
            'deadline': 'March 15'
        })
    elif business_type == 'c_corp':
        forms.append({
            'id': '1120',
            'name': 'Form 1120',
            'description': 'U.S. Corporation Income Tax Return',
            'deadline': 'April 15'
        })
    
    # Add state forms if applicable
    state_forms = get_state_forms(state, business_type)
    forms.extend(state_forms)
    
    # Add employment forms if they have employees
    if answers.get('has_employees'):
        forms.append({
            'id': '941',
            'name': 'Form 941',
            'description': 'Employer\'s Quarterly Federal Tax Return',
            'deadline': 'Quarterly'
        })
        forms.append({
            'id': '940',
            'name': 'Form 940',
            'description': 'Employer\'s Annual Federal Unemployment (FUTA) Tax Return',
            'deadline': 'January 31'
        })
    
    # Tag forms with complexity
    for form in forms:
        form['complexity'] = complexity
    
    return forms

def get_state_forms(state, business_type):
    """Get the required state tax forms based on state and business type"""
    # This is a simplified version - in a real app, this would be a comprehensive database
    forms = []
    
    # State income tax forms (simplified for example purposes)
    state_form_mapping = {
        'CA': {'name': 'Form 540/100/565', 'description': 'California Business Tax Return'},
        'NY': {'name': 'Form IT-201/CT-3/IT-204', 'description': 'New York Business Tax Return'},
        'TX': {'name': 'Form 05-158', 'description': 'Texas Franchise Tax Report'},
        'FL': {'name': 'Form F-1120', 'description': 'Florida Corporate Income Tax Return'},
        # Add other states as needed
    }
    
    if state in state_form_mapping:
        forms.append({
            'id': f'{state.lower()}_income',
            'name': state_form_mapping[state]['name'],
            'description': state_form_mapping[state]['description'],
            'deadline': 'Varies by state'
        })
    
    return forms