"""
Filing Guidance Module

This module provides smart, plain-English filing instructions tailored to the user's
specific form set, business type, state, and other contextual factors.
"""

from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app.app import db
from app.models import User, TaxForm, AuditLog, UserPlan
from app.access_control import requires_access_level
from ai.openai_interface import get_openai_response
import json
from datetime import datetime

# Create blueprint
filing_guidance_bp = Blueprint('filing_guidance', __name__, url_prefix='/filing-guidance')

@filing_guidance_bp.route('/')
@login_required
def index():
    """Display filing guidance homepage"""
    # Get user's forms and information
    user_forms = TaxForm.query.filter_by(user_id=current_user.id).all()
    
    # Get the tax year (default to current year if not specified)
    tax_year = request.args.get('tax_year', datetime.now().year, type=int)
    
    # Get filing instructions for the user's forms
    filing_instructions = generate_filing_instructions(current_user, user_forms, tax_year)
    
    # Get user's tier for conditional content
    user_tier = current_user.plan
    
    # Get audit shield summary for Pro users
    audit_shield_summary = None
    if user_tier == UserPlan.PRO:
        audit_shield_summary = generate_audit_shield_summary(current_user, user_forms, tax_year)
    
    return render_template('filing_guidance/index.html',
                          filing_instructions=filing_instructions,
                          audit_shield_summary=audit_shield_summary,
                          user_tier=user_tier,
                          tax_year=tax_year)

@filing_guidance_bp.route('/api/instructions')
@login_required
def api_instructions():
    """API endpoint to get filing instructions"""
    tax_year = request.args.get('tax_year', datetime.now().year, type=int)
    user_forms = TaxForm.query.filter_by(user_id=current_user.id, tax_year=tax_year).all()
    
    filing_instructions = generate_filing_instructions(current_user, user_forms, tax_year)
    
    return jsonify(filing_instructions)

@filing_guidance_bp.route('/api/audit-shield')
@login_required
@requires_access_level('audit_protection')
def api_audit_shield():
    """API endpoint to get audit shield summary"""
    tax_year = request.args.get('tax_year', datetime.now().year, type=int)
    user_forms = TaxForm.query.filter_by(user_id=current_user.id, tax_year=tax_year).all()
    
    audit_shield_summary = generate_audit_shield_summary(current_user, user_forms, tax_year)
    
    return jsonify(audit_shield_summary)

def generate_filing_instructions(user, forms, tax_year):
    """Generate plain-English filing instructions based on user's forms and business information"""
    # Extract business information and form data
    business_type = get_business_type(user, forms)
    state = get_business_state(user, forms)
    
    # Collect form info
    form_list = []
    for form in forms:
        if form.tax_year == tax_year:
            form_list.append({
                'form_type': form.form_type.value,
                'form_name': get_form_name(form.form_type.value),
                'status': form.status,
                'data': form.data
            })
    
    # Generate tailored filing instructions
    filing_methods = get_filing_methods(business_type, form_list, state)
    due_dates = get_due_dates(business_type, form_list, tax_year)
    penalty_info = get_penalty_information(business_type, form_list)
    ein_info = get_ein_verification_info(user, business_type)
    state_filing_info = get_state_filing_info(state, business_type, tax_year)
    
    # Compile all instructions
    instructions = {
        'business_type': business_type,
        'state': state,
        'tax_year': tax_year,
        'forms': form_list,
        'filing_methods': filing_methods,
        'due_dates': due_dates,
        'penalty_info': penalty_info,
        'ein_info': ein_info,
        'state_filing_info': state_filing_info,
        'step_by_step': generate_step_by_step_instructions(
            business_type, 
            state, 
            form_list, 
            filing_methods,
            due_dates,
            tax_year
        )
    }
    
    return instructions

def generate_audit_shield_summary(user, forms, tax_year):
    """Generate audit shield summary for Pro tier users"""
    # Extract business information and form data
    business_type = get_business_type(user, forms)
    state = get_business_state(user, forms)
    
    # Collect form info
    form_list = []
    for form in forms:
        if form.tax_year == tax_year:
            form_list.append({
                'form_type': form.form_type.value,
                'form_name': get_form_name(form.form_type.value),
                'status': form.status,
                'data': form.data
            })
    
    # Generate audit risk assessment
    audit_triggers = identify_audit_triggers(business_type, form_list, state)
    red_flags = identify_red_flags(business_type, form_list, state)
    audit_readiness = generate_audit_readiness_checklist(business_type, form_list)
    
    # Compile audit shield summary
    audit_shield_summary = {
        'business_type': business_type,
        'state': state,
        'tax_year': tax_year,
        'audit_risk_level': calculate_audit_risk_level(audit_triggers, red_flags),
        'audit_triggers': audit_triggers,
        'red_flags': red_flags,
        'audit_readiness_checklist': audit_readiness
    }
    
    return audit_shield_summary

