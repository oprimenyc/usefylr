"""
Advanced IRS Letter Generation Module

This module provides enhanced functionality for generating customized IRS letters
based on user inputs and AI-assisted document generation.
"""

from flask import Blueprint, render_template, flash, redirect, url_for, request, abort, jsonify
from flask_login import login_required, current_user
from app.app import db
from app.models import IRSLetter, AuditLog, LetterType
from app.access_control import requires_access_level, unlock_tool
from ai.openai_interface import get_openai_response
import json
from datetime import datetime, timedelta

# Create blueprint
advanced_letter_bp = Blueprint('advanced_letters', __name__, url_prefix='/advanced-letters')

@advanced_letter_bp.route('/')
@login_required
def index():
    """Display the advanced letter generation homepage"""
    # Get list of letter categories
    letter_categories = get_letter_categories()
    
    # Get user's previously generated letters
    user_letters = IRSLetter.query.filter_by(user_id=current_user.id).all()
    
    return render_template('letters/advanced/index.html', 
                          letter_categories=letter_categories,
                          user_letters=user_letters)

@advanced_letter_bp.route('/template/<letter_type>')
@login_required
def select_template(letter_type):
    """Allow user to select from available templates for a letter type"""
    # Check if the letter type is valid
    try:
        letter_enum = LetterType[letter_type.upper()]
    except KeyError:
        flash('Invalid letter type selected.', 'danger')
        return redirect(url_for('advanced_letters.index'))
    
    # Get templates for this letter type
    templates = get_letter_templates(letter_enum)
    
    return render_template('letters/advanced/select_template.html',
                          letter_type=letter_type,
                          templates=templates)

@advanced_letter_bp.route('/customize/<letter_type>/<template_id>')
@login_required
def customize_letter(letter_type, template_id):
    """Allow user to customize a letter template"""
    # Check if the letter type is valid
    try:
        letter_enum = LetterType[letter_type.upper()]
    except KeyError:
        flash('Invalid letter type selected.', 'danger')
        return redirect(url_for('advanced_letters.index'))
    
    # Get the specific template
    template = get_letter_template_by_id(letter_enum, template_id)
    if not template:
        flash('Template not found.', 'danger')
        return redirect(url_for('advanced_letters.select_template', letter_type=letter_type))
    
    # Get required fields for this template
    form_fields = get_template_form_fields(letter_enum, template_id)
    
    # Check if user is editing an existing letter
    letter_id = request.args.get('letter_id')
    letter_data = {}
    
    if letter_id:
        letter = IRSLetter.query.filter_by(id=letter_id, user_id=current_user.id).first()
        if letter:
            letter_data = letter.data
    
    return render_template('letters/advanced/customize.html',
                          letter_type=letter_type,
                          template=template,
                          form_fields=form_fields,
                          letter_data=letter_data,
                          letter_id=letter_id)

@advanced_letter_bp.route('/preview/<letter_type>/<template_id>', methods=['POST'])
@login_required
def preview_letter(letter_type, template_id):
    """Preview a letter before saving"""
    # Check if the letter type is valid
    try:
        letter_enum = LetterType[letter_type.upper()]
    except KeyError:
        flash('Invalid letter type selected.', 'danger')
        return redirect(url_for('advanced_letters.index'))
    
    # Get form data
    form_data = request.form.to_dict()
    
    # Generate letter content
    letter_content = generate_letter_content(letter_enum, template_id, form_data)
    
    return render_template('letters/advanced/preview.html',
                          letter_type=letter_type,
                          template_id=template_id,
                          form_data=form_data,
                          letter_content=letter_content)

