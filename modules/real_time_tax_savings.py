"""
Real-Time Tax Saving Recommendations Module

This module provides dynamic, personalized tax saving suggestions based on
user data, business context, and tax law changes.
"""

from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app.app import db
from app.models import User, TaxForm, TaxStrategy, AuditLog, UserPlan
from app.access_control import requires_access_level, unlock_tool
from ai.tax_strategy import generate_detailed_strategies
import json
from datetime import datetime

# Create blueprint
tax_savings_bp = Blueprint('tax_savings', __name__, url_prefix='/tax-savings')

@tax_savings_bp.route('/')
@login_required
def index():
    """Display real-time tax saving recommendations dashboard"""
    # Get current tax year
    tax_year = request.args.get('tax_year', datetime.now().year, type=int)
    
    # Get user's tax forms and data for context
    user_forms = TaxForm.query.filter_by(user_id=current_user.id, tax_year=tax_year).all()
    
    # Get saved tax strategies
    saved_strategies = TaxStrategy.query.filter_by(user_id=current_user.id, status='active').all()
    
    # Get personalized recommendations based on user data
    recommendations = generate_recommendations(current_user, user_forms, tax_year)
    
    # Get time-sensitive opportunities
    time_sensitive = get_time_sensitive_opportunities(tax_year)
    
    # Get tax law updates relevant to the user
    tax_updates = get_relevant_tax_updates(current_user, tax_year)
    
    # Get industry-specific recommendations
    industry_recommendations = get_industry_recommendations(current_user)
    
    # Calculate potential savings
    total_potential_savings = calculate_total_potential_savings(recommendations)
    
    return render_template('tax_savings/index.html',
                        recommendations=recommendations,
                        time_sensitive=time_sensitive,
                        tax_updates=tax_updates,
                        industry_recommendations=industry_recommendations,
                        saved_strategies=saved_strategies,
                        total_potential_savings=total_potential_savings,
                        tax_year=tax_year)

@tax_savings_bp.route('/strategy/<strategy_id>')
@login_required
def view_strategy(strategy_id):
    """View details of a specific tax saving strategy"""
    strategy = TaxStrategy.query.filter_by(id=strategy_id, user_id=current_user.id).first_or_404()
    
    # Get implementation steps for this strategy
    implementation_steps = get_strategy_implementation_steps(strategy)
    
    # Get related strategies
    related_strategies = get_related_strategies(strategy)
    
    return render_template('tax_savings/strategy_detail.html',
                        strategy=strategy,
                        implementation_steps=implementation_steps,
                        related_strategies=related_strategies)

@tax_savings_bp.route('/save-strategy', methods=['POST'])
@login_required
def save_strategy():
    """Save a tax strategy to the user's account"""
    strategy_data = request.get_json()
    
    # Create new TaxStrategy record
    new_strategy = TaxStrategy(
        user_id=current_user.id,
        strategy_name=strategy_data.get('name'),
        description=strategy_data.get('description'),
        estimated_savings=strategy_data.get('estimated_savings_value'),
        status='active'
    )
    
    db.session.add(new_strategy)
    db.session.commit()
    
    # Log the action
    log_entry = AuditLog(
        user_id=current_user.id,
        action="Saved tax strategy",
        details=f"Strategy: {strategy_data.get('name')}",
        ip_address=request.remote_addr
    )
    db.session.add(log_entry)
    db.session.commit()
    
    return jsonify({'success': True, 'strategy_id': new_strategy.id})

@tax_savings_bp.route('/api/recommendations')
@login_required
def api_recommendations():
    """API endpoint to get real-time tax saving recommendations"""
    tax_year = request.args.get('tax_year', datetime.now().year, type=int)
    strategy_type = request.args.get('type', 'all')
    
    # Get user's tax forms for context
    user_forms = TaxForm.query.filter_by(user_id=current_user.id, tax_year=tax_year).all()
    
    # Get personalized recommendations based on user data
    if strategy_type == 'all':
        recommendations = generate_recommendations(current_user, user_forms, tax_year)
    elif strategy_type == 'time_sensitive':
        recommendations = get_time_sensitive_opportunities(tax_year)
    elif strategy_type == 'industry':
        recommendations = get_industry_recommendations(current_user)
    elif strategy_type == 'updates':
        recommendations = get_relevant_tax_updates(current_user, tax_year)
    else:
        recommendations = []
    
    return jsonify(recommendations)

