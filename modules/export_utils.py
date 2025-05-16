"""
Document Export Utilities

This module provides utilities for exporting tax documents in various formats.
"""

from flask import Blueprint, render_template, send_file, request, jsonify, current_app
from flask_login import login_required, current_user
import json
import os
import tempfile
import datetime
from weasyprint import HTML, CSS
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from app.models import TaxForm, IRSLetter, TaxStrategy

# Create blueprint
export_bp = Blueprint('export', __name__, url_prefix='/export')

@export_bp.route('/form/<int:form_id>')
@login_required
def export_form(form_id):
    """Export a tax form in the requested format"""
    # Get the form
    form = TaxForm.query.filter_by(id=form_id, user_id=current_user.id).first_or_404()
    
    # Get requested format
    export_format = request.args.get('format', 'pdf')
    
    if export_format == 'pdf':
        return export_form_pdf(form)
    elif export_format == 'json':
        return export_form_json(form)
    elif export_format == 'html':
        return export_form_html(form)
    else:
        return jsonify({'error': 'Unsupported export format'}), 400

@export_bp.route('/letter/<int:letter_id>')
@login_required
def export_letter(letter_id):
    """Export an IRS letter in the requested format"""
    # Get the letter
    letter = IRSLetter.query.filter_by(id=letter_id, user_id=current_user.id).first_or_404()
    
    # Get requested format
    export_format = request.args.get('format', 'pdf')
    
    if export_format == 'pdf':
        return export_letter_pdf(letter)
    elif export_format == 'json':
        return export_letter_json(letter)
    elif export_format == 'html':
        return export_letter_html(letter)
    else:
        return jsonify({'error': 'Unsupported export format'}), 400

@export_bp.route('/strategy/<int:strategy_id>')
@login_required
def export_strategy(strategy_id):
    """Export a tax strategy in the requested format"""
    # Get the strategy
    strategy = TaxStrategy.query.filter_by(id=strategy_id, user_id=current_user.id).first_or_404()
    
    # Get requested format
    export_format = request.args.get('format', 'pdf')
    
    if export_format == 'pdf':
        return export_strategy_pdf(strategy)
    elif export_format == 'json':
        return export_strategy_json(strategy)
    elif export_format == 'html':
        return export_strategy_html(strategy)
    else:
        return jsonify({'error': 'Unsupported export format'}), 400

def export_form_pdf(form):
    """Export a tax form as PDF"""
    # Generate the HTML representation of the form
    html_content = render_template('export/form_pdf.html', form=form)
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
        temp_filename = temp_file.name
    
    # Convert HTML to PDF
    HTML(string=html_content).write_pdf(
        temp_filename,
        stylesheets=[CSS(string='@page { size: letter; margin: 1cm }')]
    )
    
    # Generate a meaningful filename
    filename = f"{form.form_type.value}_tax_year_{form.tax_year}_{datetime.date.today().strftime('%Y%m%d')}.pdf"
    
    # Send the file
    return send_file(
        temp_filename,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )

def export_form_json(form):
    """Export a tax form as JSON"""
    # Prepare form data
    form_data = {
        'id': form.id,
        'form_type': form.form_type.value,
        'tax_year': form.tax_year,
        'status': form.status,
        'data': form.data,
        'created_at': form.created_at.isoformat(),
        'updated_at': form.updated_at.isoformat()
    }
    
    # Generate a meaningful filename
    filename = f"{form.form_type.value}_tax_year_{form.tax_year}_{datetime.date.today().strftime('%Y%m%d')}.json"
    
    # Return JSON response with attachment headers
    response = jsonify(form_data)
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

def export_form_html(form):
    """Export a tax form as HTML (email-ready)"""
    # Generate the HTML representation of the form
    html_content = render_template('export/form_html.html', form=form)
    
    # Generate a meaningful filename
    filename = f"{form.form_type.value}_tax_year_{form.tax_year}_{datetime.date.today().strftime('%Y%m%d')}.html"
    
    # Create a response with the HTML content
    response = current_app.response_class(
        response=html_content,
        status=200,
        mimetype='text/html'
    )
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