@advanced_letter_bp.route('/save/<letter_type>/<template_id>', methods=['POST'])
@login_required
def save_letter(letter_type, template_id):
    """Save a letter after preview"""
    # Check if the letter type is valid
    try:
        letter_enum = LetterType[letter_type.upper()]
    except KeyError:
        flash('Invalid letter type selected.', 'danger')
        return redirect(url_for('advanced_letters.index'))
    
    # Get form data
    form_data = request.form.to_dict()
    letter_content = form_data.pop('letter_content', '')
    letter_id = form_data.pop('letter_id', None)
    
    # Save or update the letter
    if letter_id:
        # Update existing letter
        letter = IRSLetter.query.filter_by(id=letter_id, user_id=current_user.id).first()
        if not letter:
            flash('Letter not found.', 'danger')
            return redirect(url_for('advanced_letters.index'))
        
        letter.data = form_data
        letter.data['content'] = letter_content
        letter.updated_at = datetime.utcnow()
    else:
        # Create new letter
        letter = IRSLetter(
            user_id=current_user.id,
            letter_type=letter_enum,
            data={
                'template_id': template_id,
                'content': letter_content,
                **form_data
            },
            status='draft'
        )
        db.session.add(letter)
    
    db.session.commit()
    
    # Log the action
    log_entry = AuditLog(
        user_id=current_user.id,
        action=f"{'Updated' if letter_id else 'Created'} {letter_type} letter",
        details=f"Letter ID: {letter.id}",
        ip_address=request.remote_addr
    )
    db.session.add(log_entry)
    db.session.commit()
    
    flash(f"Letter {'updated' if letter_id else 'created'} successfully.", 'success')
    return redirect(url_for('letter.view_letter', letter_id=letter.id))

@advanced_letter_bp.route('/api/ai-suggest', methods=['POST'])
@login_required
@requires_access_level('enhanced_ai_support')
def ai_suggest():
    """Get AI-suggested content for a letter section"""
    data = request.get_json()
    
    letter_type = data.get('letter_type')
    field_name = data.get('field_name')
    context = data.get('context', {})
    
    # Generate AI suggestion
    suggestion = generate_ai_suggestion(letter_type, field_name, context)
    
    return jsonify({'suggestion': suggestion})

def get_letter_categories():
    """Get list of available letter categories"""
    categories = {
        'penalties': {
            'name': 'IRS Penalty Relief',
            'description': 'Letters requesting relief from IRS penalties',
            'types': [
                {'id': 'PENALTY_ABATEMENT', 'name': 'Penalty Abatement Request'},
                {'id': 'REASONABLE_CAUSE', 'name': 'Reasonable Cause Explanation'},
                {'id': 'LATE_FILING_RELIEF', 'name': 'Late Filing Relief Request'}
            ]
        },
        'responses': {
            'name': 'IRS Notice Responses',
            'description': 'Responses to IRS notices and audits',
            'types': [
                {'id': 'AUDIT_RESPONSE', 'name': 'Audit Response Letter'},
                {'id': 'CP2000_RESPONSE', 'name': 'CP2000 Notice Response'},
                {'id': 'INSTALLMENT_REQUEST', 'name': 'Installment Agreement Request'},
                {'id': 'OFFER_IN_COMPROMISE', 'name': 'Offer in Compromise'},
                {'id': 'INNOCENT_SPOUSE_RELIEF', 'name': 'Innocent Spouse Relief Request'}
            ]
        },
        'business': {
            'name': 'Business Tax Issues',
            'description': 'Letters addressing specific business tax matters',
            'types': [
                {'id': 'EMPLOYMENT_TAX_ISSUE', 'name': 'Employment Tax Issue Response'},
                {'id': 'BACKUP_WITHHOLDING', 'name': 'Backup Withholding Relief'},
                {'id': 'ESTIMATED_TAX_PENALTY', 'name': 'Estimated Tax Penalty Relief'},
                {'id': 'TRUST_FUND_RECOVERY', 'name': 'Trust Fund Recovery Penalty Response'}
            ]
        }
    }
    
    return categories

