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
    has_revenue = answers.get('has_revenue')
    has_expenses = answers.get('has_expenses')
    has_employees = answers.get('has_employees')
    has_ein = answers.get('has_ein')
    forms = []
    
    # Core Federal forms based on business type
    if business_type in ['sole_proprietor', 'llc_single']:
        forms.append({
            'id': 'schedule_c',
            'name': 'Schedule C (Form 1040)',
            'description': 'Profit or Loss From Business (Sole Proprietorship)',
            'deadline': 'April 15',
            'category': 'core'
        })
        
        # Add Schedule SE for self-employment tax if they have revenue
        if has_revenue:
            forms.append({
                'id': 'schedule_se',
                'name': 'Schedule SE (Form 1040)',
                'description': 'Self-Employment Tax',
                'deadline': 'April 15',
                'category': 'core'
            })
            
    elif business_type in ['partnership', 'llc_multi']:
        forms.append({
            'id': '1065',
            'name': 'Form 1065',
            'description': 'U.S. Return of Partnership Income',
            'deadline': 'March 15',
            'category': 'core'
        })
        
        # Schedule K-1 for each partner
        forms.append({
            'id': '1065_k1',
            'name': 'Schedule K-1 (Form 1065)',
            'description': 'Partner\'s Share of Income, Deductions, Credits, etc.',
            'deadline': 'March 15',
            'category': 'core'
        })
        
    elif business_type == 's_corp':
        forms.append({
            'id': '1120s',
            'name': 'Form 1120-S',
            'description': 'U.S. Income Tax Return for an S Corporation',
            'deadline': 'March 15',
            'category': 'core'
        })
        
        # Schedule K-1 for each shareholder
        forms.append({
            'id': '1120s_k1',
            'name': 'Schedule K-1 (Form 1120-S)',
            'description': 'Shareholder\'s Share of Income, Deductions, Credits, etc.',
            'deadline': 'March 15',
            'category': 'core'
        })
        
    elif business_type == 'c_corp':
        forms.append({
            'id': '1120',
            'name': 'Form 1120',
            'description': 'U.S. Corporation Income Tax Return',
            'deadline': 'April 15',
            'category': 'core'
        })
    
    # Add depreciation forms if they have expenses (likely to have assets)
    if has_expenses:
        forms.append({
            'id': '4562',
            'name': 'Form 4562',
            'description': 'Depreciation and Amortization',
            'deadline': 'Same as primary return',
            'category': 'deduction'
        })
    
    # Add employment-related forms
    if has_employees:
        # Basic employment forms
        forms.append({
            'id': '941',
            'name': 'Form 941',
            'description': 'Employer\'s Quarterly Federal Tax Return',
            'deadline': 'Quarterly (Apr 30, Jul 31, Oct 31, Jan 31)',
            'category': 'employment'
        })
        
        forms.append({
            'id': '940',
            'name': 'Form 940',
            'description': 'Employer\'s Annual Federal Unemployment (FUTA) Tax Return',
            'deadline': 'January 31',
            'category': 'employment'
        })
        
        forms.append({
            'id': 'w2',
            'name': 'Form W-2',
            'description': 'Wage and Tax Statement (for each employee)',
            'deadline': 'January 31 (to employees and SSA)',
            'category': 'employment'
        })
        
        forms.append({
            'id': 'w3',
            'name': 'Form W-3',
            'description': 'Transmittal of Wage and Tax Statements',
            'deadline': 'January 31',
            'category': 'employment'
        })
    
    # Add information reporting forms if they have expenses (likely paying contractors)
    if has_expenses:
        forms.append({
            'id': '1099nec',
            'name': 'Form 1099-NEC',
            'description': 'Nonemployee Compensation (for contractors paid $600+)',
            'deadline': 'January 31',
            'category': 'information'
        })
        
        forms.append({
            'id': '1096',
            'name': 'Form 1096',
            'description': 'Annual Summary and Transmittal of U.S. Information Returns',
            'deadline': 'January 31',
            'category': 'information'
        })
    
    # Add estimated tax forms if they're likely to owe taxes
    if has_revenue:
        if business_type in ['sole_proprietor', 'llc_single']:
            forms.append({
                'id': '1040es',
                'name': 'Form 1040-ES',
                'description': 'Estimated Tax for Individuals',
                'deadline': 'Quarterly (Apr 15, Jun 15, Sep 15, Jan 15)',
                'category': 'estimated_tax'
            })
        elif business_type == 'c_corp':
            forms.append({
                'id': '1120w',
                'name': 'Form 1120-W',
                'description': 'Estimated Tax for Corporations',
                'deadline': 'Quarterly (Apr 15, Jun 15, Sep 15, Dec 15)',
                'category': 'estimated_tax'
            })
    
    # Add application for EIN if they don't have one
    if not has_ein:
        forms.append({
            'id': 'ss4',
            'name': 'Form SS-4',
            'description': 'Application for Employer Identification Number',
            'deadline': 'Before filing returns',
            'category': 'registration'
        })
    
    # Add state forms
    state_forms = get_state_forms(state, business_type)
    forms.extend(state_forms)
    
    # Add tax election forms if needed
    if business_type == 'llc_single' or business_type == 'llc_multi':
        forms.append({
            'id': '8832',
            'name': 'Form 8832',
            'description': 'Entity Classification Election',
            'deadline': 'Any time during tax year',
            'category': 'election',
            'note': 'Optional - only if changing default classification'
        })
    
    if business_type == 'llc_single' or business_type == 'llc_multi' or business_type == 'c_corp':
        forms.append({
            'id': '2553',
            'name': 'Form 2553',
            'description': 'Election by a Small Business Corporation (S Corporation)',
            'deadline': 'Within 2 months and 15 days of the beginning of tax year',
            'category': 'election',
            'note': 'Optional - only if electing S corporation status'
        })
    
    # Tag forms with complexity
    for form in forms:
        form['complexity'] = complexity
    
    return forms

