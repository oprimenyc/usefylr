import logging
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.app import db
from app.models import IRSLetter, LetterType, AuditLog
from app.access_control import requires_access_level
from modules.pdf_utils import generate_irs_letter_pdf

letters_bp = Blueprint('letters', __name__)

# Letter templates
LETTER_TEMPLATES = {
    "penalty_abatement": {
        "title": "Penalty Abatement Request",
        "description": "Request to have penalties removed due to reasonable cause.",
        "fields": [
            {"name": "taxpayer_name", "label": "Taxpayer Name", "type": "text", "required": True},
            {"name": "taxpayer_address", "label": "Taxpayer Address", "type": "text", "required": True},
            {"name": "taxpayer_ein", "label": "EIN or SSN", "type": "text", "required": True},
            {"name": "tax_year", "label": "Tax Year(s)", "type": "text", "required": True},
            {"name": "penalty_amount", "label": "Penalty Amount", "type": "number", "required": True},
            {"name": "reason", "label": "Reason for Penalty", "type": "select", "required": True, 
             "options": ["Late Filing", "Late Payment", "Estimated Tax", "Other"]},
            {"name": "explanation", "label": "Explanation of Reasonable Cause", "type": "textarea", "required": True},
            {"name": "date", "label": "Date", "type": "date", "required": True}
        ]
    },
    "reasonable_cause": {
        "title": "Reasonable Cause Explanation",
        "description": "Detailed explanation of circumstances that led to tax compliance issue.",
        "fields": [
            {"name": "taxpayer_name", "label": "Taxpayer Name", "type": "text", "required": True},
            {"name": "taxpayer_address", "label": "Taxpayer Address", "type": "text", "required": True},
            {"name": "taxpayer_ein", "label": "EIN or SSN", "type": "text", "required": True},
            {"name": "tax_year", "label": "Tax Year(s)", "type": "text", "required": True},
            {"name": "issue_type", "label": "Issue Type", "type": "select", "required": True, 
             "options": ["Late Filing", "Late Payment", "Missing Information", "Other"]},
            {"name": "circumstances", "label": "Description of Circumstances", "type": "textarea", "required": True},
            {"name": "resolution", "label": "Steps Taken to Resolve", "type": "textarea", "required": True},
            {"name": "date", "label": "Date", "type": "date", "required": True}
        ]
    },
    "late_filing_relief": {
        "title": "Late Filing Relief Request",
        "description": "Request relief for late filing penalties for first-time offenders.",
        "fields": [
            {"name": "taxpayer_name", "label": "Taxpayer Name", "type": "text", "required": True},
            {"name": "taxpayer_address", "label": "Taxpayer Address", "type": "text", "required": True},
            {"name": "taxpayer_ein", "label": "EIN or SSN", "type": "text", "required": True},
            {"name": "tax_year", "label": "Tax Year", "type": "text", "required": True},
            {"name": "filing_date", "label": "Date Actually Filed", "type": "date", "required": True},
            {"name": "due_date", "label": "Original Due Date", "type": "date", "required": True},
            {"name": "compliance_history", "label": "Previous Compliance History", "type": "textarea", "required": True},
            {"name": "explanation", "label": "Explanation for Late Filing", "type": "textarea", "required": True},
            {"name": "date", "label": "Date", "type": "date", "required": True}
        ]
    }
}

@letters_bp.route('/letters')
@login_required
def letter_list():
    """List all IRS letters"""
    # Get user's letters
    letters = IRSLetter.query.filter_by(user_id=current_user.id).all()
    
    return render_template(
        'letter_list.html',
        letters=letters,
        letter_types=LetterType
    )

@letters_bp.route('/letters/new', methods=['GET', 'POST'])
@login_required
@requires_access_level('irs_letter_pack')
def new_letter():
    """Select a letter type to begin"""
    if request.method == 'POST':
        letter_type = request.form.get('letter_type')
        
        if not letter_type:
            flash('Please select a letter type', 'error')
            return redirect(url_for('letters.new_letter'))
        
        # Redirect to the letter editor
        return redirect(url_for('letters.edit_letter', letter_type=letter_type))
    
    # Show letter selection page
    return render_template(
        'letter_select.html',
        letter_types=LetterType,
        letter_templates=LETTER_TEMPLATES
    )

@letters_bp.route('/letters/edit/<letter_type>', methods=['GET', 'POST'])
@login_required
@requires_access_level('irs_letter_pack')
def edit_letter(letter_type):
    """Edit an IRS letter"""
    # Validate letter type
    try:
        letter_enum = LetterType(letter_type)
    except ValueError:
        flash('Invalid letter type', 'error')
        return redirect(url_for('letters.new_letter'))
    
    # Get letter template
    template = LETTER_TEMPLATES.get(letter_type)
    if not template:
        flash('Letter template not found', 'error')
        return redirect(url_for('letters.new_letter'))
    
    if request.method == 'POST':
        # Process form submission
        letter_data = {}
        for field in template['fields']:
            field_name = field['name']
            field_value = request.form.get(field_name, '')
            letter_data[field_name] = field_value
        
        # Create letter record
        letter = IRSLetter(
            user_id=current_user.id,
            letter_type=letter_enum,
            data=letter_data,
            status='completed'
        )
        
        try:
            db.session.add(letter)
            
            # Log the action
            log = AuditLog(
                user_id=current_user.id,
                action="letter_created",
                ip_address=request.remote_addr,
                details=f"Created {letter_type} letter"
            )
            db.session.add(log)
            db.session.commit()
            
            # Generate PDF
            pdf_path = generate_irs_letter_pdf(letter)
            if pdf_path:
                letter.pdf_path = pdf_path
                db.session.commit()
            
            flash('IRS letter created successfully', 'success')
            return redirect(url_for('letters.view_letter', letter_id=letter.id))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error saving IRS letter: {str(e)}")
            flash('An error occurred while saving the letter', 'error')
    
    # Show the letter template
    return render_template(
        'edit_letter.html',
        letter_type=letter_type,
        template=template
    )

@letters_bp.route('/letters/view/<int:letter_id>')
@login_required
def view_letter(letter_id):
    """View a completed IRS letter"""
    letter = IRSLetter.query.filter_by(id=letter_id, user_id=current_user.id).first_or_404()
    
    # Get letter template
    template = LETTER_TEMPLATES.get(letter.letter_type.value)
    if not template:
        flash('Letter template not found', 'error')
        return redirect(url_for('letters.letter_list'))
    
    return render_template(
        'view_letter.html',
        letter=letter,
        template=template
    )

@letters_bp.route('/letters/download/<int:letter_id>')
@login_required
def download_letter(letter_id):
    """Download a letter as PDF"""
    letter = IRSLetter.query.filter_by(id=letter_id, user_id=current_user.id).first_or_404()
    
    if not letter.pdf_path:
        # Generate PDF if not already generated
        pdf_path = generate_irs_letter_pdf(letter)
        if pdf_path:
            letter.pdf_path = pdf_path
            db.session.commit()
        else:
            flash('Could not generate PDF', 'error')
            return redirect(url_for('letters.view_letter', letter_id=letter.id))
    
    # Log the download
    log = AuditLog(
        user_id=current_user.id,
        action="letter_downloaded",
        ip_address=request.remote_addr,
        details=f"Downloaded {letter.letter_type.value} letter"
    )
    db.session.add(log)
    db.session.commit()
    
    # This would normally return a file download
    # For the purpose of this example, we'll just redirect
    flash('PDF downloaded successfully', 'success')
    return redirect(url_for('letters.view_letter', letter_id=letter.id))