def get_business_type(user, forms):
    """Extract business type from user data or forms"""
    # This would normally come from user profile or questionnaire data
    # For demo purposes, we'll return a placeholder
    return "sole_proprietor"

def get_business_state(user, forms):
    """Extract business state from user data or forms"""
    # This would normally come from user profile or questionnaire data
    # For demo purposes, we'll return a placeholder
    return "CA"

def get_form_name(form_type):
    """Get human-readable name for a form type"""
    form_names = {
        "1040": "Form 1040 - U.S. Individual Income Tax Return",
        "1120": "Form 1120 - U.S. Corporation Income Tax Return",
        "1120s": "Form 1120-S - U.S. Income Tax Return for an S Corporation",
        "1065": "Form 1065 - U.S. Return of Partnership Income",
        "schedule_c": "Schedule C - Profit or Loss From Business",
        "schedule_se": "Schedule SE - Self-Employment Tax",
        "4562": "Form 4562 - Depreciation and Amortization",
        "941": "Form 941 - Employer's Quarterly Federal Tax Return",
        "940": "Form 940 - Employer's Annual Federal Unemployment Tax Return",
        "w2": "Form W-2 - Wage and Tax Statement",
        "1099nec": "Form 1099-NEC - Nonemployee Compensation"
    }
    
    return form_names.get(form_type, f"Form {form_type}")

def get_filing_methods(business_type, forms, state):
    """Get available filing methods based on business type and forms"""
    # Determine available filing methods (e-file, mail, etc.)
    federal_methods = []
    state_methods = []
    
    # Federal filing methods
    for form in forms:
        form_type = form['form_type']
        
        if form_type in ['1040', 'schedule_c', 'schedule_se']:
            federal_methods.append({
                'method': 'e-file',
                'description': 'File electronically through IRS e-file',
                'url': 'https://www.irs.gov/e-file-providers/e-file-for-individuals',
                'steps': [
                    'Use IRS Free File if your income is below $73,000',
                    'Use commercial tax software that supports e-file',
                    'Find an authorized e-file provider'
                ]
            })
            federal_methods.append({
                'method': 'mail',
                'description': 'Mail paper forms to the IRS',
                'address': get_irs_mailing_address(business_type, state),
                'steps': [
                    'Print all required forms and schedules',
                    'Sign and date your return',
                    'Attach all required W-2s and other forms',
                    'Mail to the appropriate IRS address based on your location'
                ]
            })
        elif form_type in ['1120', '1120s', '1065']:
            federal_methods.append({
                'method': 'e-file',
                'description': 'File electronically through IRS e-file',
                'url': 'https://www.irs.gov/e-file-providers/e-file-for-businesses',
                'steps': [
                    'Use commercial tax software that supports business e-file',
                    'Find an authorized e-file provider that handles business returns',
                    'File through an online service provider'
                ]
            })
            federal_methods.append({
                'method': 'mail',
                'description': 'Mail paper forms to the IRS',
                'address': get_irs_mailing_address(business_type, state),
                'steps': [
                    'Print all required forms and schedules',
                    'Sign and date your return',
                    'Include all required schedules and attachments',
                    'Mail to the appropriate IRS address based on your location and business type'
                ]
            })
    
    # State filing methods
    state_methods.append({
        'method': 'e-file',
        'description': f'File electronically through {state} tax authority',
        'url': get_state_tax_website(state),
        'steps': [
            f'Visit the {state} tax authority website',
            'Register or log in to your account',
            'Select the appropriate forms for your business',
            'Follow the online instructions to complete and submit your return'
        ]
    })
    state_methods.append({
        'method': 'mail',
        'description': f'Mail paper forms to the {state} tax authority',
        'address': get_state_mailing_address(state, business_type),
        'steps': [
            'Print all required state tax forms',
            'Sign and date your return',
            'Include all required attachments',
            f'Mail to the appropriate {state} tax authority address'
        ]
    })
    
    # Remove duplicates
    federal_methods = {m['method']: m for m in federal_methods}.values()
    state_methods = {m['method']: m for m in state_methods}.values()
    
    return {
        'federal': list(federal_methods),
        'state': list(state_methods)
    }

