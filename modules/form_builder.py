"""
Form Builder Module

This module provides dynamic form building capabilities for tax forms
based on business type, entity structure, and other parameters.
"""

from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app.app import db
from app.models import TaxForm, User, UserPlan, TaxFormType
from app.access_control import requires_access_level
import json
from datetime import datetime

# Create blueprint
form_builder_bp = Blueprint('form_builder', __name__, url_prefix='/form-builder')

@form_builder_bp.route('/select-form')
@login_required
def select_form():
    """Select a tax form to build"""
    # Get form categories
    form_categories = get_form_categories()
    
    # Check user's access level
    user_tier = current_user.plan
    has_access_to_full_library = user_tier in [UserPlan.FYLR_PLUS, UserPlan.PRO]
    
    return render_template('form_builder/select_form.html',
                          form_categories=form_categories,
                          has_access_to_full_library=has_access_to_full_library)

@form_builder_bp.route('/form/<form_type>')
@login_required
def build_form(form_type):
    """Build a specific tax form"""
    # Check if the form exists
    try:
        form_enum = TaxFormType[form_type.upper()]
    except KeyError:
        flash(f"The form type '{form_type}' is not supported.", "danger")
        return redirect(url_for('form_builder.select_form'))
    
    # Check if the form requires upgraded access
    if requires_upgraded_access(form_type):
        if current_user.plan == UserPlan.BASIC:
            return render_template('form_builder/upgrade_required.html', 
                                  form_type=form_type,
                                  form_name=get_form_display_name(form_type))
    
    # Get form metadata
    form_metadata = get_form_metadata(form_type)
    
    # Get form schema
    form_schema = get_form_schema(form_type)
    
    # Get existing form data if editing
    existing_form_id = request.args.get('form_id')
    existing_form_data = None
    
    if existing_form_id:
        existing_form = TaxForm.query.filter_by(id=existing_form_id, user_id=current_user.id).first()
        if existing_form:
            existing_form_data = existing_form.data
    
    # Get business context
    business_type = request.args.get('business_type', 'sole_proprietor')
    tax_year = request.args.get('tax_year', datetime.now().year, type=int)
    
    return render_template('form_builder/build_form.html',
                          form_type=form_type,
                          form_name=form_metadata.get('name'),
                          form_description=form_metadata.get('description'),
                          form_schema=form_schema,
                          existing_form_data=existing_form_data,
                          business_type=business_type,
                          tax_year=tax_year,
                          existing_form_id=existing_form_id)

@form_builder_bp.route('/save-form', methods=['POST'])
@login_required
def save_form():
    """Save a completed form"""
    form_data = request.get_json()
    
    # Extract form metadata
    form_type_str = form_data.pop('form_type')
    tax_year = form_data.pop('tax_year', datetime.now().year)
    existing_form_id = form_data.pop('form_id', None)
    
    try:
        form_type = TaxFormType[form_type_str.upper()]
    except KeyError:
        return jsonify({'success': False, 'error': f"Invalid form type: {form_type_str}"}), 400
    
    # Save or update the form
    if existing_form_id:
        # Update existing form
        form = TaxForm.query.filter_by(id=existing_form_id, user_id=current_user.id).first()
        if not form:
            return jsonify({'success': False, 'error': "Form not found"}), 404
        
        form.data = form_data
        form.updated_at = datetime.utcnow()
    else:
        # Create new form
        form = TaxForm(
            user_id=current_user.id,
            form_type=form_type,
            tax_year=tax_year,
            data=form_data,
            status='draft'
        )
        db.session.add(form)
    
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'form_id': form.id,
        'message': f"Form {form_type.value} successfully saved."
    })

@form_builder_bp.route('/api/form-schema/<form_type>')
@login_required
def api_form_schema(form_type):
    """API endpoint to get a form schema"""
    try:
        form_enum = TaxFormType[form_type.upper()]
    except KeyError:
        return jsonify({'error': f"The form type '{form_type}' is not supported."}), 400
    
    # Get form schema
    form_schema = get_form_schema(form_type)
    
    return jsonify(form_schema)

