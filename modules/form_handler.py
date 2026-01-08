"""
Form Handler Module

This module contains the core functionality for handling tax forms,
using the form_library components to render, validate, and process forms.
"""
import os
import json
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app, abort
from flask_login import login_required, current_user

from app.app import db
from app.models import TaxForm, TaxFormType, BusinessProfile, AuditLog
from app.session import FormSession
from app.access_control import requires_access_level, requires_legal_acknowledgment
from modules.form_library import get_form_template
from modules.pdf_utils import generate_tax_form_pdf

# Create blueprint
forms_bp = Blueprint('forms', __name__, url_prefix='/forms')

@forms_bp.route('/')
@login_required
@requires_legal_acknowledgment
def form_list():
    """Display list of user's tax forms"""
    # Get user's tax forms
    forms = TaxForm.query.filter_by(user_id=current_user.id).order_by(TaxForm.updated_at.desc()).all()
    
    # Get all available form types
    form_types = [
        {'id': 'schedule_c', 'name': 'Schedule C', 'description': 'Profit or Loss From Business', 'entity_type': 'SOLE_PROPRIETOR'},
        {'id': 'schedule_se', 'name': 'Schedule SE', 'description': 'Self-Employment Tax', 'entity_type': 'SOLE_PROPRIETOR'},
        {'id': 'form_1120', 'name': 'Form 1120', 'description': 'U.S. Corporation Income Tax Return', 'entity_type': 'C_CORP'},
        {'id': 'form_1120s', 'name': 'Form 1120-S', 'description': 'U.S. Income Tax Return for an S Corporation', 'entity_type': 'S_CORP'},
        {'id': 'form_1065', 'name': 'Form 1065', 'description': 'U.S. Return of Partnership Income', 'entity_type': 'PARTNERSHIP'},
        {'id': 'form_4562', 'name': 'Form 4562', 'description': 'Depreciation and Amortization', 'entity_type': 'ALL'},
    ]
    
    # Get business profile
    business_profile = BusinessProfile.query.filter_by(user_id=current_user.id).first()
    
    current_year = datetime.now().year
    
    return render_template(
        'forms/list.html', 
        forms=forms, 
        form_types=form_types, 
        business_profile=business_profile,
        current_year=current_year
    )

@forms_bp.route('/new')
@login_required
@requires_legal_acknowledgment
@requires_access_level('guided_input')
def new_form():
    """Form type selection page"""
    # Get query parameters
    form_type_id = request.args.get('form_type')
    tax_year = request.args.get('tax_year', datetime.now().year - 1)
    
    # If form type is specified, redirect to form editor
    if form_type_id:
        return redirect(url_for('forms.edit_form', form_type_id=form_type_id, tax_year=tax_year))
    
    # Get all available form types
    form_types = [
        {'id': 'schedule_c', 'name': 'Schedule C', 'description': 'Profit or Loss From Business', 'entity_type': 'SOLE_PROPRIETOR'},
        {'id': 'schedule_se', 'name': 'Schedule SE', 'description': 'Self-Employment Tax', 'entity_type': 'SOLE_PROPRIETOR'},
        {'id': 'form_1120', 'name': 'Form 1120', 'description': 'U.S. Corporation Income Tax Return', 'entity_type': 'C_CORP'},
        {'id': 'form_1120s', 'name': 'Form 1120-S', 'description': 'U.S. Income Tax Return for an S Corporation', 'entity_type': 'S_CORP'},
        {'id': 'form_1065', 'name': 'Form 1065', 'description': 'U.S. Return of Partnership Income', 'entity_type': 'PARTNERSHIP'},
        {'id': 'form_4562', 'name': 'Form 4562', 'description': 'Depreciation and Amortization', 'entity_type': 'ALL'},
    ]
    
    # Get business profile
    business_profile = BusinessProfile.query.filter_by(user_id=current_user.id).first()
    
    # Get current and available tax years
    current_year = datetime.now().year
    available_years = list(range(current_year - 3, current_year + 1))
    
    return render_template(
        'forms/new.html', 
        form_types=form_types, 
        business_profile=business_profile,
        current_year=current_year,
        available_years=available_years
    )