def generate_recommendations(user, forms, tax_year):
    """Generate personalized tax saving recommendations"""
    # Get basic business information from user profile and forms
    business_info = extract_business_info(user, forms)
    
    # Define strategies based on business type and available data
    # In a production app, this would use the AI for truly personalized recommendations
    recommendations = []
    
    # Determine plan-specific recommendations
    if user.plan == UserPlan.BASIC:
        # Basic tier gets a limited set of general recommendations
        recommendations.extend(get_basic_recommendations(business_info))
    elif user.plan == UserPlan.FYLR_PLUS:
        # Plus tier gets more detailed recommendations
        recommendations.extend(get_plus_recommendations(business_info))
    else:  # Pro tier
        # Pro tier gets the most detailed, personalized recommendations
        recommendations.extend(get_pro_recommendations(business_info, forms))
    
    # Add business-type-specific recommendations
    if business_info.get('business_type') == 'sole_proprietor':
        recommendations.extend(get_sole_proprietor_recommendations(business_info, tax_year))
    elif business_info.get('business_type') in ['llc_single', 'llc_multi']:
        recommendations.extend(get_llc_recommendations(business_info, tax_year))
    elif business_info.get('business_type') == 's_corp':
        recommendations.extend(get_s_corp_recommendations(business_info, tax_year))
    elif business_info.get('business_type') == 'c_corp':
        recommendations.extend(get_c_corp_recommendations(business_info, tax_year))
    
    # Sort recommendations by potential savings (highest first)
    recommendations.sort(key=lambda x: x.get('estimated_savings_value', 0), reverse=True)
    
    return recommendations

def extract_business_info(user, forms):
    """Extract business information from user profile and forms"""
    # This would normally extract real business data from the user's profile and forms
    # For demo purposes, we'll return placeholder data
    return {
        'business_type': 'sole_proprietor',
        'industry': 'consulting',
        'revenue': 150000,
        'expenses': 75000,
        'employees': 0,
        'state': 'CA',
        'has_home_office': True,
        'has_vehicle_expenses': True,
        'has_retirement_plan': False,
        'has_health_insurance': True
    }

def get_basic_recommendations(business_info):
    """Get basic tier tax saving recommendations"""
    recommendations = [
        {
            'id': 'basic_expense_tracking',
            'name': 'Improve Expense Tracking',
            'description': 'Set up a dedicated business account and credit card to better track deductible expenses.',
            'category': 'bookkeeping',
            'estimated_savings': '$500-$1,500',
            'estimated_savings_value': 1000,
            'implementation_difficulty': 'Easy',
            'time_required': '1-2 hours',
            'icon': 'credit-card',
            'tier': 'basic'
        },
        {
            'id': 'basic_home_office',
            'name': 'Home Office Deduction',
            'description': 'If you use part of your home exclusively for business, you may be eligible for the home office deduction.',
            'category': 'deductions',
            'estimated_savings': '$1,000-$2,500',
            'estimated_savings_value': 1750,
            'implementation_difficulty': 'Medium',
            'time_required': '2-3 hours',
            'icon': 'home',
            'tier': 'basic'
        },
        {
            'id': 'basic_vehicle_log',
            'name': 'Vehicle Expense Log',
            'description': 'Keep a detailed log of business mileage to maximize your vehicle deduction.',
            'category': 'deductions',
            'estimated_savings': '$500-$2,000',
            'estimated_savings_value': 1250,
            'implementation_difficulty': 'Easy',
            'time_required': 'Ongoing',
            'icon': 'car',
            'tier': 'basic'
        }
    ]
    
    return recommendations