@form_builder_bp.route('/api/field-help', methods=['POST'])
@login_required
@requires_access_level('smart_form_logic')
def api_field_help():
    """API endpoint to get AI-guided help for a specific form field"""
    data = request.get_json()
    
    form_type = data.get('form_type')
    field_name = data.get('field_name')
    business_context = data.get('business_context', {})
    tax_year = data.get('tax_year', datetime.now().year)
    
    # In a real implementation, this would use AI to generate context-aware help
    # For prototype purposes, we return pre-defined help text
    field_help = get_field_help(form_type, field_name, business_context, tax_year)
    
    return jsonify({'help_text': field_help})

def get_form_categories():
    """Get available form categories"""
    categories = {
        'core': {
            'name': 'Core Business Tax Forms',
            'description': 'Primary tax forms for reporting business income and expenses',
            'forms': [
                {
                    'id': 'schedule_c', 
                    'name': 'Schedule C', 
                    'full_name': 'Profit or Loss From Business',
                    'description': 'Used by sole proprietors and single-member LLCs to report business income and expenses',
                    'business_types': ['sole_proprietor', 'llc_single'],
                    'complexity': 'medium',
                    'requires_upgrade': False
                },
                {
                    'id': '1065', 
                    'name': 'Form 1065', 
                    'full_name': 'U.S. Return of Partnership Income',
                    'description': 'Used by partnerships and multi-member LLCs to report income, deductions, gains, and losses',
                    'business_types': ['partnership', 'llc_multi'],
                    'complexity': 'high',
                    'requires_upgrade': True
                },
                {
                    'id': '1120s', 
                    'name': 'Form 1120-S', 
                    'full_name': 'U.S. Income Tax Return for an S Corporation',
                    'description': 'Used by S corporations to report income, losses, and dividends distributed to shareholders',
                    'business_types': ['s_corp'],
                    'complexity': 'high',
                    'requires_upgrade': True
                },
                {
                    'id': '1120', 
                    'name': 'Form 1120', 
                    'full_name': 'U.S. Corporation Income Tax Return',
                    'description': 'Used by C corporations to report income, gains, losses, deductions, and credits',
                    'business_types': ['c_corp'],
                    'complexity': 'high',
                    'requires_upgrade': True
                }
            ]
        },
        'supplemental': {
            'name': 'Supplemental Forms & Schedules',
            'description': 'Additional forms required for specific business situations',
            'forms': [
                {
                    'id': 'schedule_se', 
                    'name': 'Schedule SE', 
                    'full_name': 'Self-Employment Tax',
                    'description': 'Used to calculate self-employment tax for business owners',
                    'business_types': ['sole_proprietor', 'llc_single'],
                    'complexity': 'low',
                    'requires_upgrade': False
                },
                {
                    'id': '4562', 
                    'name': 'Form 4562', 
                    'full_name': 'Depreciation and Amortization',
                    'description': 'Used to claim depreciation and amortization deductions, and the section 179 expense deduction',
                    'business_types': ['sole_proprietor', 'llc_single', 'partnership', 'llc_multi', 's_corp', 'c_corp'],
                    'complexity': 'medium',
                    'requires_upgrade': False
                },
                {
                    'id': '8825', 
                    'name': 'Form 8825', 
                    'full_name': 'Rental Real Estate Income and Expenses of a Partnership or an S Corporation',
                    'description': 'Used to report rental real estate income and expenses for partnerships and S corporations',
                    'business_types': ['partnership', 'llc_multi', 's_corp'],
                    'complexity': 'medium',
                    'requires_upgrade': True
                },
                {
                    'id': '8832', 
                    'name': 'Form 8832', 
                    'full_name': 'Entity Classification Election',
                    'description': 'Used to elect how an entity is classified for federal tax purposes',
                    'business_types': ['llc_single', 'llc_multi'],
                    'complexity': 'medium',
                    'requires_upgrade': True
                },
                {
                    'id': '2553', 
                    'name': 'Form 2553', 
                    'full_name': 'Election by a Small Business Corporation',
                    'description': 'Used to elect S corporation status for a corporation',
                    'business_types': ['llc_single', 'llc_multi', 'c_corp'],
                    'complexity': 'medium',
                    'requires_upgrade': True
                }
            ]
        },
        'employment': {
            'name': 'Employment Tax Forms',
            'description': 'Forms related to employment taxes and reporting',
            'forms': [
                {
                    'id': '941', 
                    'name': 'Form 941', 
                    'full_name': 'Employer\'s Quarterly Federal Tax Return',
                    'description': 'Used to report income taxes, Social Security tax, and Medicare tax withheld from employee wages',
                    'business_types': ['sole_proprietor', 'llc_single', 'partnership', 'llc_multi', 's_corp', 'c_corp'],
                    'complexity': 'medium',
                    'requires_upgrade': True
                },
                {
                    'id': '940', 
                    'name': 'Form 940', 
                    'full_name': 'Employer\'s Annual Federal Unemployment (FUTA) Tax Return',
                    'description': 'Used to report annual Federal Unemployment Tax Act (FUTA) tax',
                    'business_types': ['sole_proprietor', 'llc_single', 'partnership', 'llc_multi', 's_corp', 'c_corp'],
                    'complexity': 'medium',
                    'requires_upgrade': True
                },
                {
                    'id': 'w2', 
                    'name': 'Form W-2', 
                    'full_name': 'Wage and Tax Statement',
                    'description': 'Used to report wages, tips, and other compensation paid to employees',
                    'business_types': ['sole_proprietor', 'llc_single', 'partnership', 'llc_multi', 's_corp', 'c_corp'],
                    'complexity': 'medium',
                    'requires_upgrade': True
                },
                {
                    'id': 'w3', 
                    'name': 'Form W-3', 
                    'full_name': 'Transmittal of Wage and Tax Statements',
                    'description': 'Used to transmit W-2 forms to the SSA',
                    'business_types': ['sole_proprietor', 'llc_single', 'partnership', 'llc_multi', 's_corp', 'c_corp'],
                    'complexity': 'low',
                    'requires_upgrade': True
                }
            ]
        },
        'information': {
            'name': 'Information Returns',
            'description': 'Forms for reporting payments to contractors and other non-employees',
            'forms': [
                {
                    'id': '1099nec', 
                    'name': 'Form 1099-NEC', 
                    'full_name': 'Nonemployee Compensation',
                    'description': 'Used to report payments to nonemployees for services performed',
                    'business_types': ['sole_proprietor', 'llc_single', 'partnership', 'llc_multi', 's_corp', 'c_corp'],
                    'complexity': 'low',
                    'requires_upgrade': False
                },
                {
                    'id': '1099misc', 
                    'name': 'Form 1099-MISC', 
                    'full_name': 'Miscellaneous Information',
                    'description': 'Used to report miscellaneous payments such as rent, prizes, awards, etc.',
                    'business_types': ['sole_proprietor', 'llc_single', 'partnership', 'llc_multi', 's_corp', 'c_corp'],
                    'complexity': 'low',
                    'requires_upgrade': True
                },
                {
                    'id': '1096', 
                    'name': 'Form 1096', 
                    'full_name': 'Annual Summary and Transmittal of U.S. Information Returns',
                    'description': 'Used to transmit paper Forms 1099 to the IRS',
                    'business_types': ['sole_proprietor', 'llc_single', 'partnership', 'llc_multi', 's_corp', 'c_corp'],
                    'complexity': 'low',
                    'requires_upgrade': True
                }
            ]
        },
        'state': {
            'name': 'State Tax Forms',
            'description': 'State-specific tax forms for businesses',
            'forms': [
                {
                    'id': 'ca_540', 
                    'name': 'CA Form 540', 
                    'full_name': 'California Resident Income Tax Return',
                    'description': 'Used by California residents to report state income tax',
                    'business_types': ['sole_proprietor', 'llc_single'],
                    'complexity': 'medium',
                    'requires_upgrade': True
                },
                {
                    'id': 'ca_568', 
                    'name': 'CA Form 568', 
                    'full_name': 'Limited Liability Company Return of Income',
                    'description': 'Used by LLCs doing business in California',
                    'business_types': ['llc_single', 'llc_multi'],
                    'complexity': 'medium',
                    'requires_upgrade': True
                },
                {
                    'id': 'ca_100s', 
                    'name': 'CA Form 100S', 
                    'full_name': 'California S Corporation Franchise or Income Tax Return',
                    'description': 'Used by S corporations doing business in California',
                    'business_types': ['s_corp'],
                    'complexity': 'high',
                    'requires_upgrade': True
                },
                {
                    'id': 'ny_it201', 
                    'name': 'NY Form IT-201', 
                    'full_name': 'New York Resident Income Tax Return',
                    'description': 'Used by New York residents to report state income tax',
                    'business_types': ['sole_proprietor', 'llc_single'],
                    'complexity': 'medium',
                    'requires_upgrade': True
                },
                {
                    'id': 'ny_ct3', 
                    'name': 'NY Form CT-3', 
                    'full_name': 'New York General Business Corporation Franchise Tax Return',
                    'description': 'Used by corporations doing business in New York',
                    'business_types': ['c_corp'],
                    'complexity': 'high',
                    'requires_upgrade': True
                }
            ]
        }
    }
    
    return categories