@forms_bp.route('/edit/<form_type_id>', methods=['GET', 'POST'])
@login_required
@requires_legal_acknowledgment
@requires_access_level('guided_input')
def edit_form(form_type_id):
    """Edit or create a new tax form"""
    # Get query parameters
    form_id = request.args.get('id')
    tax_year = request.args.get('tax_year', datetime.now().year - 1)
    section = request.args.get('section', 0, type=int)
    
    # Get form template
    form_template = get_form_template(form_type_id)
    
    if not form_template:
        flash(f"Form template '{form_type_id}' not found.", "danger")
        return redirect(url_for('forms.new_form'))
    
    # Load existing form data if editing
    form_data = {}
    form = None
    
    if form_id:
        # Get existing form
        form = TaxForm.query.filter_by(id=form_id, user_id=current_user.id).first_or_404()
        
        # Load form data
        form_data = form.data or {}
        tax_year = form.tax_year
    else:
        # Check if we have form progress in session
        form_progress = FormSession.get_form_progress(form_type_id)
        if form_progress:
            form_data = form_progress
    
    # Handle form submission
    if request.method == 'POST':
        # Get form data
        form_data = request.form.to_dict()
        
        # Check if save draft
        is_save_draft = 'save_draft' in request.form
        
        # Convert checkbox values
        for key, value in form_data.items():
            if value == 'true':
                form_data[key] = True
            elif value == 'false':
                form_data[key] = False
        
        # Validate form data
        errors = form_template.validate(form_data)
        
        if errors and not is_save_draft:
            # Flash validation errors
            flash("Please correct the errors in the form.", "danger")
            
            # Return to form with errors
            return render_template(
                'forms/edit.html',
                form_template=form_template,
                form_data=form_data,
                form=form,
                tax_year=tax_year,
                section_index=section,
                errors=errors
            )
        
        # Save form progress to session
        FormSession.save_form_progress(form_type_id, form_data)
        
        # If this is just to save a draft
        if is_save_draft:
            flash("Form progress saved successfully.", "success")
            
            # Stay on the same page
            return render_template(
                'forms/edit.html',
                form_template=form_template,
                form_data=form_data,
                form=form,
                tax_year=tax_year,
                section_index=section
            )
        
        # Save to database
        if form:
            # Update existing form
            form.data = form_data
            form.updated_at = datetime.utcnow()
            form.status = 'completed'
        else:
            # Create new form
            form = TaxForm(
                user_id=current_user.id,
                form_type=TaxFormType[form_template.metadata['tax_form_type']],
                tax_year=tax_year,
                data=form_data,
                status='completed'
            )
            db.session.add(form)
        
        # Commit to database
        db.session.commit()
        
        # Clear form progress
        FormSession.clear_form_progress()
        
        # Log this action
        AuditLog.log_action(
            user_id=current_user.id,
            action=f"Completed form {form_template.title} for tax year {tax_year}",
            data={'form_id': form.id, 'form_type': form_template.metadata['tax_form_type'], 'tax_year': tax_year}
        )
        
        # Generate PDF
        try:
            pdf_path = generate_tax_form_pdf(form)
            
            # Update form with PDF path
            form.pdf_path = pdf_path
            db.session.commit()
            
            flash("Form completed and PDF generated successfully.", "success")
        except Exception as e:
            flash(f"Form saved, but PDF generation failed: {str(e)}", "warning")
        
        # Redirect to view form
        return redirect(url_for('forms.view_form', form_id=form.id))
    
    # Pre-fill form with business profile data if new form
    if not form_id and not form_data:
        business_profile = BusinessProfile.query.filter_by(user_id=current_user.id).first()
        
        if business_profile:
            # Populate form data from business profile
            form_data['business_name'] = business_profile.business_name
            form_data['ein'] = business_profile.ein
            form_data['business_address'] = business_profile.business_address
    
    # Render form template
    return render_template(
        'forms/edit.html',
        form_template=form_template,
        form_data=form_data,
        form=form,
        tax_year=tax_year,
        section_index=section
    )