def get_plus_recommendations(business_info):
    """Get plus tier tax saving recommendations"""
    # Include all basic recommendations
    recommendations = get_basic_recommendations(business_info)
    
    # Add Plus-specific recommendations
    plus_recommendations = [
        {
            'id': 'plus_retirement_plan',
            'name': 'Self-Employed Retirement Plan',
            'description': 'Set up a SEP IRA, SIMPLE IRA, or Solo 401(k) to reduce taxable income and save for retirement.',
            'category': 'retirement',
            'estimated_savings': '$2,000-$5,000',
            'estimated_savings_value': 3500,
            'implementation_difficulty': 'Medium',
            'time_required': '3-5 hours',
            'icon': 'piggy-bank',
            'tier': 'plus'
        },
        {
            'id': 'plus_health_insurance',
            'name': 'Self-Employed Health Insurance Deduction',
            'description': 'Deduct health insurance premiums for yourself, your spouse, and dependents.',
            'category': 'deductions',
            'estimated_savings': '$1,500-$4,000',
            'estimated_savings_value': 2750,
            'implementation_difficulty': 'Easy',
            'time_required': '1-2 hours',
            'icon': 'medkit',
            'tier': 'plus'
        },
        {
            'id': 'plus_quarterly_planning',
            'name': 'Quarterly Tax Planning',
            'description': 'Schedule quarterly tax planning sessions to identify deductions and adjust estimated payments.',
            'category': 'planning',
            'estimated_savings': '$1,000-$3,000',
            'estimated_savings_value': 2000,
            'implementation_difficulty': 'Medium',
            'time_required': '2-3 hours per quarter',
            'icon': 'calendar-alt',
            'tier': 'plus'
        }
    ]
    
    recommendations.extend(plus_recommendations)
    return recommendations

def get_pro_recommendations(business_info, forms):
    """Get pro tier tax saving recommendations"""
    # Include all plus recommendations
    recommendations = get_plus_recommendations(business_info)
    
    # Add Pro-specific recommendations
    pro_recommendations = [
        {
            'id': 'pro_entity_structure',
            'name': 'Optimize Business Entity Structure',
            'description': 'Evaluate changing from sole proprietorship to S-Corporation to potentially save on self-employment taxes.',
            'category': 'entity',
            'estimated_savings': '$3,000-$10,000',
            'estimated_savings_value': 6500,
            'implementation_difficulty': 'Complex',
            'time_required': '10+ hours',
            'icon': 'building',
            'tier': 'pro'
        },
        {
            'id': 'pro_tax_loss_harvesting',
            'name': 'Tax Loss Harvesting',
            'description': 'Strategically sell investments with losses to offset capital gains and reduce your tax burden.',
            'category': 'investments',
            'estimated_savings': '$2,000-$8,000',
            'estimated_savings_value': 5000,
            'implementation_difficulty': 'Complex',
            'time_required': '5-8 hours',
            'icon': 'chart-line',
            'tier': 'pro'
        },
        {
            'id': 'pro_cost_segregation',
            'name': 'Cost Segregation Study',
            'description': 'If you own business property, a cost segregation study can accelerate depreciation deductions.',
            'category': 'real_estate',
            'estimated_savings': '$5,000-$20,000',
            'estimated_savings_value': 12500,
            'implementation_difficulty': 'Complex',
            'time_required': '10+ hours',
            'icon': 'building',
            'tier': 'pro'
        },
        {
            'id': 'pro_income_shifting',
            'name': 'Income Shifting Strategies',
            'description': 'Legally shift income to future years or to family members in lower tax brackets.',
            'category': 'planning',
            'estimated_savings': '$3,000-$15,000',
            'estimated_savings_value': 9000,
            'implementation_difficulty': 'Complex',
            'time_required': '8+ hours',
            'icon': 'exchange-alt',
            'tier': 'pro'
        }
    ]
    
    recommendations.extend(pro_recommendations)
    return recommendations