def get_irs_mailing_address(business_type, state):
    """Get the appropriate IRS mailing address based on business type and state"""
    # This would normally come from a database of IRS mailing addresses
    # Simplified version for demo purposes
    if state in ['CA', 'AZ', 'NV', 'HI', 'OR', 'WA', 'AK']:
        return "Internal Revenue Service\nP.O. Box 7704\nSan Francisco, CA 94120-7704"
    else:
        return "Internal Revenue Service\nP.O. Box 931000\nLouisville, KY 40293-1000"

def get_state_tax_website(state):
    """Get the state tax website URL"""
    # This would normally come from a database of state tax websites
    # Simplified version for demo purposes
    state_websites = {
        'CA': 'https://www.ftb.ca.gov/',
        'NY': 'https://www.tax.ny.gov/',
        'TX': 'https://comptroller.texas.gov/taxes/',
        'FL': 'https://floridarevenue.com/taxes/'
    }
    
    return state_websites.get(state, f"https://www.google.com/search?q={state}+state+tax+website")

def get_state_mailing_address(state, business_type):
    """Get the state tax authority mailing address"""
    # This would normally come from a database of state tax mailing addresses
    # Simplified version for demo purposes
    state_addresses = {
        'CA': "Franchise Tax Board\nPO Box 942857\nSacramento, CA 94257-0500",
        'NY': "NYS Tax Department\nP.O. Box 15555\nAlbany, NY 12212-5555",
        'TX': "Texas Comptroller of Public Accounts\nP.O. Box 149348\nAustin, TX 78714-9348",
        'FL': "Florida Department of Revenue\nPO Box 6530\nTallahassee, FL 32314-6530"
    }
    
    return state_addresses.get(state, f"{state} Department of Revenue\n[Address depends on form and filing type]")

def get_due_dates(business_type, forms, tax_year):
    """Get filing due dates based on business type and forms"""
    # Federal due dates
    federal_dates = {}
    
    # Core filing dates based on business type
    if business_type in ['partnership', 'llc_multi', 's_corp']:
        federal_dates['primary'] = {
            'date': f"{tax_year}-03-15",
            'description': f"Filing deadline for {get_business_type_name(business_type)}",
            'extension_date': f"{tax_year}-09-15",
            'extension_form': "Form 7004"
        }
    elif business_type in ['c_corp']:
        federal_dates['primary'] = {
            'date': f"{tax_year}-04-15",
            'description': f"Filing deadline for {get_business_type_name(business_type)}",
            'extension_date': f"{tax_year}-10-15",
            'extension_form': "Form 7004"
        }
    else:  # sole_proprietor, llc_single
        federal_dates['primary'] = {
            'date': f"{tax_year}-04-15",
            'description': f"Filing deadline for {get_business_type_name(business_type)}",
            'extension_date': f"{tax_year}-10-15",
            'extension_form': "Form 4868"
        }
    
    # Additional form-specific dates
    for form in forms:
        form_type = form['form_type']
        
        if form_type in ['941']:
            federal_dates['941_q1'] = {
                'date': f"{tax_year}-04-30",
                'description': "Form 941 - Q1 deadline",
                'extension_date': None,
                'extension_form': None
            }
            federal_dates['941_q2'] = {
                'date': f"{tax_year}-07-31",
                'description': "Form 941 - Q2 deadline",
                'extension_date': None,
                'extension_form': None
            }
            federal_dates['941_q3'] = {
                'date': f"{tax_year}-10-31",
                'description': "Form 941 - Q3 deadline",
                'extension_date': None,
                'extension_form': None
            }
            federal_dates['941_q4'] = {
                'date': f"{tax_year + 1}-01-31",
                'description': "Form 941 - Q4 deadline",
                'extension_date': None,
                'extension_form': None
            }
        elif form_type in ['940']:
            federal_dates['940'] = {
                'date': f"{tax_year + 1}-01-31",
                'description': "Form 940 - Annual deadline",
                'extension_date': None,
                'extension_form': None
            }
        elif form_type in ['w2']:
            federal_dates['w2'] = {
                'date': f"{tax_year + 1}-01-31",
                'description': "Form W-2 - Employee copies and filing with SSA",
                'extension_date': None,
                'extension_form': None
            }
        elif form_type in ['1099nec']:
            federal_dates['1099nec'] = {
                'date': f"{tax_year + 1}-01-31",
                'description': "Form 1099-NEC - Recipient copies and filing with IRS",
                'extension_date': None,
                'extension_form': None
            }
    
    # State due dates (typically mirror federal, but can vary)
    state_dates = {}
    if business_type in ['partnership', 'llc_multi', 's_corp']:
        state_dates['primary'] = {
            'date': f"{tax_year}-03-15",
            'description': f"State filing deadline for {get_business_type_name(business_type)}",
            'extension_date': f"{tax_year}-09-15",
            'extension_form': "State extension form (varies by state)"
        }
    elif business_type in ['c_corp']:
        state_dates['primary'] = {
            'date': f"{tax_year}-04-15",
            'description': f"State filing deadline for {get_business_type_name(business_type)}",
            'extension_date': f"{tax_year}-10-15",
            'extension_form': "State extension form (varies by state)"
        }
    else:  # sole_proprietor, llc_single
        state_dates['primary'] = {
            'date': f"{tax_year}-04-15",
            'description': f"State filing deadline for {get_business_type_name(business_type)}",
            'extension_date': f"{tax_year}-10-15",
            'extension_form': "State extension form (varies by state)"
        }
    
    return {
        'federal': federal_dates,
        'state': state_dates
    }