def get_letter_templates(letter_type):
    """Get templates for a specific letter type"""
    # Map of letter types to their templates
    template_map = {
        LetterType.PENALTY_ABATEMENT: [
            {
                'id': 'simple_abatement',
                'name': 'Simple Penalty Abatement',
                'description': 'Basic request for first-time penalty abatement',
                'complexity': 'basic'
            },
            {
                'id': 'detailed_abatement',
                'name': 'Detailed Penalty Abatement',
                'description': 'Comprehensive penalty abatement with supporting evidence and legal references',
                'complexity': 'advanced'
            }
        ],
        LetterType.REASONABLE_CAUSE: [
            {
                'id': 'health_issue',
                'name': 'Health-Related Reasonable Cause',
                'description': 'Reasonable cause explanation based on health issues',
                'complexity': 'basic'
            },
            {
                'id': 'disaster',
                'name': 'Natural Disaster Reasonable Cause',
                'description': 'Reasonable cause due to natural disaster or emergency',
                'complexity': 'basic'
            },
            {
                'id': 'professional_advice',
                'name': 'Reliance on Professional Advice',
                'description': 'Reasonable cause based on reliance on tax professional',
                'complexity': 'intermediate'
            }
        ],
        LetterType.AUDIT_RESPONSE: [
            {
                'id': 'initial_response',
                'name': 'Initial Audit Response',
                'description': 'First response to an IRS audit notice',
                'complexity': 'intermediate'
            },
            {
                'id': 'documentation_response',
                'name': 'Documentation Submission',
                'description': 'Response with supporting documentation for audited items',
                'complexity': 'advanced'
            },
            {
                'id': 'disagreement_response',
                'name': 'Audit Findings Disagreement',
                'description': 'Response disagreeing with audit findings with legal justification',
                'complexity': 'advanced'
            }
        ],
        LetterType.CP2000_RESPONSE: [
            {
                'id': 'agreement',
                'name': 'CP2000 Agreement Response',
                'description': 'Response agreeing with CP2000 notice changes',
                'complexity': 'basic'
            },
            {
                'id': 'partial_agreement',
                'name': 'CP2000 Partial Agreement',
                'description': 'Response agreeing with some changes and disputing others',
                'complexity': 'intermediate'
            },
            {
                'id': 'disagreement',
                'name': 'CP2000 Disagreement Response',
                'description': 'Response disputing CP2000 notice changes with evidence',
                'complexity': 'advanced'
            }
        ],
        LetterType.EMPLOYMENT_TAX_ISSUE: [
            {
                'id': 'classification',
                'name': 'Worker Classification Response',
                'description': 'Response to employee/contractor classification issues',
                'complexity': 'advanced'
            },
            {
                'id': 'tax_deposit',
                'name': 'Employment Tax Deposit Response',
                'description': 'Response to employment tax deposit issues',
                'complexity': 'intermediate'
            }
        ]
    }
    
    # Return templates for the specified letter type, or empty list if not found
    return template_map.get(letter_type, [])

def get_letter_template_by_id(letter_type, template_id):
    """Get a specific template by ID"""
    templates = get_letter_templates(letter_type)
    for template in templates:
        if template['id'] == template_id:
            return template
    return None