def get_sole_proprietor_recommendations(business_info, tax_year):
    """Get recommendations specific to sole proprietors"""
    recommendations = [
        {
            'id': 'sp_qbi_deduction',
            'name': 'Qualified Business Income Deduction',
            'description': 'As a sole proprietor, you may be eligible for a deduction of up to 20% of your qualified business income.',
            'category': 'deductions',
            'estimated_savings': '$2,000-$7,500',
            'estimated_savings_value': 4750,
            'implementation_difficulty': 'Medium',
            'time_required': '1-3 hours',
            'icon': 'percentage',
            'tier': 'basic'
        },
        {
            'id': 'sp_estimated_taxes',
            'name': 'Optimize Estimated Tax Payments',
            'description': 'Properly calculate and time your quarterly estimated tax payments to avoid penalties while maximizing cash flow.',
            'category': 'planning',
            'estimated_savings': '$500-$2,000',
            'estimated_savings_value': 1250,
            'implementation_difficulty': 'Medium',
            'time_required': '2-4 hours',
            'icon': 'calendar-check',
            'tier': 'plus'
        }
    ]
    
    # Add S-Corp recommendation if income is high enough
    if business_info.get('revenue', 0) > 80000:
        recommendations.append({
            'id': 'sp_s_corp_election',
            'name': 'Consider S-Corporation Election',
            'description': 'With your income level, electing S-Corporation status could save you thousands in self-employment taxes.',
            'category': 'entity',
            'estimated_savings': '$3,000-$12,000',
            'estimated_savings_value': 7500,
            'implementation_difficulty': 'Complex',
            'time_required': '10+ hours',
            'icon': 'file-contract',
            'tier': 'pro'
        })
    
    return recommendations

def get_llc_recommendations(business_info, tax_year):
    """Get recommendations specific to LLCs"""
    recommendations = [
        {
            'id': 'llc_tax_election',
            'name': 'Optimize LLC Tax Classification',
            'description': 'Ensure your LLC has the most advantageous tax classification (disregarded entity, partnership, or S-corporation).',
            'category': 'entity',
            'estimated_savings': '$2,000-$8,000',
            'estimated_savings_value': 5000,
            'implementation_difficulty': 'Complex',
            'time_required': '5-8 hours',
            'icon': 'file-contract',
            'tier': 'plus'
        },
        {
            'id': 'llc_operating_agreement',
            'name': 'Optimize LLC Operating Agreement',
            'description': 'Structure your operating agreement to maximize tax benefits and protect assets.',
            'category': 'legal',
            'estimated_savings': '$1,000-$5,000',
            'estimated_savings_value': 3000,
            'implementation_difficulty': 'Complex',
            'time_required': '3-6 hours',
            'icon': 'file-signature',
            'tier': 'pro'
        }
    ]
    
    return recommendations

def get_s_corp_recommendations(business_info, tax_year):
    """Get recommendations specific to S-Corporations"""
    recommendations = [
        {
            'id': 'scorp_reasonable_comp',
            'name': 'Optimize Owner Compensation',
            'description': 'Ensure your salary is "reasonable" while maximizing tax-advantaged distributions.',
            'category': 'compensation',
            'estimated_savings': '$3,000-$15,000',
            'estimated_savings_value': 9000,
            'implementation_difficulty': 'Complex',
            'time_required': '3-5 hours',
            'icon': 'money-bill-wave',
            'tier': 'pro'
        },
        {
            'id': 'scorp_retirement',
            'name': 'S-Corporation Retirement Planning',
            'description': 'Implement a retirement plan that allows for larger contributions than individual plans.',
            'category': 'retirement',
            'estimated_savings': '$2,500-$10,000',
            'estimated_savings_value': 6250,
            'implementation_difficulty': 'Medium',
            'time_required': '4-6 hours',
            'icon': 'piggy-bank',
            'tier': 'plus'
        },
        {
            'id': 'scorp_health_benefits',
            'name': 'S-Corporation Health Benefits',
            'description': 'Structure health insurance and benefits to maximize tax advantages.',
            'category': 'benefits',
            'estimated_savings': '$1,500-$7,000',
            'estimated_savings_value': 4250,
            'implementation_difficulty': 'Medium',
            'time_required': '2-4 hours',
            'icon': 'heartbeat',
            'tier': 'plus'
        }
    ]
    
    return recommendations