def get_business_type_name(business_type):
    """Get human-readable business type name"""
    business_type_names = {
        'sole_proprietor': 'Sole Proprietorship',
        'llc_single': 'Single-Member LLC',
        'llc_multi': 'Multi-Member LLC',
        'partnership': 'Partnership',
        's_corp': 'S Corporation',
        'c_corp': 'C Corporation'
    }
    
    return business_type_names.get(business_type, business_type)

def get_penalty_information(business_type, forms):
    """Get penalty information for late filing and payment"""
    penalties = {
        'late_filing': {
            'description': 'Penalty for filing after the deadline',
            'rate': '5% of unpaid taxes for each month or part of a month the return is late, up to 25%',
            'minimum': 'The minimum penalty for a return filed more than 60 days late is $435 or 100% of the tax due, whichever is less'
        },
        'late_payment': {
            'description': 'Penalty for paying taxes after the deadline',
            'rate': '0.5% of unpaid taxes for each month or part of a month the payment is late, up to 25%',
            'notes': 'Even if you file for an extension, you still need to pay your estimated taxes by the original deadline to avoid this penalty'
        },
        'estimated_tax': {
            'description': 'Penalty for not paying enough estimated tax throughout the year',
            'calculation': 'Based on the federal short-term rate plus 3 percentage points, applied to underpayment amounts',
            'safe_harbor': 'You can avoid this penalty by paying at least 90% of this year\'s tax liability or 100% of last year\'s tax (110% if your AGI was over $150,000)'
        }
    }
    
    # Add form-specific penalties
    for form in forms:
        form_type = form['form_type']
        
        if form_type in ['941', '940']:
            penalties['employment_tax'] = {
                'description': 'Penalty for late filing or payment of employment taxes',
                'rate': 'From 2% to 15% depending on how late the payment is made',
                'notes': 'If both filing and payment are late, the combined penalty can be up to 47.5% of the unpaid tax'
            }
        elif form_type in ['1099nec']:
            penalties['information_returns'] = {
                'description': 'Penalty for late filing of information returns (1099s, W-2s)',
                'rate': 'From $50 to $280 per form, depending on how late the filing is made',
                'maximum': 'Maximum penalty of $3,392,000 per year ($1,131,000 for small businesses)'
            }
    
    return penalties

def get_ein_verification_info(user, business_type):
    """Get EIN verification information"""
    # Determine if the business needs an EIN
    needs_ein = business_type not in ['sole_proprietor']
    
    # Construct EIN information
    ein_info = {
        'required': needs_ein,
        'verification_url': 'https://sa.www4.irs.gov/modiein/individual/verification.jsp',
        'application_url': 'https://www.irs.gov/businesses/small-businesses-self-employed/apply-for-an-employer-identification-number-ein-online',
        'description': 'An Employer Identification Number (EIN) is required for most business types to file taxes',
        'steps': [
            'Verify your existing EIN by accessing the link above',
            'If you don\'t have an EIN, you can apply for one online',
            'The online application process takes about 15 minutes',
            'Once completed, you\'ll receive your EIN immediately'
        ]
    }
    
    return ein_info

