"""
Export Utilities Module

This module provides functions for exporting tax strategies, forms,
and other data in various formats (PDF, JSON, HTML).
"""

from flask import render_template, make_response, jsonify, send_file
import json
from datetime import datetime
import tempfile
import os
from weasyprint import HTML

def export_strategy_as_pdf(strategy):
    """
    Export a tax strategy as a PDF document
    
    Args:
        strategy: The TaxStrategy object to export
        
    Returns:
        Flask response with PDF attachment
    """
    # Generate HTML content first
    html_content = render_template('export/strategy_html.html', 
                                  strategy=strategy)
    
    # Create a temporary file for the PDF
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
        temp_path = temp_file.name
    
    # Convert HTML to PDF
    HTML(string=html_content).write_pdf(temp_path)
    
    # Create response with PDF attachment
    filename = f"tax_strategy_{strategy.strategy_name.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    response = make_response(send_file(temp_path, as_attachment=True, 
                                      download_name=filename))
    
    # Clean up the temporary file (will be deleted when the request is complete)
    os.unlink(temp_path)
    
    return response

def export_strategy_as_json(strategy):
    """
    Export a tax strategy as a JSON file
    
    Args:
        strategy: The TaxStrategy object to export
        
    Returns:
        Flask response with JSON attachment
    """
    # Create a dictionary with strategy data
    strategy_data = {
        'strategy_name': strategy.strategy_name,
        'description': strategy.description,
        'estimated_savings': strategy.estimated_savings,
        'implementation_steps': strategy.implementation_steps,
        'qualifications': strategy.qualifications,
        'tax_year': strategy.tax_year,
        'tier': strategy.tier,
        'created_at': strategy.created_at.isoformat(),
        'disclaimer': 'This tax strategy is provided for informational purposes only and does not constitute professional tax advice. Always consult with a qualified tax professional before implementing any tax strategy.'
    }
    
    # Add business context if available
    if hasattr(strategy, 'data') and strategy.data:
        # Only include non-sensitive business context data
        if 'business_data' in strategy.data:
            business_data = strategy.data['business_data'].copy()
            # Remove any potentially sensitive information
            if 'ein' in business_data:
                del business_data['ein']
            if 'ssn' in business_data:
                del business_data['ssn']
            strategy_data['business_context'] = business_data
        
        # Include relevant questionnaire answers if available
        if 'questionnaire_answers' in strategy.data:
            strategy_data['answers'] = strategy.data['questionnaire_answers']
    
    # Create JSON response with attachment
    response = jsonify(strategy_data)
    response.headers['Content-Disposition'] = f'attachment; filename=tax_strategy_{strategy.strategy_name.replace(" ", "_").lower()}_{datetime.now().strftime("%Y%m%d")}.json'
    
    return response

def export_strategy_as_html(strategy):
    """
    Export a tax strategy as an HTML file
    
    Args:
        strategy: The TaxStrategy object to export
        
    Returns:
        Flask response with HTML attachment
    """
    # Generate HTML content
    html_content = render_template('export/strategy_html.html', 
                                  strategy=strategy)
    
    # Create response with HTML attachment
    response = make_response(html_content)
    response.headers['Content-Type'] = 'text/html'
    response.headers['Content-Disposition'] = f'attachment; filename=tax_strategy_{strategy.strategy_name.replace(" ", "_").lower()}_{datetime.now().strftime("%Y%m%d")}.html'
    
    return response

def export_form_as_pdf(form):
    """
    Export a tax form as a PDF document
    
    Args:
        form: The TaxForm object to export
        
    Returns:
        Flask response with PDF attachment
    """
    # Generate HTML content first
    html_content = render_template('export/form_html.html', 
                                  form=form)
    
    # Create a temporary file for the PDF
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
        temp_path = temp_file.name
    
    # Convert HTML to PDF
    HTML(string=html_content).write_pdf(temp_path)
    
    # Create response with PDF attachment
    filename = f"tax_form_{form.form_type.name.lower()}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    response = make_response(send_file(temp_path, as_attachment=True, 
                                      download_name=filename))
    
    # Clean up the temporary file (will be deleted when the request is complete)
    os.unlink(temp_path)
    
    return response

def export_form_as_json(form):
    """
    Export a tax form as a JSON file
    
    Args:
        form: The TaxForm object to export
        
    Returns:
        Flask response with JSON attachment
    """
    # Create a dictionary with form data
    form_data = {
        'form_type': form.form_type.name,
        'tax_year': form.tax_year,
        'data': form.data,
        'status': form.status,
        'created_at': form.created_at.isoformat(),
        'updated_at': form.updated_at.isoformat() if form.updated_at else None,
        'disclaimer': 'This tax form data is provided for informational purposes only and does not constitute a filed tax return. Always consult with a qualified tax professional before filing tax forms.'
    }
    
    # Create JSON response with attachment
    response = jsonify(form_data)
    response.headers['Content-Disposition'] = f'attachment; filename=tax_form_{form.form_type.name.lower()}_{datetime.now().strftime("%Y%m%d")}.json'
    
    return response