def get_template_form_fields(letter_type, template_id):
    """Get form fields for a specific template"""
    # Common fields for all letter types
    common_fields = [
        {
            'id': 'taxpayer_name',
            'label': 'Taxpayer Name',
            'type': 'text',
            'required': True,
            'placeholder': 'Enter your full legal name or business name'
        },
        {
            'id': 'taxpayer_id',
            'label': 'Taxpayer ID (SSN/EIN)',
            'type': 'text',
            'required': True,
            'placeholder': 'Enter your SSN or EIN'
        },
        {
            'id': 'address',
            'label': 'Address',
            'type': 'textarea',
            'required': True,
            'placeholder': 'Enter your full mailing address'
        },
        {
            'id': 'tax_year',
            'label': 'Tax Year(s)',
            'type': 'text',
            'required': True,
            'placeholder': 'Enter the tax year(s) this letter concerns'
        }
    ]
    
    # Template-specific fields
    template_fields = {
        # Penalty Abatement templates
        'simple_abatement': [
            {
                'id': 'notice_number',
                'label': 'IRS Notice Number',
                'type': 'text',
                'required': True,
                'placeholder': 'Enter the IRS notice number (e.g., CP-14)'
            },
            {
                'id': 'notice_date',
                'label': 'Notice Date',
                'type': 'date',
                'required': True
            },
            {
                'id': 'penalty_amount',
                'label': 'Penalty Amount',
                'type': 'text',
                'required': True,
                'placeholder': 'Enter the penalty amount'
            },
            {
                'id': 'previous_compliance',
                'label': 'Previous Tax Compliance History',
                'type': 'textarea',
                'required': True,
                'placeholder': 'Describe your history of filing and paying taxes on time'
            }
        ],
        'detailed_abatement': [
            {
                'id': 'notice_number',
                'label': 'IRS Notice Number',
                'type': 'text',
                'required': True,
                'placeholder': 'Enter the IRS notice number (e.g., CP-14)'
            },
            {
                'id': 'notice_date',
                'label': 'Notice Date',
                'type': 'date',
                'required': True
            },
            {
                'id': 'penalty_amount',
                'label': 'Penalty Amount',
                'type': 'text',
                'required': True,
                'placeholder': 'Enter the penalty amount'
            },
            {
                'id': 'penalty_type',
                'label': 'Penalty Type',
                'type': 'select',
                'required': True,
                'options': [
                    {'value': 'failure_to_file', 'label': 'Failure to File'},
                    {'value': 'failure_to_pay', 'label': 'Failure to Pay'},
                    {'value': 'estimated_tax', 'label': 'Estimated Tax Penalty'},
                    {'value': 'other', 'label': 'Other (specify in explanation)'}
                ]
            },
            {
                'id': 'previous_compliance',
                'label': 'Previous Tax Compliance History',
                'type': 'textarea',
                'required': True,
                'placeholder': 'Describe your history of filing and paying taxes on time'
            },
            {
                'id': 'abatement_reason',
                'label': 'Detailed Reason for Abatement Request',
                'type': 'textarea',
                'required': True,
                'placeholder': 'Provide a detailed explanation for your abatement request'
            },
            {
                'id': 'supporting_documents',
                'label': 'Supporting Documents',
                'type': 'textarea',
                'required': False,
                'placeholder': 'List any supporting documents you are attaching'
            }
        ],
        # Audit Response templates
        'initial_response': [
            {
                'id': 'audit_notice_number',
                'label': 'Audit Notice Number',
                'type': 'text',
                'required': True,
                'placeholder': 'Enter the audit notice number'
            },
            {
                'id': 'audit_date',
                'label': 'Audit Notice Date',
                'type': 'date',
                'required': True
            },
            {
                'id': 'audit_items',
                'label': 'Items Under Audit',
                'type': 'textarea',
                'required': True,
                'placeholder': 'List the specific items being audited'
            },
            {
                'id': 'response_overview',
                'label': 'Response Overview',
                'type': 'textarea',
                'required': True,
                'placeholder': 'Provide a summary of your response to the audit notice'
            }
        ],
        # Other templates would have their specific fields here
    }
    
    # Combine common fields with template-specific fields
    return common_fields + template_fields.get(template_id, [])