def get_state_forms(state, business_type):
    """Get the required state tax forms based on state and business type"""
    forms = []
    
    # Comprehensive state form database
    state_forms = {
        'CA': {
            'sole_proprietor': [
                {'id': 'ca_540', 'name': 'Form 540', 'description': 'California Resident Income Tax Return', 'deadline': 'April 15'},
                {'id': 'ca_3522', 'name': 'Form 3522', 'description': 'LLC Tax Voucher', 'deadline': 'April 15'}
            ],
            'llc_single': [
                {'id': 'ca_568', 'name': 'Form 568', 'description': 'Limited Liability Company Return of Income', 'deadline': 'April 15'},
                {'id': 'ca_3522', 'name': 'Form 3522', 'description': 'LLC Tax Voucher', 'deadline': 'April 15'}
            ],
            'llc_multi': [
                {'id': 'ca_568', 'name': 'Form 568', 'description': 'Limited Liability Company Return of Income', 'deadline': 'April 15'},
                {'id': 'ca_3522', 'name': 'Form 3522', 'description': 'LLC Tax Voucher', 'deadline': 'April 15'}
            ],
            's_corp': [
                {'id': 'ca_100s', 'name': 'Form 100S', 'description': 'California S Corporation Franchise or Income Tax Return', 'deadline': 'March 15'}
            ],
            'c_corp': [
                {'id': 'ca_100', 'name': 'Form 100', 'description': 'California Corporation Franchise or Income Tax Return', 'deadline': 'April 15'}
            ],
            'partnership': [
                {'id': 'ca_565', 'name': 'Form 565', 'description': 'Partnership Return of Income', 'deadline': 'March 15'}
            ],
            'sales_tax': [
                {'id': 'ca_401', 'name': 'Form 401', 'description': 'State, Local, and District Sales and Use Tax Return', 'deadline': 'Monthly, Quarterly, or Annually'}
            ],
            'employment': [
                {'id': 'ca_de9', 'name': 'Form DE 9', 'description': 'Quarterly Contribution Return and Report of Wages', 'deadline': 'Monthly or Quarterly'}
            ]
        },
        'NY': {
            'sole_proprietor': [
                {'id': 'ny_it201', 'name': 'Form IT-201', 'description': 'Resident Income Tax Return', 'deadline': 'April 15'}
            ],
            'llc_single': [
                {'id': 'ny_it204', 'name': 'Form IT-204', 'description': 'Partnership Return', 'deadline': 'April 15'},
                {'id': 'ny_it204ll', 'name': 'Form IT-204-LL', 'description': 'Limited Liability Company/Limited Liability Partnership Filing Fee Payment Form', 'deadline': 'April 15'}
            ],
            'llc_multi': [
                {'id': 'ny_it204', 'name': 'Form IT-204', 'description': 'Partnership Return', 'deadline': 'April 15'},
                {'id': 'ny_it204ll', 'name': 'Form IT-204-LL', 'description': 'Limited Liability Company/Limited Liability Partnership Filing Fee Payment Form', 'deadline': 'April 15'}
            ],
            's_corp': [
                {'id': 'ny_ct3s', 'name': 'Form CT-3-S', 'description': 'New York S Corporation Franchise Tax Return', 'deadline': 'March 15'}
            ],
            'c_corp': [
                {'id': 'ny_ct3', 'name': 'Form CT-3', 'description': 'General Business Corporation Franchise Tax Return', 'deadline': 'April 15'}
            ],
            'partnership': [
                {'id': 'ny_it204', 'name': 'Form IT-204', 'description': 'Partnership Return', 'deadline': 'March 15'}
            ],
            'sales_tax': [
                {'id': 'ny_st100', 'name': 'Form ST-100', 'description': 'New York State and Local Quarterly Sales and Use Tax Return', 'deadline': 'Quarterly'}
            ],
            'employment': [
                {'id': 'ny_nys45', 'name': 'Form NYS-45', 'description': 'Quarterly Combined Withholding, Wage Reporting, and Unemployment Insurance Return', 'deadline': 'Quarterly'}
            ]
        },
        'TX': {
            'all': [
                {'id': 'tx_05158', 'name': 'Form 05-158', 'description': 'Texas Franchise Tax Report', 'deadline': 'May 15'}
            ],
            'sales_tax': [
                {'id': 'tx_01114', 'name': 'Form 01-114', 'description': 'Texas Sales and Use Tax Return', 'deadline': 'Monthly or Quarterly'}
            ],
            'employment': [
                {'id': 'tx_c3', 'name': 'Form C-3', 'description': 'Employer\'s Quarterly Report', 'deadline': 'Quarterly'}
            ]
        },
        'FL': {
            'c_corp': [
                {'id': 'fl_f1120', 'name': 'Form F-1120', 'description': 'Florida Corporate Income/Franchise Tax Return', 'deadline': 'May 1'}
            ],
            's_corp': [
                {'id': 'fl_f1120', 'name': 'Form F-1120', 'description': 'Florida Corporate Income/Franchise Tax Return', 'deadline': 'May 1'}
            ],
            'sales_tax': [
                {'id': 'fl_dr15', 'name': 'Form DR-15', 'description': 'Sales and Use Tax Return', 'deadline': 'Monthly or Quarterly'}
            ],
            'employment': [
                {'id': 'fl_rt6', 'name': 'Form RT-6', 'description': 'Employer\'s Quarterly Report', 'deadline': 'Quarterly'}
            ]
        }
    }
    
    # Add common state forms based on business type
    state_data = state_forms.get(state, {})
    
    # Add business-type-specific forms
    if business_type in state_data:
        for form in state_data[business_type]:
            forms.append(form)
    
    # Add forms that apply to all business types in that state
    if 'all' in state_data:
        for form in state_data['all']:
            forms.append(form)
    
    # Add sales tax forms if they have revenue (they might need to collect sales tax)
    if 'sales_tax' in state_data:
        forms.append({
            'id': f'{state.lower()}_sales_tax',
            'name': state_data['sales_tax'][0]['name'],
            'description': state_data['sales_tax'][0]['description'],
            'deadline': state_data['sales_tax'][0]['deadline'],
            'category': 'sales_tax',
            'note': 'Required if selling taxable goods or services'
        })
    
    # Add employment tax forms if they have employees
    if 'employment' in state_data:
        forms.append({
            'id': f'{state.lower()}_employment',
            'name': state_data['employment'][0]['name'],
            'description': state_data['employment'][0]['description'],
            'deadline': state_data['employment'][0]['deadline'],
            'category': 'employment',
            'note': 'Required if you have employees'
        })
    
    # If state isn't in our database, add a generic placeholder
    if not forms:
        forms.append({
            'id': f'{state.lower()}_business',
            'name': f'{state} Business Tax Forms',
            'description': f'Business tax forms for {state}',
            'deadline': 'Varies by state',
            'category': 'state',
            'note': 'Check with your state\'s department of revenue for specific requirements'
        })
    
    return forms