def get_c_corp_recommendations(business_info, tax_year):
    """Get recommendations specific to C-Corporations"""
    recommendations = [
        {
            'id': 'ccorp_tax_planning',
            'name': 'Corporate Tax Rate Planning',
            'description': 'Structure income and expenses to take advantage of corporate tax brackets.',
            'category': 'planning',
            'estimated_savings': '$5,000-$20,000',
            'estimated_savings_value': 12500,
            'implementation_difficulty': 'Complex',
            'time_required': '8+ hours',
            'icon': 'chart-bar',
            'tier': 'pro'
        },
        {
            'id': 'ccorp_benefits',
            'name': 'Maximize Tax-Free Benefits',
            'description': 'Implement employee benefits programs that are deductible to the corporation and tax-free to employees.',
            'category': 'benefits',
            'estimated_savings': '$3,000-$12,000',
            'estimated_savings_value': 7500,
            'implementation_difficulty': 'Medium',
            'time_required': '5-8 hours',
            'icon': 'gift',
            'tier': 'pro'
        },
        {
            'id': 'ccorp_fiscal_year',
            'name': 'Optimize Fiscal Year',
            'description': 'Choose a fiscal year that aligns with your business cycle for better tax planning.',
            'category': 'planning',
            'estimated_savings': '$2,000-$8,000',
            'estimated_savings_value': 5000,
            'implementation_difficulty': 'Complex',
            'time_required': '4-6 hours',
            'icon': 'calendar-alt',
            'tier': 'pro'
        }
    ]
    
    return recommendations