def get_state_filing_info(state, business_type, tax_year):
    """Get state filing information"""
    # This would normally come from a database of state filing requirements
    # Simplified version for demo purposes
    state_info = {
        'CA': {
            'tax_authority': 'California Franchise Tax Board',
            'website': 'https://www.ftb.ca.gov/',
            'filing_portal': 'https://www.ftb.ca.gov/file/index.html',
            'forms': get_state_specific_forms('CA', business_type),
            'llc_fee': {
                'required': business_type in ['llc_single', 'llc_multi'],
                'description': 'California charges an annual LLC fee based on gross income',
                'amount': 'From $800 to $11,790 depending on gross income',
                'deadline': f"{tax_year}-04-15"
            }
        },
        'NY': {
            'tax_authority': 'New York State Department of Taxation and Finance',
            'website': 'https://www.tax.ny.gov/',
            'filing_portal': 'https://www.tax.ny.gov/online/',
            'forms': get_state_specific_forms('NY', business_type),
            'publication_20': {
                'description': 'NY Publication 20 provides a guide for new businesses',
                'url': 'https://www.tax.ny.gov/pdf/publications/multi/pub20.pdf'
            }
        },
        'TX': {
            'tax_authority': 'Texas Comptroller of Public Accounts',
            'website': 'https://comptroller.texas.gov/taxes/',
            'filing_portal': 'https://comptroller.texas.gov/taxes/file-pay/',
            'forms': get_state_specific_forms('TX', business_type),
            'franchise_tax': {
                'required': business_type in ['llc_single', 'llc_multi', 'c_corp', 's_corp'],
                'description': 'Texas franchise tax applies to entities formed in Texas or doing business in Texas',
                'deadline': f"{tax_year}-05-15"
            }
        },
        'FL': {
            'tax_authority': 'Florida Department of Revenue',
            'website': 'https://floridarevenue.com/taxes/',
            'filing_portal': 'https://floridarevenue.com/taxes/eservices/',
            'forms': get_state_specific_forms('FL', business_type),
            'no_income_tax': {
                'description': 'Florida does not have a personal income tax',
                'business_tax': 'Florida does have a corporate income tax for C and S corporations'
            }
        }
    }
    
    # Default state info if not in our database
    if state not in state_info:
        return {
            'tax_authority': f'{state} Department of Revenue',
            'website': f'https://www.google.com/search?q={state}+department+of+revenue',
            'note': f'Please check the {state} Department of Revenue website for specific filing requirements'
        }
    
    return state_info.get(state)

def get_state_specific_forms(state, business_type):
    """Get state-specific tax forms"""
    # This would normally come from a database of state tax forms
    # Simplified version for demo purposes
    state_forms = {
        'CA': {
            'sole_proprietor': ['Form 540', 'Schedule CA'],
            'llc_single': ['Form 568', 'Form 3522'],
            'llc_multi': ['Form 568', 'Form 3522'],
            's_corp': ['Form 100S'],
            'c_corp': ['Form 100'],
            'partnership': ['Form 565']
        },
        'NY': {
            'sole_proprietor': ['Form IT-201', 'Form IT-204-LL'],
            'llc_single': ['Form IT-204', 'Form IT-204-LL'],
            'llc_multi': ['Form IT-204', 'Form IT-204-LL'],
            's_corp': ['Form CT-3-S'],
            'c_corp': ['Form CT-3'],
            'partnership': ['Form IT-204']
        },
        'TX': {
            'sole_proprietor': [],  # No state income tax for individuals
            'llc_single': ['Form 05-158-A'],
            'llc_multi': ['Form 05-158-A'],
            's_corp': ['Form 05-158-A'],
            'c_corp': ['Form 05-158-A'],
            'partnership': ['Form 05-158-A']
        },
        'FL': {
            'sole_proprietor': [],  # No state income tax for individuals
            'llc_single': [],  # No state income tax for individuals
            'llc_multi': [],  # No state income tax for individuals
            's_corp': ['Form F-1120'],
            'c_corp': ['Form F-1120'],
            'partnership': []  # No state income tax for individuals
        }
    }
    
    if state not in state_forms or business_type not in state_forms[state]:
        return []
    
    # Convert form IDs to form objects
    forms = []
    for form_id in state_forms[state][business_type]:
        forms.append({
            'id': form_id,
            'name': form_id,
            'description': f'{state} {form_id}'
        })
    
    return forms