@forms_bp.route('/view/<int:form_id>')
@login_required
@requires_legal_acknowledgment
def view_form(form_id):
    """View a completed tax form"""
    # Get form
    form = TaxForm.query.filter_by(id=form_id, user_id=current_user.id).first_or_404()
    
    # Get form template
    form_template = None
    for template_id, template_info in {
        'schedule_c': {'tax_form_type': 'SCHEDULE_C'},
        'schedule_se': {'tax_form_type': 'SCHEDULE_SE'},
        'form_1120': {'tax_form_type': 'FORM_1120'},
        'form_1120s': {'tax_form_type': 'FORM_1120S'},
        'form_1065': {'tax_form_type': 'FORM_1065'},
        'form_4562': {'tax_form_type': 'FORM_4562'},
    }.items():
        if form.form_type.name == template_info['tax_form_type']:
            form_template = get_form_template(template_id)
            break
    
    if not form_template:
        flash(f"Form template for '{form.form_type.name}' not found.", "danger")
        return redirect(url_for('forms.form_list'))
    
    # Render form view
    return render_template(
        'forms/view.html',
        form=form,
        form_template=form_template,
        form_data=form.data or {}
    )

@forms_bp.route('/download/<int:form_id>')
@login_required
@requires_legal_acknowledgment
@requires_access_level('export_forms')
def download_form(form_id):
    """Download a tax form PDF"""
    # Get form
    form = TaxForm.query.filter_by(id=form_id, user_id=current_user.id).first_or_404()
    
    # Check if PDF exists
    if not form.pdf_path or not os.path.exists(form.pdf_path):
        # Generate PDF
        try:
            pdf_path = generate_tax_form_pdf(form)
            
            # Update form with PDF path
            form.pdf_path = pdf_path
            db.session.commit()
        except Exception as e:
            flash(f"Failed to generate PDF: {str(e)}", "danger")
            return redirect(url_for('forms.view_form', form_id=form.id))
    
    # Send PDF file
    from flask import send_file
    return send_file(
        form.pdf_path,
        as_attachment=True,
        download_name=f"{form.form_type.name}_{form.tax_year}.pdf"
    )

@forms_bp.route('/delete/<int:form_id>', methods=['POST'])
@login_required
def delete_form(form_id):
    """Delete a tax form"""
    # Get form
    form = TaxForm.query.filter_by(id=form_id, user_id=current_user.id).first_or_404()
    
    # Delete PDF if exists
    if form.pdf_path and os.path.exists(form.pdf_path):
        os.remove(form.pdf_path)
    
    # Log this action
    AuditLog.log_action(
        user_id=current_user.id,
        action=f"Deleted form {form.form_type.name} for tax year {form.tax_year}",
        data={'form_id': form.id, 'form_type': form.form_type.name, 'tax_year': form.tax_year}
    )
    
    # Delete form
    db.session.delete(form)
    db.session.commit()
    
    flash("Form deleted successfully.", "success")
    return redirect(url_for('forms.form_list'))

@forms_bp.route('/save-progress/<form_type_id>', methods=['POST'])
@login_required
def save_progress(form_type_id):
    """Save form progress via AJAX"""
    # Get form data
    form_data = request.json
    
    # Save to session
    FormSession.save_form_progress(form_type_id, form_data)
    
    return jsonify({'status': 'success', 'message': 'Progress saved'})

@forms_bp.route('/template/<form_type_id>')
@login_required
def get_template(form_type_id):
    """Get form template JSON"""
    form_template = get_form_template(form_type_id)
    
    if not form_template:
        abort(404, f"Form template '{form_type_id}' not found.")
    
    return jsonify(form_template.to_dict())

@forms_bp.route('/validate/<form_type_id>', methods=['POST'])
@login_required
def validate_form(form_type_id):
    """Validate form data"""
    # Get form template
    form_template = get_form_template(form_type_id)
    
    if not form_template:
        abort(404, f"Form template '{form_type_id}' not found.")
    
    # Get form data
    form_data = request.json
    
    # Validate form data
    errors = form_template.validate(form_data)
    
    return jsonify({
        'valid': len(errors) == 0,
        'errors': errors
    })

def init_app(app):
    """Initialize the form handlers with the Flask app"""
    app.register_blueprint(forms_bp)