def get_time_sensitive_opportunities(tax_year):
    """Get time-sensitive tax saving opportunities"""
    current_month = datetime.now().month
    current_day = datetime.now().day
    
    time_sensitive = []
    
    # Year-end planning (November-December)
    if current_month >= 11:
        time_sensitive.append({
            'id': 'ts_year_end',
            'name': 'Year-End Tax Planning',
            'description': f'Take advantage of these year-end tax planning strategies before December 31, {tax_year}.',
            'deadline': f'{tax_year}-12-31',
            'days_remaining': (datetime(tax_year, 12, 31) - datetime.now()).days,
            'category': 'planning',
            'estimated_savings': '$1,000-$5,000',
            'estimated_savings_value': 3000,
            'actions': [
                'Defer income to next year if possible',
                'Accelerate deductions into current year',
                'Maximize retirement contributions',
                'Harvest tax losses in investment accounts',
                'Make charitable contributions'
            ],
            'icon': 'calendar-alt',
            'urgent': current_month == 12 and current_day > 15
        })
    
    # Retirement plan setup deadline approaching (for some plans)
    if current_month >= 9 and current_month <= 12:
        time_sensitive.append({
            'id': 'ts_retirement_setup',
            'name': 'Retirement Plan Setup Deadline',
            'description': f'Set up a qualified retirement plan by December 31, {tax_year} to be eligible for {tax_year} deductions.',
            'deadline': f'{tax_year}-12-31',
            'days_remaining': (datetime(tax_year, 12, 31) - datetime.now()).days,
            'category': 'retirement',
            'estimated_savings': '$2,000-$10,000',
            'estimated_savings_value': 6000,
            'actions': [
                'Research plan options (SEP IRA, SIMPLE IRA, Solo 401(k))',
                'Contact financial institution to set up plan',
                'Complete necessary paperwork',
                'Inform employees if applicable'
            ],
            'icon': 'piggy-bank',
            'urgent': current_month == 12 and current_day > 15
        })
    
    # Estimated tax payment deadlines
    est_tax_dates = [
        {'month': 4, 'day': 15, 'quarter': 1},
        {'month': 6, 'day': 15, 'quarter': 2},
        {'month': 9, 'day': 15, 'quarter': 3},
        {'month': 1, 'day': 15, 'quarter': 4, 'next_year': True}  # January of next year
    ]
    
    for date in est_tax_dates:
        est_month = date['month']
        est_day = date['day']
        quarter = date['quarter']
        year = tax_year + 1 if date.get('next_year') else tax_year
        
        # If within 30 days of deadline
        deadline = datetime(year, est_month, est_day)
        days_until = (deadline - datetime.now()).days
        
        if 0 <= days_until <= 30:
            time_sensitive.append({
                'id': f'ts_estimated_tax_q{quarter}',
                'name': f'Estimated Tax Payment (Q{quarter})',
                'description': f'Make your Q{quarter} estimated tax payment by {est_month}/{est_day}/{year}.',
                'deadline': f'{year}-{est_month:02d}-{est_day:02d}',
                'days_remaining': days_until,
                'category': 'payments',
                'estimated_savings': 'Avoid penalties',
                'estimated_savings_value': 500,  # Penalty avoidance value
                'actions': [
                    'Calculate required payment',
                    'Submit payment online via IRS Direct Pay or EFTPS',
                    'Document payment for your records',
                    'Consider adjustments based on year-to-date income'
                ],
                'icon': 'money-check-alt',
                'urgent': days_until <= 7
            })
    
    # Equipment purchases for Section 179 deduction
    if current_month >= 10:
        time_sensitive.append({
            'id': 'ts_section_179',
            'name': 'Section 179 Equipment Purchases',
            'description': f'Purchase qualifying equipment by December 31, {tax_year} to take advantage of Section 179 deduction.',
            'deadline': f'{tax_year}-12-31',
            'days_remaining': (datetime(tax_year, 12, 31) - datetime.now()).days,
            'category': 'deductions',
            'estimated_savings': '$2,500-$25,000+',
            'estimated_savings_value': 13750,
            'actions': [
                'Identify needed business equipment',
                'Ensure equipment is placed in service by year-end',
                'Document purchase and business use',
                'Consult with tax professional about eligibility'
            ],
            'icon': 'truck',
            'urgent': current_month == 12 and current_day > 15
        })
    
    return time_sensitive

def get_relevant_tax_updates(user, tax_year):
    """Get relevant tax law updates for the user"""
    # This would normally query a database of tax law changes
    # For demo purposes, we'll return sample updates
    updates = [
        {
            'id': 'update_standard_mileage',
            'name': 'Standard Mileage Rate Change',
            'description': f'The standard mileage rate for {tax_year} is now 65.5 cents per mile, up from 62.5 cents in the previous year.',
            'effective_date': f'{tax_year}-01-01',
            'impact': 'Positive',
            'estimated_savings': 'Varies based on business miles',
            'estimated_savings_value': 750,
            'actions': [
                'Update your mileage tracking system with the new rate',
                'Consider using actual expenses if more beneficial',
                'Ensure proper documentation of business mileage'
            ],
            'icon': 'car',
            'category': 'deductions'
        },
        {
            'id': 'update_retirement_limits',
            'name': 'Increased Retirement Contribution Limits',
            'description': f'Contribution limits for retirement plans have increased for {tax_year}. 401(k) limit is now $23,000 and IRA limit is $7,000 ($8,000 if age 50+).',
            'effective_date': f'{tax_year}-01-01',
            'impact': 'Positive',
            'estimated_savings': '$500-$2,000 in additional tax deferrals',
            'estimated_savings_value': 1250,
            'actions': [
                'Adjust your contribution amounts to maximize benefits',
                'Consider catch-up contributions if eligible',
                'Review your retirement strategy with a financial advisor'
            ],
            'icon': 'piggy-bank',
            'category': 'retirement'
        },
        {
            'id': 'update_section_179',
            'name': 'Section 179 Deduction Limit Increase',
            'description': f'The Section 179 deduction limit has increased to $1,190,000 for {tax_year}, with a phase-out threshold of $3,040,000.',
            'effective_date': f'{tax_year}-01-01',
            'impact': 'Positive',
            'estimated_savings': 'Varies based on equipment purchases',
            'estimated_savings_value': 5000,
            'actions': [
                'Evaluate planned equipment purchases',
                'Consider accelerating purchases to current year',
                'Document business use percentage'
            ],
            'icon': 'tools',
            'category': 'deductions'
        },
        {
            'id': 'update_tax_brackets',
            'name': 'Tax Bracket Adjustments',
            'description': f'Income tax brackets have been adjusted for inflation for {tax_year}, potentially putting you in a different bracket.',
            'effective_date': f'{tax_year}-01-01',
            'impact': 'Varies',
            'estimated_savings': 'Varies based on income',
            'estimated_savings_value': 1000,
            'actions': [
                'Review your projected income for the year',
                'Adjust tax planning strategies accordingly',
                'Consider income shifting or timing of income/deductions'
            ],
            'icon': 'percentage',
            'category': 'planning'
        }
    ]
    
    return updates