def generate_step_by_step_instructions(business_type, state, forms, filing_methods, due_dates, tax_year):
    """Generate step-by-step filing instructions"""
    # Create a unified set of steps
    steps = []
    
    # Step 1: Verify information
    steps.append({
        'number': 1,
        'title': 'Verify Your Information',
        'description': 'Ensure all your business and tax information is correct',
        'substeps': [
            'Verify your business name, address, and contact information',
            'Confirm your EIN (if applicable)',
            'Check that all income and expense information is accurate',
            'Ensure all required forms are completed'
        ]
    })
    
    # Step 2: Choose Filing Method
    steps.append({
        'number': 2,
        'title': 'Choose Your Filing Method',
        'description': 'Decide whether to e-file or mail your returns',
        'substeps': [
            'E-filing is generally faster, more secure, and provides confirmation of receipt',
            'Paper filing may be necessary for certain forms or attachments',
            'If e-filing, you\'ll need to select tax software or an e-file provider',
            'If paper filing, you\'ll need to print all required forms and schedules'
        ]
    })
    
    # Step 3: Federal Filing
    federal_method = 'e-file' if any(m['method'] == 'e-file' for m in filing_methods['federal']) else 'mail'
    federal_deadline = due_dates['federal']['primary']['date']
    
    if federal_method == 'e-file':
        steps.append({
            'number': 3,
            'title': 'File Your Federal Return',
            'description': f'E-file your federal return by {federal_deadline}',
            'substeps': [
                'Select an IRS-approved e-file provider or tax software',
                'Follow the software\'s instructions to complete your return',
                'Submit your return electronically',
                'Print and keep a copy of your return for your records',
                'Pay any taxes due electronically (Direct debit from your e-file, EFTPS, IRS Direct Pay, or credit/debit card)'
            ]
        })
    else:
        steps.append({
            'number': 3,
            'title': 'File Your Federal Return',
            'description': f'Mail your federal return by {federal_deadline}',
            'substeps': [
                'Print all required forms and schedules',
                'Sign and date your return',
                'Include all required attachments (W-2s, 1099s, etc.)',
                'Make a copy of your complete return for your records',
                f'Mail your return to: {get_irs_mailing_address(business_type, state)}',
                'Pay any taxes due (Check or money order, or pay electronically via EFTPS, IRS Direct Pay, or credit/debit card)'
            ]
        })
    
    # Step 4: State Filing
    if state in ['CA', 'NY', 'TX', 'FL']:
        state_method = 'e-file' if any(m['method'] == 'e-file' for m in filing_methods['state']) else 'mail'
        state_deadline = due_dates['state']['primary']['date']
        state_info = get_state_filing_info(state, business_type, tax_year)
        
        if state_method == 'e-file':
            steps.append({
                'number': 4,
                'title': 'File Your State Return',
                'description': f'E-file your {state} return by {state_deadline}',
                'substeps': [
                    f'Visit the {state} tax filing portal: {state_info["filing_portal"]}',
                    'Log in or create an account',
                    'Follow the instructions to complete your state return',
                    'Submit your return electronically',
                    'Print and keep a copy of your return for your records',
                    'Pay any taxes due electronically through the state portal'
                ]
            })
        else:
            steps.append({
                'number': 4,
                'title': 'File Your State Return',
                'description': f'Mail your {state} return by {state_deadline}',
                'substeps': [
                    'Print all required state forms',
                    'Sign and date your return',
                    'Include all required attachments',
                    'Make a copy of your complete return for your records',
                    f'Mail your return to: {get_state_mailing_address(state, business_type)}',
                    'Pay any taxes due according to state instructions'
                ]
            })
    
    # Step 5: Keep Records
    steps.append({
        'number': 5,
        'title': 'Keep Records of Your Filing',
        'description': 'Maintain proper documentation of your tax filing',
        'substeps': [
            'Save electronic copies of all filed returns',
            'Keep paper copies in a secure location',
            'Save your e-file confirmation or mailing receipt',
            'Keep records of all tax payments',
            'Organize and save all supporting documentation',
            'Keep tax records for at least 7 years'
        ]
    })
    
    # Step 6: Follow Up (if needed)
    steps.append({
        'number': 6,
        'title': 'Follow Up As Needed',
        'description': 'Be prepared to respond to notices or requests',
        'substeps': [
            'Track your refund if applicable',
            'Respond promptly to any IRS or state tax notices',
            'Consider setting reminders for quarterly estimated taxes if required',
            'Note the deadline for filing an amended return if errors are discovered'
        ]
    })
    
    return steps