def export_letter_pdf(letter):
    """Export an IRS letter as PDF"""
    # Generate the HTML representation of the letter
    html_content = render_template('export/letter_pdf.html', letter=letter)
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
        temp_filename = temp_file.name
    
    # Convert HTML to PDF
    HTML(string=html_content).write_pdf(
        temp_filename,
        stylesheets=[CSS(string='@page { size: letter; margin: 1cm }')]
    )
    
    # Generate a meaningful filename
    filename = f"IRS_letter_{letter.letter_type.value}_{datetime.date.today().strftime('%Y%m%d')}.pdf"
    
    # Send the file
    return send_file(
        temp_filename,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )

def export_letter_json(letter):
    """Export an IRS letter as JSON"""
    # Prepare letter data
    letter_data = {
        'id': letter.id,
        'letter_type': letter.letter_type.value,
        'data': letter.data,
        'status': letter.status,
        'created_at': letter.created_at.isoformat(),
        'updated_at': letter.updated_at.isoformat()
    }
    
    # Generate a meaningful filename
    filename = f"IRS_letter_{letter.letter_type.value}_{datetime.date.today().strftime('%Y%m%d')}.json"
    
    # Return JSON response with attachment headers
    response = jsonify(letter_data)
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

def export_letter_html(letter):
    """Export an IRS letter as HTML (email-ready)"""
    # Generate the HTML representation of the letter
    html_content = render_template('export/letter_html.html', letter=letter)
    
    # Generate a meaningful filename
    filename = f"IRS_letter_{letter.letter_type.value}_{datetime.date.today().strftime('%Y%m%d')}.html"
    
    # Create a response with the HTML content
    response = current_app.response_class(
        response=html_content,
        status=200,
        mimetype='text/html'
    )
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

def export_strategy_pdf(strategy):
    """Export a tax strategy as PDF"""
    # Generate the HTML representation of the strategy
    html_content = render_template('export/strategy_pdf.html', strategy=strategy)
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
        temp_filename = temp_file.name
    
    # Convert HTML to PDF
    HTML(string=html_content).write_pdf(
        temp_filename,
        stylesheets=[CSS(string='@page { size: letter; margin: 1cm }')]
    )
    
    # Generate a meaningful filename
    filename = f"Tax_Strategy_{strategy.strategy_name.replace(' ', '_')}_{datetime.date.today().strftime('%Y%m%d')}.pdf"
    
    # Send the file
    return send_file(
        temp_filename,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )

def export_strategy_json(strategy):
    """Export a tax strategy as JSON"""
    # Prepare strategy data
    strategy_data = {
        'id': strategy.id,
        'strategy_name': strategy.strategy_name,
        'description': strategy.description,
        'estimated_savings': strategy.estimated_savings,
        'answers': strategy.answers,
        'status': strategy.status,
        'created_at': strategy.created_at.isoformat()
    }
    
    # Generate a meaningful filename
    filename = f"Tax_Strategy_{strategy.strategy_name.replace(' ', '_')}_{datetime.date.today().strftime('%Y%m%d')}.json"
    
    # Return JSON response with attachment headers
    response = jsonify(strategy_data)
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

def export_strategy_html(strategy):
    """Export a tax strategy as HTML (email-ready)"""
    # Generate the HTML representation of the strategy
    html_content = render_template('export/strategy_html.html', strategy=strategy)
    
    # Generate a meaningful filename
    filename = f"Tax_Strategy_{strategy.strategy_name.replace(' ', '_')}_{datetime.date.today().strftime('%Y%m%d')}.html"
    
    # Create a response with the HTML content
    response = current_app.response_class(
        response=html_content,
        status=200,
        mimetype='text/html'
    )
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

def send_email_export(recipient_email, subject, html_content, text_content=None):
    """Send an email with the exported content"""
    # This would use SMTP to send emails in a production environment
    # For demo purposes, we'll just show a placeholder implementation
    
    # Create a MIMEMultipart message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = "noreply@fylr.app"
    msg['To'] = recipient_email
    
    # Add plain text version if provided
    if text_content:
        msg.attach(MIMEText(text_content, 'plain'))
    
    # Add HTML version
    msg.attach(MIMEText(html_content, 'html'))
    
    # In a real implementation, you would send the email:
    # with smtplib.SMTP_SSL('smtp.example.com', 465) as server:
    #     server.login(username, password)
    #     server.send_message(msg)
    
    return True