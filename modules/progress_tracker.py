"""
Tax Preparation Progress Tracker Module for .fylr

This module tracks progress of tax preparation activities, visualizes completion status,
and provides AI-driven recommendations for tax savings.
"""

from flask import Blueprint, render_template, jsonify, request, abort, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import json
from app.app import db
from app.models import TaxForm, IRSLetter, TaxStrategy, User
from app.access_control import requires_access_level, unlock_tool
from ai.analyzer import generate_tax_strategies
import calendar

# Create blueprint
progress_bp = Blueprint('progress', __name__, url_prefix='/progress')

@progress_bp.route('/')
@login_required
def index():
    """Main progress visualization page"""
    # Get current tax year (for real app, this would be determined by configuration or user selection)
    tax_year = datetime.now().year
    if datetime.now().month > 3:  # After April, we're usually working on current year taxes
        tax_year = datetime.now().year
    else:
        tax_year = datetime.now().year - 1
    
    # Get the user's tax preparation progress
    progress = calculate_tax_prep_progress(current_user.id, tax_year)
    
    # Get tax timeline events
    timeline = get_tax_timeline(current_user.id, tax_year)
    
    # Get required forms and their completion status
    forms = get_forms_status(current_user.id, tax_year)
    
    # Get tax saving recommendations (AI-powered)
    recommendations = get_tax_saving_recommendations(current_user.id, tax_year)
    
    return render_template('dashboard/progress.html', 
                          progress=progress, 
                          timeline=timeline, 
                          forms=forms, 
                          recommendations=recommendations,
                          tax_year=tax_year)

@progress_bp.route('/api/progress')
@login_required
def api_progress():
    """API endpoint to get current progress data (for AJAX updates)"""
    tax_year = request.args.get('tax_year', datetime.now().year, type=int)
    progress = calculate_tax_prep_progress(current_user.id, tax_year)
    return jsonify(progress)

def calculate_tax_prep_progress(user_id, tax_year):
    """Calculate tax preparation progress for a user"""
    # Get user's tax forms for the specified year
    forms = TaxForm.query.filter_by(user_id=user_id, tax_year=tax_year).all()
    
    # In a production app, this would calculate actual progress based on form completeness
    # For demo purposes, we'll calculate synthetic progress
    
    total_forms = len(forms) or 1  # Avoid division by zero
    completed_forms = sum(1 for form in forms if form.status == 'completed')
    in_progress_forms = sum(1 for form in forms if form.status == 'in_progress')
    
    # Calculate percentages for different stages
    information_percentage = min(100, (completed_forms + (in_progress_forms * 0.5)) / total_forms * 100)
    forms_percentage = min(100, completed_forms / total_forms * 100)
    
    # Review percentage is based on completion - only forms that are completed can be reviewed
    review_percentage = min(100, completed_forms / total_forms * 100 * 0.8)  # Assume 80% of completed forms are reviewed
    
    # Overall completion percentage is weighted average of the three stages
    completion_percentage = round((information_percentage * 0.3) + (forms_percentage * 0.5) + (review_percentage * 0.2))
    
    return {
        'completion_percentage': completion_percentage,
        'information_percentage': round(information_percentage),
        'forms_percentage': round(forms_percentage),
        'review_percentage': round(review_percentage)
    }

def get_tax_timeline(user_id, tax_year):
    """Generate tax timeline for a user"""
    now = datetime.now()
    
    # Create a timeline with key tax dates
    timeline = []
    
    # Questionnaire completion (today or past)
    timeline.append({
        'date': 'Today' if now.date() == datetime.today().date() else now.strftime('%b %d, %Y'),
        'title': 'Tax Questionnaire Completed',
        'description': 'Identified required tax forms for your business',
        'icon': 'clipboard-check',
        'completed': True,
        'overdue': False,
        'urgent': False
    })
    
    # Data gathering (2 weeks from today or past date)
    data_gathering_date = now + timedelta(days=14)
    timeline.append({
        'date': data_gathering_date.strftime('%b %d, %Y'),
        'title': 'Financial Data Collection',
        'description': 'Gather all income, expense, and financial records',
        'icon': 'folder',
        'completed': False,
        'overdue': data_gathering_date.date() < now.date(),
        'urgent': data_gathering_date.date() < (now + timedelta(days=7)).date() and data_gathering_date.date() >= now.date()
    })
    
    # Form completion deadline (1 month before tax day)
    # April 15th for most businesses, March 15th for S-corps and partnerships
    is_pass_through = True  # This would be determined by checking the business type
    
    if is_pass_through:
        tax_day = datetime(tax_year, 3, 15)
    else:
        tax_day = datetime(tax_year, 4, 15)
    
    # If tax day falls on weekend, adjust to next business day
    if tax_day.weekday() > 4:  # Saturday or Sunday
        tax_day += timedelta(days=(7 - tax_day.weekday()))
    
    # Form completion deadline (1 month before tax day)
    form_completion_date = tax_day - timedelta(days=30)
    timeline.append({
        'date': form_completion_date.strftime('%b %d, %Y'),
        'title': 'Forms Completion Deadline',
        'description': 'Complete all required tax forms',
        'icon': 'edit',
        'completed': False,
        'overdue': form_completion_date.date() < now.date(),
        'urgent': form_completion_date.date() < (now + timedelta(days=7)).date() and form_completion_date.date() >= now.date()
    })
    
    # Final filing deadline
    timeline.append({
        'date': tax_day.strftime('%b %d, %Y'),
        'title': f'{tax_year} Tax Filing Deadline',
        'description': 'File your business tax returns',
        'icon': 'file-alt',
        'completed': False,
        'overdue': tax_day.date() < now.date(),
        'urgent': tax_day.date() < (now + timedelta(days=7)).date() and tax_day.date() >= now.date()
    })
    
    # Sort timeline by date (completed items first, then by date)
    timeline.sort(key=lambda x: (not x['completed'], datetime.strptime(x['date'], '%b %d, %Y') if x['date'] != 'Today' else now))
    
    return timeline