def identify_audit_triggers(business_type, forms, state):
    """Identify potential audit triggers based on business type and forms"""
    # This would normally use AI to analyze specific form data
    # For demo purposes, we'll return common audit triggers
    common_triggers = [
        {
            'trigger': 'Home Office Deduction',
            'description': 'Taking a home office deduction increases audit risk, especially if the amount is large relative to income',
            'risk_level': 'Medium',
            'mitigation': 'Ensure you have proper documentation and that the space is exclusively used for business'
        },
        {
            'trigger': 'High Business Expenses',
            'description': 'Business expenses that are high relative to income may trigger an audit',
            'risk_level': 'Medium-High',
            'mitigation': 'Keep detailed records of all expenses and ensure they are ordinary and necessary for your business'
        },
        {
            'trigger': 'Vehicle Expenses',
            'description': 'Vehicle expenses, especially when claiming 100% business use, are frequently examined',
            'risk_level': 'Medium',
            'mitigation': 'Maintain a detailed mileage log with dates, destinations, and business purposes'
        }
    ]
    
    # Add business-type-specific triggers
    if business_type == 'sole_proprietor':
        common_triggers.append({
            'trigger': 'Schedule C Income',
            'description': 'Sole proprietors with Schedule C income above $100,000 face increased scrutiny',
            'risk_level': 'Medium-High',
            'mitigation': 'Ensure all income is properly reported and maintain excellent documentation for all deductions'
        })
    elif business_type in ['llc_single', 'llc_multi']:
        common_triggers.append({
            'trigger': 'LLC Classification',
            'description': 'LLCs that switch tax classifications may face additional scrutiny',
            'risk_level': 'Medium',
            'mitigation': 'Ensure proper filing of Form 8832 if changing entity classification'
        })
    elif business_type == 's_corp':
        common_triggers.append({
            'trigger': 'Shareholder Compensation',
            'description': 'S-corporation shareholders who take low salaries and high distributions may trigger audits',
            'risk_level': 'High',
            'mitigation': 'Ensure shareholder-employees receive reasonable compensation for services rendered'
        })
    
    # Add form-specific triggers
    for form in forms:
        form_type = form['form_type']
        
        if form_type == 'schedule_c':
            common_triggers.append({
                'trigger': 'Round Numbers',
                'description': 'Reporting expenses in round numbers (e.g., $5,000 exactly) suggests estimation rather than actual records',
                'risk_level': 'Medium',
                'mitigation': 'Report actual expense amounts from your records, not estimates'
            })
        elif form_type in ['941', '940']:
            common_triggers.append({
                'trigger': 'Employment Tax Discrepancies',
                'description': 'Discrepancies between employment tax forms and W-2/1099 forms may trigger an audit',
                'risk_level': 'High',
                'mitigation': 'Reconcile all employment tax forms before filing to ensure consistency'
            })
    
    return common_triggers

def identify_red_flags(business_type, forms, state):
    """Identify potential red flags that might attract IRS attention"""
    # This would normally use AI to analyze specific form data
    # For demo purposes, we'll return common red flags
    red_flags = []
    
    # Add general red flags
    red_flags.append({
        'flag': 'Income Omission',
        'description': 'Failing to report all income, especially when the IRS has received 1099s or other information returns',
        'risk_level': 'Critical',
        'detection': 'IRS computer systems automatically match reported income with information returns'
    })
    
    red_flags.append({
        'flag': 'Consistency Issues',
        'description': 'Inconsistencies between different forms or between federal and state returns',
        'risk_level': 'High',
        'detection': 'IRS and state tax authorities share information and can detect discrepancies'
    })
    
    # Add business-type-specific red flags
    if business_type == 'sole_proprietor':
        if has_high_schedule_c_deductions(forms):
            red_flags.append({
                'flag': 'High Schedule C Deductions',
                'description': 'Schedule C with deductions that significantly reduce taxable income',
                'risk_level': 'High',
                'detection': 'IRS uses DIF scores to compare your deductions to norms for your industry and income level'
            })
        
        if has_consecutive_schedule_c_losses(forms):
            red_flags.append({
                'flag': 'Multiple Years of Losses',
                'description': 'Reporting business losses for multiple consecutive years',
                'risk_level': 'High',
                'detection': 'May trigger a hobby loss audit where the IRS challenges whether your activity is a business or hobby'
            })
    
    # Add form-specific red flags
    for form in forms:
        form_type = form['form_type']
        
        if form_type == '1099nec':
            red_flags.append({
                'flag': 'Worker Misclassification',
                'description': 'Treating workers as contractors (1099-NEC) when they should be employees (W-2)',
                'risk_level': 'Critical',
                'detection': 'IRS and Department of Labor actively look for worker misclassification'
            })
    
    # State-specific red flags
    if state == 'CA':
        red_flags.append({
            'flag': 'California Residency Issues',
            'description': 'Claiming non-residency or partial-year residency in California while maintaining ties to the state',
            'risk_level': 'High',
            'detection': 'California FTB aggressively pursues residency audits'
        })
    
    return red_flags