def get_industry_recommendations(user):
    """Get industry-specific tax recommendations"""
    # This would normally be based on the user's actual industry
    # For demo purposes, we'll return consulting industry recommendations
    industry = 'consulting'
    
    industry_recommendations = {
        'consulting': [
            {
                'id': 'ind_home_office',
                'name': 'Maximize Home Office Deduction',
                'description': 'As a consultant primarily working from home, ensure you\'re maximizing your home office deduction.',
                'category': 'deductions',
                'estimated_savings': '$1,500-$3,000',
                'estimated_savings_value': 2250,
                'implementation_difficulty': 'Medium',
                'time_required': '2-3 hours',
                'icon': 'home',
                'tier': 'basic'
            },
            {
                'id': 'ind_client_entertainment',
                'name': 'Business Meal Documentation',
                'description': 'Properly document client meals to take advantage of the 100% deduction for business meals in {tax_year}.',
                'category': 'deductions',
                'estimated_savings': '$500-$2,000',
                'estimated_savings_value': 1250,
                'implementation_difficulty': 'Easy',
                'time_required': 'Ongoing',
                'icon': 'utensils',
                'tier': 'basic'
            },
            {
                'id': 'ind_professional_development',
                'name': 'Professional Development Deductions',
                'description': 'Deduct costs for continuing education, certifications, and professional subscriptions relevant to your consulting practice.',
                'category': 'deductions',
                'estimated_savings': '$1,000-$3,000',
                'estimated_savings_value': 2000,
                'implementation_difficulty': 'Easy',
                'time_required': '1-2 hours',
                'icon': 'graduation-cap',
                'tier': 'basic'
            }
        ],
        'real_estate': [
            # Real estate industry recommendations would go here
        ],
        'e-commerce': [
            # E-commerce industry recommendations would go here
        ]
    }
    
    return industry_recommendations.get(industry, [])