def get_forms_status(user_id, tax_year):
    """Get status of required tax forms for a user"""
    # Get user's tax forms
    user_forms = TaxForm.query.filter_by(user_id=user_id, tax_year=tax_year).all()
    
    # Map of form IDs to their statuses
    form_status_map = {form.form_type.value: form.status for form in user_forms}
    
    # This would normally come from the questionnaire results,
    # but for now we'll create a sample list of required forms
    required_forms = [
        {
            'id': 'schedule_c',
            'name': 'Schedule C (Form 1040)',
            'description': 'Profit or Loss From Business',
            'deadline': 'April 15',
            'category': 'core',
            'complexity': 'basic'
        },
        {
            'id': 'schedule_se',
            'name': 'Schedule SE (Form 1040)',
            'description': 'Self-Employment Tax',
            'deadline': 'April 15',
            'category': 'core',
            'complexity': 'basic'
        },
        {
            'id': '4562',
            'name': 'Form 4562',
            'description': 'Depreciation and Amortization',
            'deadline': 'April 15',
            'category': 'deduction',
            'complexity': 'intermediate'
        },
        {
            'id': '1099nec',
            'name': 'Form 1099-NEC',
            'description': 'Nonemployee Compensation',
            'deadline': 'January 31',
            'category': 'information',
            'complexity': 'basic'
        },
        {
            'id': 'ca_540',
            'name': 'CA Form 540',
            'description': 'California Resident Income Tax Return',
            'deadline': 'April 15',
            'category': 'state',
            'complexity': 'intermediate'
        }
    ]
    
    # Assign status to each form
    for form in required_forms:
        # Check if we have this form in our database
        if form['id'] in form_status_map:
            form['status'] = form_status_map[form['id']]
        else:
            form['status'] = 'not_started'
        
        # URL for editing the form
        form['url'] = url_for('form.edit_form', form_type=form['id'])
    
    return required_forms

def get_tax_saving_recommendations(user_id, tax_year):
    """Generate AI-powered tax saving recommendations"""
    user = User.query.get(user_id)
    
    # For basic plan users, we return an empty list (template handles this case)
    if user.plan == 'basic':
        return []
    
    # For paid tiers, generate recommendations based on business information
    recommendations = [
        {
            'icon': 'building',
            'title': 'S-Corporation Election',
            'description': 'Based on your business profile, electing S-Corporation status could save on self-employment taxes.',
            'potential_savings': '$2,500 - $5,000',
            'url': '#',  # This would link to a detailed page in a real app
            'tier': 'fylr_plus'
        },
        {
            'icon': 'home',
            'title': 'Home Office Deduction',
            'description': 'You may qualify for a home office deduction based on the exclusive use of part of your home for business.',
            'potential_savings': '$1,200 - $2,400',
            'url': '#',
            'tier': 'fylr_plus'
        },
        {
            'icon': 'car',
            'title': 'Vehicle Expense Optimization',
            'description': 'Switching from standard mileage to actual expenses may be more beneficial based on your vehicle usage.',
            'potential_savings': '$800 - $1,500',
            'url': '#',
            'tier': 'pro'
        },
        {
            'icon': 'piggy-bank',
            'title': 'Retirement Plan Contribution',
            'description': 'Setting up a SEP IRA or Solo 401(k) could significantly reduce your taxable income.',
            'potential_savings': '$5,000 - $15,000',
            'url': '#',
            'tier': 'pro'
        }
    ]
    
    # Filter recommendations based on the user's plan
    if user.plan == 'fylr_plus':
        recommendations = [r for r in recommendations if r['tier'] == 'fylr_plus']
    
    return recommendations