def get_form_metadata(form_type):
    """Get metadata for a specific form"""
    # Iterate through all categories to find the form
    for category in get_form_categories().values():
        for form in category['forms']:
            if form['id'] == form_type:
                return form
    
    # Default metadata if form not found
    return {
        'name': form_type.upper(),
        'full_name': 'Tax Form',
        'description': 'No description available',
        'business_types': [],
        'complexity': 'medium',
        'requires_upgrade': False
    }

def get_form_display_name(form_type):
    """Get a display name for a form"""
    metadata = get_form_metadata(form_type)
    return f"{metadata['name']} - {metadata['full_name']}"

def requires_upgraded_access(form_type):
    """Check if a form requires upgraded access"""
    metadata = get_form_metadata(form_type)
    return metadata.get('requires_upgrade', False)

def get_form_schema(form_type):
    """Get the form schema for a specific form type"""
    # In a real implementation, this would load from a database or file
    # For prototype purposes, we'll return hardcoded schemas for a few common forms
    
    if form_type == 'schedule_c':
        return {
            'title': 'Schedule C - Profit or Loss From Business',
            'sections': [
                {
                    'id': 'business_info',
                    'title': 'Business Information',
                    'fields': [
                        {
                            'id': 'business_name',
                            'label': 'Business Name',
                            'type': 'text',
                            'required': True,
                            'placeholder': 'Enter your business name'
                        },
                        {
                            'id': 'business_code',
                            'label': 'Business Code',
                            'type': 'text',
                            'required': True,
                            'placeholder': 'Enter 6-digit business code',
                            'help_text': 'Enter the 6-digit code from the Business Code List in the Schedule C instructions'
                        },
                        {
                            'id': 'ein',
                            'label': 'Employer ID Number (EIN)',
                            'type': 'text',
                            'required': False,
                            'placeholder': 'XX-XXXXXXX',
                            'help_text': 'If you have an EIN, enter it here'
                        },
                        {
                            'id': 'business_address',
                            'label': 'Business Address',
                            'type': 'textarea',
                            'required': True,
                            'placeholder': 'Enter your business address'
                        },
                        {
                            'id': 'accounting_method',
                            'label': 'Accounting Method',
                            'type': 'select',
                            'required': True,
                            'options': [
                                {'value': 'cash', 'label': 'Cash'},
                                {'value': 'accrual', 'label': 'Accrual'},
                                {'value': 'other', 'label': 'Other'}
                            ],
                            'help_text': 'Most small businesses use the cash method'
                        }
                    ]
                },
                {
                    'id': 'income',
                    'title': 'Income',
                    'fields': [
                        {
                            'id': 'gross_receipts',
                            'label': 'Gross receipts or sales',
                            'type': 'currency',
                            'required': True,
                            'placeholder': '0.00'
                        },
                        {
                            'id': 'returns_allowances',
                            'label': 'Returns and allowances',
                            'type': 'currency',
                            'required': False,
                            'placeholder': '0.00'
                        },
                        {
                            'id': 'other_income',
                            'label': 'Other business income',
                            'type': 'currency',
                            'required': False,
                            'placeholder': '0.00'
                        }
                    ]
                },
                {
                    'id': 'expenses',
                    'title': 'Expenses',
                    'fields': [
                        {
                            'id': 'advertising',
                            'label': 'Advertising',
                            'type': 'currency',
                            'required': False,
                            'placeholder': '0.00'
                        },
                        {
                            'id': 'car_expenses',
                            'label': 'Car and truck expenses',
                            'type': 'currency',
                            'required': False,
                            'placeholder': '0.00'
                        },
                        {
                            'id': 'commissions',
                            'label': 'Commissions and fees',
                            'type': 'currency',
                            'required': False,
                            'placeholder': '0.00'
                        },
                        {
                            'id': 'contract_labor',
                            'label': 'Contract labor',
                            'type': 'currency',
                            'required': False,
                            'placeholder': '0.00'
                        },
                        {
                            'id': 'depletion',
                            'label': 'Depletion',
                            'type': 'currency',
                            'required': False,
                            'placeholder': '0.00'
                        },
                        {
                            'id': 'depreciation',
                            'label': 'Depreciation and Section 179 expense',
                            'type': 'currency',
                            'required': False,
                            'placeholder': '0.00'
                        },
                        {
                            'id': 'employee_benefits',
                            'label': 'Employee benefit programs',
                            'type': 'currency',
                            'required': False,
                            'placeholder': '0.00'
                        },
                        {
                            'id': 'insurance',
                            'label': 'Insurance (other than health)',
                            'type': 'currency',
                            'required': False,
                            'placeholder': '0.00'
                        },
                        {
                            'id': 'interest_mortgage',
                            'label': 'Interest - Mortgage',
                            'type': 'currency',
                            'required': False,
                            'placeholder': '0.00'
                        },
                        {
                            'id': 'interest_other',
                            'label': 'Interest - Other',
                            'type': 'currency',
                            'required': False,
                            'placeholder': '0.00'
                        },
                        {
                            'id': 'legal_professional',
                            'label': 'Legal and professional services',
                            'type': 'currency',
                            'required': False,
                            'placeholder': '0.00'
                        },
                        {
                            'id': 'office_expenses',
                            'label': 'Office expenses',
                            'type': 'currency',
                            'required': False,
                            'placeholder': '0.00'
                        },
                        {
                            'id': 'pension_profit_sharing',
                            'label': 'Pension and profit-sharing plans',
                            'type': 'currency',
                            'required': False,
                            'placeholder': '0.00'
                        },
                        {
                            'id': 'rent_lease_vehicles',
                            'label': 'Rent/lease - Vehicles, machinery, equipment',
                            'type': 'currency',
                            'required': False,
                            'placeholder': '0.00'
                        },
                        {
                            'id': 'rent_lease_other',
                            'label': 'Rent/lease - Other business property',
                            'type': 'currency',
                            'required': False,
                            'placeholder': '0.00'
                        },
                        {
                            'id': 'repairs_maintenance',
                            'label': 'Repairs and maintenance',
                            'type': 'currency',
                            'required': False,
                            'placeholder': '0.00'
                        },
                        {
                            'id': 'supplies',
                            'label': 'Supplies',
                            'type': 'currency',
                            'required': False,
                            'placeholder': '0.00'
                        },
                        {
                            'id': 'taxes_licenses',
                            'label': 'Taxes and licenses',
                            'type': 'currency',
                            'required': False,
                            'placeholder': '0.00'
                        },
                        {
                            'id': 'travel',
                            'label': 'Travel',
                            'type': 'currency',
                            'required': False,
                            'placeholder': '0.00'
                        },
                        {
                            'id': 'meals',
                            'label': 'Deductible meals',
                            'type': 'currency',
                            'required': False,
                            'placeholder': '0.00'
                        },
                        {
                            'id': 'utilities',
                            'label': 'Utilities',
                            'type': 'currency',
                            'required': False,
                            'placeholder': '0.00'
                        },
                        {
                            'id': 'wages',
                            'label': 'Wages',
                            'type': 'currency',
                            'required': False,
                            'placeholder': '0.00'
                        },
                        {
                            'id': 'other_expenses',
                            'label': 'Other expenses',
                            'type': 'currency_table',
                            'required': False,
                            'placeholder': '0.00',
                            'columns': [
                                {'id': 'description', 'label': 'Description', 'type': 'text'},
                                {'id': 'amount', 'label': 'Amount', 'type': 'currency'}
                            ]
                        }
                    ]
                },
                {
                    'id': 'home_office',
                    'title': 'Home Office Information',
                    'fields': [
                        {
                            'id': 'use_home_office',
                            'label': 'Do you use part of your home for business?',
                            'type': 'boolean',
                            'required': True,
                            'default': False
                        },
                        {
                            'id': 'home_office_area',
                            'label': 'Area of home used for business (square feet)',
                            'type': 'number',
                            'required': False,
                            'placeholder': '0',
                            'condition': {
                                'field': 'use_home_office',
                                'value': true
                            }
                        },
                        {
                            'id': 'total_home_area',
                            'label': 'Total area of home (square feet)',
                            'type': 'number',
                            'required': False,
                            'placeholder': '0',
                            'condition': {
                                'field': 'use_home_office',
                                'value': true
                            }
                        },
                        {
                            'id': 'exclusive_use',
                            'label': 'Is your home office used exclusively for business?',
                            'type': 'boolean',
                            'required': False,
                            'default': False,
                            'condition': {
                                'field': 'use_home_office',
                                'value': true
                            },
                            'help_text': 'The area must be used exclusively for business to qualify for the deduction'
                        }
                    ]
                },
                {
                    'id': 'vehicle',
                    'title': 'Vehicle Information',
                    'fields': [
                        {
                            'id': 'use_vehicle',
                            'label': 'Do you use a vehicle for business?',
                            'type': 'boolean',
                            'required': True,
                            'default': False
                        },
                        {
                            'id': 'vehicle_description',
                            'label': 'Vehicle description',
                            'type': 'text',
                            'required': False,
                            'placeholder': 'Year, make, model',
                            'condition': {
                                'field': 'use_vehicle',
                                'value': true
                            }
                        },
                        {
                            'id': 'business_miles',
                            'label': 'Business miles',
                            'type': 'number',
                            'required': False,
                            'placeholder': '0',
                            'condition': {
                                'field': 'use_vehicle',
                                'value': true
                            }
                        },
                        {
                            'id': 'commuting_miles',
                            'label': 'Commuting miles',
                            'type': 'number',
                            'required': False,
                            'placeholder': '0',
                            'condition': {
                                'field': 'use_vehicle',
                                'value': true
                            }
                        },
                        {
                            'id': 'other_personal_miles',
                            'label': 'Other personal miles',
                            'type': 'number',
                            'required': False,
                            'placeholder': '0',
                            'condition': {
                                'field': 'use_vehicle',
                                'value': true
                            }
                        },
                        {
                            'id': 'vehicle_method',
                            'label': 'Vehicle expense method',
                            'type': 'select',
                            'required': False,
                            'options': [
                                {'value': 'standard', 'label': 'Standard mileage rate'},
                                {'value': 'actual', 'label': 'Actual expenses'}
                            ],
                            'condition': {
                                'field': 'use_vehicle',
                                'value': true
                            },
                            'help_text': 'Standard mileage rate is simpler but actual expenses may result in a larger deduction'
                        }
                    ]
                }
            ]
        }
    elif form_type == '1099nec':
        return {
            'title': 'Form 1099-NEC - Nonemployee Compensation',
            'sections': [
                {
                    'id': 'payer_info',
                    'title': 'Payer Information',
                    'fields': [
                        {
                            'id': 'payer_name',
                            'label': 'Payer\'s Name',
                            'type': 'text',
                            'required': True,
                            'placeholder': 'Enter your business name'
                        },
                        {
                            'id': 'payer_tin',
                            'label': 'Payer\'s TIN',
                            'type': 'text',
                            'required': True,
                            'placeholder': 'XX-XXXXXXX'
                        },
                        {
                            'id': 'payer_address',
                            'label': 'Payer\'s Address',
                            'type': 'textarea',
                            'required': True,
                            'placeholder': 'Enter your business address'
                        },
                        {
                            'id': 'payer_phone',
                            'label': 'Payer\'s Phone Number',
                            'type': 'text',
                            'required': True,
                            'placeholder': '(XXX) XXX-XXXX'
                        }
                    ]
                },
                {
                    'id': 'recipient_info',
                    'title': 'Recipient Information',
                    'fields': [
                        {
                            'id': 'recipient_name',
                            'label': 'Recipient\'s Name',
                            'type': 'text',
                            'required': True,
                            'placeholder': 'Enter recipient\'s name'
                        },
                        {
                            'id': 'recipient_tin',
                            'label': 'Recipient\'s TIN',
                            'type': 'text',
                            'required': True,
                            'placeholder': 'XXX-XX-XXXX or XX-XXXXXXX'
                        },
                        {
                            'id': 'recipient_address',
                            'label': 'Recipient\'s Address',
                            'type': 'textarea',
                            'required': True,
                            'placeholder': 'Enter recipient\'s address'
                        }
                    ]
                },
                {
                    'id': 'payment_info',
                    'title': 'Payment Information',
                    'fields': [
                        {
                            'id': 'nonemployee_compensation',
                            'label': 'Nonemployee Compensation',
                            'type': 'currency',
                            'required': True,
                            'placeholder': '0.00',
                            'help_text': 'Total amount paid to the recipient for services'
                        },
                        {
                            'id': 'federal_income_tax_withheld',
                            'label': 'Federal Income Tax Withheld',
                            'type': 'currency',
                            'required': False,
                            'placeholder': '0.00'
                        },
                        {
                            'id': 'state_tax_withheld',
                            'label': 'State Tax Withheld',
                            'type': 'currency',
                            'required': False,
                            'placeholder': '0.00'
                        },
                        {
                            'id': 'state_code',
                            'label': 'State Code',
                            'type': 'text',
                            'required': False,
                            'placeholder': 'XX',
                            'help_text': 'Two-letter state code'
                        }
                    ]
                }
            ]
        }
    elif form_type == 'schedule_se':
        return {
            'title': 'Schedule SE - Self-Employment Tax',
            'sections': [
                {
                    'id': 'taxpayer_info',
                    'title': 'Taxpayer Information',
                    'fields': [
                        {
                            'id': 'name',
                            'label': 'Name',
                            'type': 'text',
                            'required': True,
                            'placeholder': 'Enter your name'
                        },
                        {
                            'id': 'ssn',
                            'label': 'Social Security Number',
                            'type': 'text',
                            'required': True,
                            'placeholder': 'XXX-XX-XXXX'
                        }
                    ]
                },
                {
                    'id': 'income_info',
                    'title': 'Self-Employment Income',
                    'fields': [
                        {
                            'id': 'schedule_c_income',
                            'label': 'Net profit (or loss) from Schedule C',
                            'type': 'currency',
                            'required': True,
                            'placeholder': '0.00'
                        },
                        {
                            'id': 'farm_income',
                            'label': 'Net farm profit (or loss) from Schedule F',
                            'type': 'currency',
                            'required': False,
                            'placeholder': '0.00'
                        },
                        {
                            'id': 'partnership_income',
                            'label': 'Net income (or loss) from partnerships and S corporations',
                            'type': 'currency',
                            'required': False,
                            'placeholder': '0.00'
                        },
                        {
                            'id': 'other_income',
                            'label': 'Other self-employment income',
                            'type': 'currency',
                            'required': False,
                            'placeholder': '0.00'
                        }
                    ]
                }
            ]
        }
    
    # Default schema for unsupported forms
    return {
        'title': f'Form {form_type.upper()}',
        'sections': [
            {
                'id': 'coming_soon',
                'title': 'Coming Soon',
                'fields': [
                    {
                        'id': 'message',
                        'label': 'Message',
                        'type': 'static',
                        'value': f'Detailed form for {form_type.upper()} is coming soon. Please check back later.'
                    }
                ]
            }
        ]
    }