def generate_letter_content(letter_type, template_id, form_data):
    """Generate letter content based on template and form data"""
    # Get template data
    template = get_letter_template_by_id(letter_type, template_id)
    if not template:
        return "Error: Template not found."
    
    # For basic templates, we can use a predefined structure with form data inserted
    letter_content = ""
    
    # Add current date
    letter_content += datetime.now().strftime("%B %d, %Y") + "\n\n"
    
    # Add addressee (IRS)
    letter_content += "Internal Revenue Service\n"
    letter_content += "[IRS Address will be added before sending]\n\n"
    
    # Add subject line based on letter type
    if letter_type == LetterType.PENALTY_ABATEMENT:
        letter_content += f"Re: Request for Penalty Abatement - {form_data.get('taxpayer_name', '[Name]')}, Tax ID: {form_data.get('taxpayer_id', '[ID]')}, Tax Year(s): {form_data.get('tax_year', '[Year]')}\n\n"
    elif letter_type == LetterType.AUDIT_RESPONSE:
        letter_content += f"Re: Response to Audit Notice {form_data.get('audit_notice_number', '[Notice #]')} - {form_data.get('taxpayer_name', '[Name]')}, Tax ID: {form_data.get('taxpayer_id', '[ID]')}, Tax Year(s): {form_data.get('tax_year', '[Year]')}\n\n"
    else:
        letter_content += f"Re: {letter_type.value.replace('_', ' ').title()} - {form_data.get('taxpayer_name', '[Name]')}, Tax ID: {form_data.get('taxpayer_id', '[ID]')}, Tax Year(s): {form_data.get('tax_year', '[Year]')}\n\n"
    
    # Add greeting
    letter_content += "To Whom It May Concern:\n\n"
    
    # Add introduction
    if letter_type == LetterType.PENALTY_ABATEMENT:
        if template_id == 'simple_abatement':
            letter_content += f"I am writing to request an abatement of the penalty in the amount of {form_data.get('penalty_amount', '[amount]')} as shown on the notice dated {form_data.get('notice_date', '[date]')}.\n\n"
            letter_content += "I have a history of filing and paying my taxes on time:\n\n"
            letter_content += f"{form_data.get('previous_compliance', '[compliance history]')}\n\n"
            letter_content += "Based on my history of compliance and this being a first-time occurrence, I respectfully request that the penalty be abated under the First Time Abatement administrative waiver.\n\n"
        elif template_id == 'detailed_abatement':
            letter_content += f"I am writing to request an abatement of the {form_data.get('penalty_type', '[penalty type]').replace('_', ' ').title()} penalty in the amount of {form_data.get('penalty_amount', '[amount]')} as shown on the notice dated {form_data.get('notice_date', '[date]')}.\n\n"
            letter_content += "I have a history of filing and paying my taxes on time:\n\n"
            letter_content += f"{form_data.get('previous_compliance', '[compliance history]')}\n\n"
            letter_content += "I am requesting this abatement for the following reason(s):\n\n"
            letter_content += f"{form_data.get('abatement_reason', '[abatement reason]')}\n\n"
            
            if form_data.get('supporting_documents'):
                letter_content += "I have included the following supporting documentation with this letter:\n\n"
                letter_content += f"{form_data.get('supporting_documents', '[supporting documents]')}\n\n"
    
    elif letter_type == LetterType.AUDIT_RESPONSE:
        if template_id == 'initial_response':
            letter_content += f"I am writing in response to your audit notice {form_data.get('audit_notice_number', '[notice #]')} dated {form_data.get('audit_date', '[date]')}.\n\n"
            letter_content += f"The notice indicates that you are examining the following items on my tax return for {form_data.get('tax_year', '[year]')}:\n\n"
            letter_content += f"{form_data.get('audit_items', '[audit items]')}\n\n"
            letter_content += f"{form_data.get('response_overview', '[response overview]')}\n\n"
    
    # Add closing
    letter_content += "If you have any questions or need additional information, please contact me at [your phone number] or [your email].\n\n"
    letter_content += "Thank you for your consideration of this matter.\n\n"
    letter_content += "Sincerely,\n\n\n"
    letter_content += f"{form_data.get('taxpayer_name', '[Name]')}\n"
    letter_content += f"Tax ID: {form_data.get('taxpayer_id', '[ID]')}\n"
    letter_content += f"{form_data.get('address', '[Address]')}"
    
    return letter_content

def generate_ai_suggestion(letter_type, field_name, context):
    """Generate AI-suggested content for a letter field"""
    # Create a system prompt based on the letter type and field
    system_prompt = f"""
    You are an AI tax letter specialist for the .fylr tax automation platform.
    Generate appropriate content for a {letter_type} letter, specifically for the '{field_name}' section.
    
    The content should be professional, concise, and appropriate for IRS communication.
    Focus on factual statements and relevant details that would strengthen the taxpayer's position.
    Avoid making false claims or exaggerated statements.
    """
    
    # Create user message with context
    user_message = f"""
    Please suggest content for the '{field_name}' section of my {letter_type} letter.
    
    Here is the context:
    {json.dumps(context, indent=2)}
    
    The suggested content should be specific to my situation and ready to use in the letter.
    """
    
    # Get response from OpenAI
    suggestion = get_openai_response(system_prompt, user_message)
    
    return suggestion