import json
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.app import db
from app.models import TaxForm, TaxFormType, AuditLog
from app.session import FormSession
from app.access_control import requires_access_level
from modules.pdf_utils import generate_tax_form_pdf

forms_bp = Blueprint('forms', __name__)

# Form templates and structure
FORM_TEMPLATES = {
    "1120": {
        "sections": [
            {
                "name": "Basic Information",
                "fields": [
                    {"name": "company_name", "label": "Company Name", "type": "text", "required": True},
                    {"name": "ein", "label": "Employer Identification Number", "type": "text", "required": True},
                    {"name": "address", "label": "Business Address", "type": "text", "required": True},
                    {"name": "incorporation_date", "label": "Date of Incorporation", "type": "date", "required": True},
                    {"name": "tax_year", "label": "Tax Year", "type": "number", "required": True}
                ]
            },
            {
                "name": "Income",
                "fields": [
                    {"name": "gross_receipts", "label": "Gross Receipts or Sales", "type": "number", "required": True},
                    {"name": "returns_allowances", "label": "Returns and Allowances", "type": "number", "required": False},
                    {"name": "other_income", "label": "Other Income", "type": "number", "required": False}
                ]
            },
            {
                "name": "Deductions",
                "fields": [
                    {"name": "salaries_wages", "label": "Salaries and Wages", "type": "number", "required": False},
                    {"name": "repairs_maintenance", "label": "Repairs and Maintenance", "type": "number", "required": False},
                    {"name": "rents", "label": "Rents", "type": "number", "required": False},
                    {"name": "taxes_licenses", "label": "Taxes and Licenses", "type": "number", "required": False},
                    {"name": "interest", "label": "Interest", "type": "number", "required": False},
                    {"name": "depreciation", "label": "Depreciation", "type": "number", "required": False},
                    {"name": "other_deductions", "label": "Other Deductions", "type": "number", "required": False}
                ]
            }
        ]
    },
    "1065": {
        "sections": [
            {
                "name": "Partnership Information",
                "fields": [
                    {"name": "partnership_name", "label": "Partnership Name", "type": "text", "required": True},
                    {"name": "ein", "label": "Employer Identification Number", "type": "text", "required": True},
                    {"name": "address", "label": "Business Address", "type": "text", "required": True},
                    {"name": "formation_date", "label": "Date Partnership Formed", "type": "date", "required": True},
                    {"name": "tax_year", "label": "Tax Year", "type": "number", "required": True}
                ]
            },
            {
                "name": "Income",
                "fields": [
                    {"name": "gross_receipts", "label": "Gross Receipts or Sales", "type": "number", "required": True},
                    {"name": "cost_of_goods", "label": "Cost of Goods Sold", "type": "number", "required": False},
                    {"name": "other_income", "label": "Other Income", "type": "number", "required": False}
                ]
            },
            {
                "name": "Deductions",
                "fields": [
                    {"name": "salaries_wages", "label": "Salaries and Wages", "type": "number", "required": False},
                    {"name": "guaranteed_payments", "label": "Guaranteed Payments to Partners", "type": "number", "required": False},
                    {"name": "repairs_maintenance", "label": "Repairs and Maintenance", "type": "number", "required": False},
                    {"name": "rent", "label": "Rent", "type": "number", "required": False},
                    {"name": "taxes_licenses", "label": "Taxes and Licenses", "type": "number", "required": False},
                    {"name": "interest", "label": "Interest", "type": "number", "required": False},
                    {"name": "depreciation", "label": "Depreciation", "type": "number", "required": False},
                    {"name": "other_deductions", "label": "Other Deductions", "type": "number", "required": False}
                ]
            }
        ]
    },
    "Schedule C": {
        "sections": [
            {
                "name": "Business Information",
                "fields": [
                    {"name": "business_name", "label": "Business Name", "type": "text", "required": True},
                    {"name": "business_code", "label": "Business Code", "type": "text", "required": True},
                    {"name": "ssn", "label": "Social Security Number", "type": "text", "required": True},
                    {"name": "address", "label": "Business Address", "type": "text", "required": True},
                    {"name": "tax_year", "label": "Tax Year", "type": "number", "required": True}
                ]
            },
            {
                "name": "Income",
                "fields": [
                    {"name": "gross_receipts", "label": "Gross Receipts or Sales", "type": "number", "required": True},
                    {"name": "returns_allowances", "label": "Returns and Allowances", "type": "number", "required": False},
                    {"name": "other_income", "label": "Other Income", "type": "number", "required": False}
                ]
            },
            {
                "name": "Expenses",
                "fields": [
                    {"name": "advertising", "label": "Advertising", "type": "number", "required": False},
                    {"name": "car_expenses", "label": "Car and Truck Expenses", "type": "number", "required": False},
                    {"name": "commissions", "label": "Commissions and Fees", "type": "number", "required": False},
                    {"name": "depreciation", "label": "Depreciation", "type": "number", "required": False},
                    {"name": "insurance", "label": "Insurance (other than health)", "type": "number", "required": False},
                    {"name": "professional_fees", "label": "Legal and Professional Services", "type": "number", "required": False},
                    {"name": "office_expenses", "label": "Office Expenses", "type": "number", "required": False},
                    {"name": "rent_equipment", "label": "Rent - Equipment", "type": "number", "required": False},
                    {"name": "rent_property", "label": "Rent - Property", "type": "number", "required": False},
                    {"name": "supplies", "label": "Supplies", "type": "number", "required": False},
                    {"name": "taxes_licenses", "label": "Taxes and Licenses", "type": "number", "required": False},
                    {"name": "travel", "label": "Travel", "type": "number", "required": False},
                    {"name": "meals", "label": "Meals", "type": "number", "required": False},
                    {"name": "utilities", "label": "Utilities", "type": "number", "required": False},
                    {"name": "wages", "label": "Wages", "type": "number", "required": False},
                    {"name": "other_expenses", "label": "Other Expenses", "type": "number", "required": False}
                ]
            }
        ]
    }
}