def has_high_schedule_c_deductions(forms):
    """Check if Schedule C has high deductions relative to income"""
    # This would normally analyze actual form data
    # For demo purposes, we'll return a placeholder value
    return True

def has_consecutive_schedule_c_losses(forms):
    """Check if Schedule C has losses for consecutive years"""
    # This would normally analyze actual form data across multiple years
    # For demo purposes, we'll return a placeholder value
    return False

def calculate_audit_risk_level(audit_triggers, red_flags):
    """Calculate overall audit risk level based on triggers and red flags"""
    # Count high and critical risk items
    high_risk_count = sum(1 for trigger in audit_triggers if trigger['risk_level'] in ['High', 'Medium-High'])
    high_risk_count += sum(1 for flag in red_flags if flag['risk_level'] in ['High'])
    critical_risk_count = sum(1 for flag in red_flags if flag['risk_level'] == 'Critical')
    
    # Determine overall risk level
    if critical_risk_count > 0:
        return "High"
    elif high_risk_count > 2:
        return "Medium-High"
    elif high_risk_count > 0:
        return "Medium"
    else:
        return "Low"

def generate_audit_readiness_checklist(business_type, forms):
    """Generate audit readiness checklist"""
    # Common checklist items for all business types
    checklist = [
        {
            'category': 'Record Keeping',
            'items': [
                'Organize all receipts and invoices by category',
                'Maintain a separate business bank account and credit card',
                'Keep records of all business transactions for at least 7 years',
                'Document business purpose for all travel, meal, and entertainment expenses',
                'Maintain a mileage log if claiming vehicle expenses'
            ]
        },
        {
            'category': 'Documentation',
            'items': [
                'Retain copies of all filed tax returns and schedules',
                'Keep copies of all 1099s, W-2s, and other information returns',
                'Maintain documentation for all business deductions',
                'Keep records of all asset purchases and depreciation schedules',
                'Document all business-related transactions with clear business purpose'
            ]
        },
        {
            'category': 'Compliance',
            'items': [
                'File all required tax returns on time',
                'Pay all tax obligations by their due dates',
                'Respond promptly to any IRS or state tax notices',
                'Keep records of all tax payments and confirmations',
                'Ensure consistency between federal and state tax filings'
            ]
        }
    ]
    
    # Add business-type-specific checklist items
    if business_type in ['sole_proprietor', 'llc_single']:
        checklist.append({
            'category': 'Self-Employment Considerations',
            'items': [
                'Keep detailed records of all business income, including cash payments',
                'Document home office expenses and measurements if claiming deduction',
                'Track all business miles if claiming vehicle expenses',
                'Maintain documentation for health insurance premiums and retirement contributions',
                'Document any business losses with evidence of profit motive'
            ]
        })
    elif business_type in ['s_corp', 'c_corp']:
        checklist.append({
            'category': 'Corporate Considerations',
            'items': [
                'Maintain corporate meeting minutes and resolutions',
                'Document all shareholder transactions and distributions',
                'Ensure reasonable compensation for shareholder-employees',
                'Maintain clear separation between personal and business expenses',
                'Document all related-party transactions with proper valuation'
            ]
        })
    
    # Add form-specific checklist items
    has_employment_forms = any(form['form_type'] in ['941', '940', 'w2'] for form in forms)
    if has_employment_forms:
        checklist.append({
            'category': 'Employment Tax Considerations',
            'items': [
                'Maintain records of all employee wages and withholdings',
                'Keep documentation of contractor vs. employee status determinations',
                'Retain copies of all filed employment tax returns',
                'Document all employee benefits and perks',
                'Maintain records of employment tax deposits and payments'
            ]
        })
    
    return checklist