def get_strategy_implementation_steps(strategy):
    """Get detailed implementation steps for a tax strategy"""
    # This would normally be stored in the database or generated by AI
    # For demo purposes, we'll return sample steps based on strategy ID
    implementation_steps = {
        'basic_expense_tracking': [
            {
                'step': 1,
                'title': 'Open a dedicated business checking account',
                'description': 'Separate personal and business finances by opening a dedicated business checking account.',
                'time_estimate': '1-2 hours',
                'resources_needed': ['Personal identification', 'Business formation documents', 'EIN or SSN']
            },
            {
                'step': 2,
                'title': 'Apply for a business credit card',
                'description': 'Get a business credit card to use exclusively for business expenses.',
                'time_estimate': '30 minutes',
                'resources_needed': ['Business checking account', 'Personal credit score', 'Business information']
            },
            {
                'step': 3,
                'title': 'Set up expense tracking software',
                'description': 'Choose and set up accounting software that can import transactions from your accounts.',
                'time_estimate': '1-2 hours',
                'resources_needed': ['Business credit card', 'Bank account login', 'Accounting software subscription']
            },
            {
                'step': 4,
                'title': 'Categorize expenses regularly',
                'description': 'Schedule time weekly or monthly to categorize expenses and attach receipts.',
                'time_estimate': '1 hour per month',
                'resources_needed': ['Accounting software', 'Receipt storage system']
            }
        ],
        'sp_qbi_deduction': [
            {
                'step': 1,
                'title': 'Determine if you qualify',
                'description': 'Verify that your business type and income level qualify for the QBI deduction.',
                'time_estimate': '30 minutes',
                'resources_needed': ['Previous year tax return', 'Current year income projection']
            },
            {
                'step': 2,
                'title': 'Calculate your taxable income',
                'description': 'Determine your taxable income to ensure you\'re below the phase-out thresholds.',
                'time_estimate': '1 hour',
                'resources_needed': ['Income records', 'Deduction records']
            },
            {
                'step': 3,
                'title': 'Calculate your qualified business income',
                'description': 'Determine your qualified business income (QBI), which is generally your net income from the business.',
                'time_estimate': '1 hour',
                'resources_needed': ['Profit and loss statement', 'Business tax records']
            },
            {
                'step': 4,
                'title': 'Apply the appropriate percentage',
                'description': 'Calculate 20% of your QBI, subject to limitations based on W-2 wages and property.',
                'time_estimate': '30 minutes',
                'resources_needed': ['QBI calculation', 'W-2 wage information if applicable']
            },
            {
                'step': 5,
                'title': 'Document your calculation',
                'description': 'Keep detailed records of how you calculated your QBI deduction.',
                'time_estimate': '30 minutes',
                'resources_needed': ['Calculation worksheet', 'Supporting documentation']
            }
        ]
    }
    
    # Return implementation steps if available, otherwise return generic steps
    return implementation_steps.get(strategy.strategy_name, [
        {
            'step': 1,
            'title': 'Consult with a tax professional',
            'description': 'Discuss this strategy with your tax advisor to ensure it\'s appropriate for your situation.',
            'time_estimate': '1 hour',
            'resources_needed': ['Tax advisor contact information', 'Business financial information']
        },
        {
            'step': 2,
            'title': 'Gather necessary documentation',
            'description': 'Collect all required documentation to implement this strategy.',
            'time_estimate': '2-3 hours',
            'resources_needed': ['Financial records', 'Business documentation']
        },
        {
            'step': 3,
            'title': 'Implement the strategy',
            'description': 'Follow specific steps to implement this tax saving strategy.',
            'time_estimate': 'Varies',
            'resources_needed': ['Varies based on strategy']
        },
        {
            'step': 4,
            'title': 'Document implementation',
            'description': 'Keep detailed records of how and when you implemented this strategy.',
            'time_estimate': '1 hour',
            'resources_needed': ['Record-keeping system']
        }
    ])

def get_related_strategies(strategy):
    """Get related tax strategies"""
    # This would normally be generated based on the strategy and user context
    # For demo purposes, we'll return sample related strategies
    return [
        {
            'id': 'related_1',
            'name': 'Complementary Tax Strategy',
            'description': 'This strategy works well in combination with your current strategy.',
            'category': 'planning',
            'estimated_savings': '$500-$2,000',
            'estimated_savings_value': 1250,
            'implementation_difficulty': 'Medium',
            'icon': 'puzzle-piece'
        },
        {
            'id': 'related_2',
            'name': 'Alternative Approach',
            'description': 'Consider this alternative approach if your current strategy isn\'t optimal.',
            'category': 'planning',
            'estimated_savings': '$1,000-$3,000',
            'estimated_savings_value': 2000,
            'implementation_difficulty': 'Medium',
            'icon': 'random'
        }
    ]

def calculate_total_potential_savings(recommendations):
    """Calculate the total potential savings from all recommendations"""
    return sum(rec.get('estimated_savings_value', 0) for rec in recommendations)