@forms_bp.route('/forms')
@login_required
def form_list():
    """List all tax forms"""
    # Get user's forms
    forms = TaxForm.query.filter_by(user_id=current_user.id).all()
    
    return render_template(
        'form_list.html',
        forms=forms,
        form_types=TaxFormType
    )

@forms_bp.route('/forms/new', methods=['GET', 'POST'])
@login_required
@requires_access_level('guided_filing')
def new_form():
    """Select a form type to begin"""
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        tax_year = request.form.get('tax_year')
        
        if not form_type or not tax_year:
            flash('Please select a form type and tax year', 'error')
            return redirect(url_for('forms.new_form'))
        
        # Save form context
        FormSession.save_tax_context({
            'form_type': form_type,
            'tax_year': tax_year,
            'started_at': datetime.utcnow().isoformat()
        })
        
        # Redirect to the form editor
        return redirect(url_for('forms.edit_form', form_type=form_type))
    
    # Show form selection page
    current_year = datetime.now().year
    available_years = range(2019, current_year + 1)
    
    return render_template(
        'form_select.html',
        form_types=TaxFormType,
        available_years=available_years
    )

@forms_bp.route('/forms/edit/<form_type>', methods=['GET', 'POST'])
@login_required
@requires_access_level('guided_filing')
def edit_form(form_type):
    """Edit a tax form step by step"""
    # Validate form type
    try:
        form_enum = TaxFormType(form_type)
    except ValueError:
        flash('Invalid form type', 'error')
        return redirect(url_for('forms.new_form'))
    
    # Get tax context
    tax_context = FormSession.get_tax_context()
    if not tax_context:
        flash('Please select a form type and tax year first', 'warning')
        return redirect(url_for('forms.new_form'))
    
    # Get form template
    template = FORM_TEMPLATES.get(form_type)
    if not template:
        flash('Form template not found', 'error')
        return redirect(url_for('forms.new_form'))
    
    if request.method == 'POST':
        # Process form submission
        form_data = {}
        for section in template['sections']:
            for field in section['fields']:
                field_name = field['name']
                field_value = request.form.get(field_name, '')
                form_data[field_name] = field_value
        
        # Add tax context
        form_data['tax_year'] = tax_context.get('tax_year')
        
        # Create or update tax form record
        tax_form = TaxForm(
            user_id=current_user.id,
            form_type=form_enum,
            tax_year=int(tax_context.get('tax_year')),
            data=form_data,
            status='completed'
        )
        
        try:
            db.session.add(tax_form)
            
            # Log the action
            log = AuditLog(
                user_id=current_user.id,
                action="form_completed",
                ip_address=request.remote_addr,
                details=f"Completed {form_type} for year {tax_context.get('tax_year')}"
            )
            db.session.add(log)
            db.session.commit()
            
            # Generate PDF
            pdf_path = generate_tax_form_pdf(tax_form)
            if pdf_path:
                tax_form.pdf_path = pdf_path
                db.session.commit()
            
            flash('Tax form saved successfully', 'success')
            return redirect(url_for('forms.view_form', form_id=tax_form.id))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error saving tax form: {str(e)}")
            flash('An error occurred while saving the form', 'error')
    
    # Show the form template
    return render_template(
        'tax_form.html',
        form_type=form_type,
        template=template,
        tax_context=tax_context
    )

@forms_bp.route('/forms/view/<int:form_id>')
@login_required
def view_form(form_id):
    """View a completed tax form"""
    form = TaxForm.query.filter_by(id=form_id, user_id=current_user.id).first_or_404()
    
    # Get form template
    template = FORM_TEMPLATES.get(form.form_type.value)
    if not template:
        flash('Form template not found', 'error')
        return redirect(url_for('forms.form_list'))
    
    return render_template(
        'view_form.html',
        form=form,
        template=template
    )

@forms_bp.route('/forms/download/<int:form_id>')
@login_required
def download_form(form_id):
    """Download a form as PDF"""
    form = TaxForm.query.filter_by(id=form_id, user_id=current_user.id).first_or_404()
    
    if not form.pdf_path:
        # Generate PDF if not already generated
        pdf_path = generate_tax_form_pdf(form)
        if pdf_path:
            form.pdf_path = pdf_path
            db.session.commit()
        else:
            flash('Could not generate PDF', 'error')
            return redirect(url_for('forms.view_form', form_id=form.id))
    
    # Log the download
    log = AuditLog(
        user_id=current_user.id,
        action="form_downloaded",
        ip_address=request.remote_addr,
        details=f"Downloaded {form.form_type.value} for year {form.tax_year}"
    )
    db.session.add(log)
    db.session.commit()
    
    # This would normally return a file download
    # For the purpose of this example, we'll just redirect
    flash('PDF downloaded successfully', 'success')
    return redirect(url_for('forms.view_form', form_id=form.id))