def get_field_help(form_type, field_name, business_context, tax_year):
    """Get AI-guided help for a specific form field"""
    # In a real implementation, this would use AI to generate context-aware help
    # For prototype purposes, we return pre-defined help text for common fields
    
    # Help text for Schedule C fields
    schedule_c_help = {
        'business_code': 'The business code is a 6-digit code that describes your type of business. You can find the appropriate code in the Schedule C instructions. Common codes include 541990 (Professional Services), 541519 (IT Services), 624410 (Childcare), and 448140 (Clothing Retail).',
        'ein': 'Enter your Employer Identification Number (EIN) if you have one. If you operate as a sole proprietor and don\'t have employees, an EIN is not required - you can use your Social Security Number instead.',
        'accounting_method': 'Most small businesses use the Cash method, which counts income when received and expenses when paid. The Accrual method counts income when earned and expenses when incurred, regardless of when money changes hands. Once you choose a method, you generally need to use it consistently.',
        'gross_receipts': 'Include all income from your business before deducting expenses. This includes cash, checks, credit card payments, fair market value of property or services received, and any other income related to your business.',
        'returns_allowances': 'Include amounts paid to customers for returned merchandise and any allowances given for damaged or defective products.',
        'advertising': 'Include costs for marketing your business including ads, business cards, promotional materials, and website expenses.',
        'car_expenses': 'If you use the actual expenses method, include gas, oil, repairs, insurance, vehicle registration, lease payments, etc. If using standard mileage rate, report the miles in the Vehicle Information section instead.',
        'commissions': 'Include fees paid to non-employees (independent contractors) for selling your products or services. Payments to employees go under Wages.',
        'contract_labor': 'Include payments to independent contractors for services related to your business. If you paid any individual $600 or more, you may need to file Form 1099-NEC.',
        'depreciation': 'Use this line if you are claiming depreciation or Section 179 expenses for business assets. If claiming this deduction, you should also complete Form 4562.',
        'insurance': 'Include business insurance premiums such as liability insurance, business property insurance, and business interruption insurance. Do not include health insurance for yourself (that goes on Schedule 1) or for employees (use Employee Benefits).',
        'interest_mortgage': 'Include interest paid on a mortgage for real property used in your business (other than your home).',
        'interest_other': 'Include interest on business loans, business credit cards, and other business debt.',
        'legal_professional': 'Include fees paid to lawyers, accountants, consultants, and other professionals who provided services to your business.',
        'office_expenses': 'Include office supplies, postage, stationery, and other consumable office items. Computer equipment and furniture should usually be depreciated.',
        'rent_lease_vehicles': 'Include amounts paid to rent or lease vehicles, machinery, or equipment for your business.',
        'rent_lease_other': 'Include amounts paid to rent or lease office space, storage, or other business property.',
        'repairs_maintenance': 'Include costs to keep your business property in good working condition. Major improvements that add to the property\'s value should be depreciated.',
        'supplies': 'Include costs of supplies that are not inventory and not included in office expenses.',
        'taxes_licenses': 'Include business licenses, regulatory fees, and taxes except self-employment tax. Include property taxes on business assets.',
        'travel': 'Include airfare, hotels, rental cars, and other costs of business trips. Do not include local transportation or meals (those go on separate lines).',
        'meals': 'Include 50% of business meals with clients or while traveling. For 2021 and 2022, certain restaurant meals may be 100% deductible - check current IRS rules.',
        'utilities': 'Include electricity, gas, water, trash removal, and telephone expenses for your business. For a home office, these are typically included in the home office deduction instead.',
        'wages': 'Include wages, salaries, and bonuses paid to employees (not to yourself as the business owner). Include payroll taxes in Taxes and Licenses.',
        'home_office_area': 'Measure the area used regularly and exclusively for your business. If you use a 10×12 foot room, enter 120 square feet.',
        'total_home_area': 'Enter the total square footage of your entire home.',
        'exclusive_use': 'The home office area must be used exclusively for business to qualify for the deduction. This means you cannot use the area for personal activities. There are limited exceptions for daycare facilities and inventory storage.'
    }
    
    # Return the appropriate help text based on the form type and field
    if form_type == 'schedule_c':
        return schedule_c_help.get(field_name, 'No specific guidance available for this field. Please refer to the IRS instructions for Schedule C.')
    elif form_type == '1099nec':
        if field_name == 'nonemployee_compensation':
            return 'Enter the total amount paid to the recipient for services during the year. This includes fees, commissions, prizes, awards, and other forms of compensation for services.'
        elif field_name == 'recipient_tin':
            return 'Enter the recipient\'s taxpayer identification number (TIN). For individuals, this is their Social Security Number (SSN). For businesses, this is their Employer Identification Number (EIN). If the recipient did not provide a TIN, you may be required to withhold federal income tax (backup withholding).'
        return 'Please refer to the IRS instructions for Form 1099-NEC for guidance on this field.'
    
    # Default help text if no specific guidance is available
    return 'No specific guidance available for this field. Please refer to the IRS instructions.'