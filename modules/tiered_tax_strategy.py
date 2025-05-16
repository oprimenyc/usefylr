"""
Tiered Tax Strategy Module

This module provides tax strategy recommendations based on the user's membership tier,
business type, and activity level.
"""

from flask import Blueprint, render_template, jsonify, request, session
from flask_login import login_required, current_user
from app.app import db
from app.models import User, TaxForm, UserPlan
from app.access_control import requires_access_level
import json
from datetime import datetime

# Create blueprint
tiered_strategy_bp = Blueprint('tiered_strategy', __name__, url_prefix='/tiered-strategy')

@tiered_strategy_bp.route('/recommendations')
@login_required
def recommendations():
    """Get tax strategy recommendations based on user's tier and business data"""
    # Get business information from questionnaire or forms
    business_type = request.args.get('business_type', 'sole_proprietor')
    annual_revenue = request.args.get('annual_revenue', 0, type=int)
    has_employees = request.args.get('has_employees', 'false') == 'true'
    tax_year = request.args.get('tax_year', datetime.now().year, type=int)
    state = request.args.get('state', 'CA')
    
    # Determine user's tier
    user_tier = current_user.plan
    
    # Get recommendations based on tier
    recommendations = get_tiered_recommendations(
        user_tier, 
        business_type, 
        annual_revenue, 
        has_employees,
        tax_year,
        state
    )
    
    # Store in session for reference
    session['tax_recommendations'] = recommendations
    
    return jsonify(recommendations)

@tiered_strategy_bp.route('/view')
@login_required
def view_recommendations():
    """View page with tax strategy recommendations"""
    # Get business information
    business_type = request.args.get('business_type', 'sole_proprietor')
    annual_revenue = request.args.get('annual_revenue', 0, type=int)
    has_employees = request.args.get('has_employees', 'false') == 'true'
    tax_year = request.args.get('tax_year', datetime.now().year, type=int)
    state = request.args.get('state', 'CA')
    
    # Get user's plan
    user_tier = current_user.plan
    
    # Get recommendations based on tier
    recommendations = get_tiered_recommendations(
        user_tier, 
        business_type, 
        annual_revenue, 
        has_employees,
        tax_year,
        state
    )
    
    # Get business type display name
    business_type_name = get_business_type_display(business_type)
    
    return render_template('tax_savings/tiered_recommendations.html',
                          recommendations=recommendations,
                          business_type=business_type,
                          business_type_name=business_type_name,
                          annual_revenue=annual_revenue,
                          has_employees=has_employees,
                          tax_year=tax_year,
                          state=state,
                          user_tier=user_tier)

def get_tiered_recommendations(user_tier, business_type, annual_revenue, has_employees, tax_year, state):
    """Get tax strategy recommendations based on user's tier"""
    recommendations = {}
    
    if user_tier == UserPlan.BASIC:
        # Basic users get 1-2 general tax saving tips
        recommendations = get_basic_recommendations(business_type, annual_revenue, has_employees, state)
    elif user_tier == UserPlan.FYLR_PLUS:
        # Plus users get more detailed recommendations, still with upgrade message
        recommendations = get_plus_recommendations(business_type, annual_revenue, has_employees, tax_year, state)
    elif user_tier == UserPlan.PRO:
        # Pro users get full strategy breakdown
        recommendations = get_pro_recommendations(business_type, annual_revenue, has_employees, tax_year, state)
    else:
        # Default to basic recommendations if tier is unknown
        recommendations = get_basic_recommendations(business_type, annual_revenue, has_employees, state)
    
    return recommendations

def get_basic_recommendations(business_type, annual_revenue, has_employees, state):
    """Get basic tax recommendations for free/basic users"""
    general_tips = []
    
    # Add 1-2 general tax saving tips based on business type
    if business_type == 'sole_proprietor':
        if annual_revenue > 40000:
            general_tips.append({
                'tip': 'Consider an S Corporation Election',
                'description': 'Sole proprietors with net income exceeding $40K may benefit from electing S Corporation status, potentially saving thousands in self-employment taxes.',
                'estimated_savings': 'Up to $3,000+ annually',
                'icon': 'building'
            })
        
        general_tips.append({
            'tip': 'Track Home Office Expenses',
            'description': 'If you use part of your home exclusively for business, you may qualify for the home office deduction.',
            'estimated_savings': 'Up to $1,500 annually',
            'icon': 'home'
        })
    elif business_type in ['llc_single', 'llc_multi']:
        general_tips.append({
            'tip': 'Optimize Tax Classification',
            'description': 'LLCs can elect different tax treatments (disregarded entity, partnership, S corporation) that may reduce overall tax burden.',
            'estimated_savings': 'Varies based on income',
            'icon': 'file-contract'
        })
        
        if business_type == 'llc_single' and annual_revenue > 80000:
            general_tips.append({
                'tip': 'S Corporation Election',
                'description': 'Single-member LLCs with significant profit may save on self-employment taxes by electing S corporation status.',
                'estimated_savings': 'Up to $5,000+ annually',
                'icon': 'building'
            })
    elif business_type == 's_corp':
        general_tips.append({
            'tip': 'Optimize Owner Compensation',
            'description': 'S corporation owners must take a reasonable salary, but distributions above this amount aren\'t subject to self-employment tax.',
            'estimated_savings': 'Varies based on income',
            'icon': 'money-bill-wave'
        })
    elif business_type == 'c_corp':
        general_tips.append({
            'tip': 'Consider Accountable Plans',
            'description': 'Reimburse employees (including owner-employees) for business expenses through accountable plans, which are deductible by the corporation and non-taxable to employees.',
            'estimated_savings': 'Varies based on expenses',
            'icon': 'receipt'
        })
    
    # Add employee-specific tip if applicable
    if has_employees:
        general_tips.append({
            'tip': 'Research Tax Credits for Employers',
            'description': 'You may qualify for tax credits like the Work Opportunity Tax Credit or Small Business Health Care Tax Credit.',
            'estimated_savings': 'Up to $9,600 per eligible employee',
            'icon': 'users'
        })
    
    # Add state-specific tip if available
    state_tip = get_state_specific_tip(state, business_type)
    if state_tip:
        general_tips.append(state_tip)
    
    # Limit to 2 tips for basic users
    general_tips = general_tips[:2]
    
    # Get upgrade message
    upgrade_message = {
        'title': 'Want a full tax strategy breakdown and personalized deductions checklist?',
        'description': 'Upgrade to .fylr+ or Pro for in-depth tax strategy recommendations personalized to your specific business situation.',
        'cta': 'Upgrade Now',
        'link': '/pricing'
    }
    
    return {
        'general_tips': general_tips,
        'upgrade_message': upgrade_message,
        'is_limited': True
    }

def get_plus_recommendations(business_type, annual_revenue, has_employees, tax_year, state):
    """Get enhanced recommendations for Plus tier users"""
    # Start with basic recommendations
    recommendations = get_basic_recommendations(business_type, annual_revenue, has_employees, state)
    
    # Add additional tips for Plus users
    additional_tips = []
    
    # Add retirement plan recommendation
    if annual_revenue > 30000:
        additional_tips.append({
            'tip': 'Set Up a Self-Employed Retirement Plan',
            'description': f'For {tax_year}, you can contribute up to $22,500 to a Solo 401(k) or up to 25% of net self-employment income to a SEP IRA (maximum $66,000).',
            'estimated_savings': 'Varies based on contribution and tax bracket',
            'icon': 'piggy-bank'
        })
    
    # Add business expense tracking recommendation
    additional_tips.append({
        'tip': 'Optimize Business Expense Tracking',
        'description': 'Use dedicated business accounts and accounting software to ensure you capture all eligible deductions.',
        'estimated_savings': 'Up to $2,000 in missed deductions',
        'icon': 'receipt'
    })
    
    # Add deduction recommendations based on business type
    if business_type == 'sole_proprietor':
        additional_tips.append({
            'tip': 'Health Insurance Premium Deduction',
            'description': 'Self-employed individuals can deduct health, dental, and long-term care insurance premiums for themselves, spouse, and dependents.',
            'estimated_savings': 'Varies based on premium amounts',
            'icon': 'medkit'
        })
    elif business_type in ['s_corp', 'c_corp']:
        additional_tips.append({
            'tip': 'Fringe Benefits Strategy',
            'description': 'Corporations can provide certain tax-free fringe benefits to employees (including owner-employees).',
            'estimated_savings': 'Up to $5,000+ annually',
            'icon': 'gift'
        })
    
    # Add upgrade message for even more features
    upgrade_message = {
        'title': 'Unlock advanced tax strategies and entity optimization',
        'description': 'Upgrade to Pro for our most advanced tax strategies, entity optimization recommendations, and personalized deductions checklist.',
        'cta': 'Upgrade to Pro',
        'link': '/pricing'
    }
    
    # Replace basic recommendations with enhanced ones
    recommendations['general_tips'].extend(additional_tips)
    recommendations['upgrade_message'] = upgrade_message
    recommendations['deduction_categories'] = get_common_deduction_categories(business_type)
    recommendations['is_limited'] = True
    
    return recommendations

def get_pro_recommendations(business_type, annual_revenue, has_employees, tax_year, state):
    """Get comprehensive recommendations for Pro tier users"""
    # Start with plus recommendations without the upgrade message
    recommendations = get_plus_recommendations(business_type, annual_revenue, has_employees, tax_year, state)
    
    # Remove the upgrade message
    recommendations.pop('upgrade_message', None)
    
    # Add top 3 tax strategies for their business type
    top_strategies = get_top_tax_strategies(business_type, annual_revenue, has_employees, tax_year)
    
    # Add custom deductions checklist
    custom_deductions = get_custom_deductions(business_type, annual_revenue, has_employees)
    
    # Add entity optimization suggestion
    entity_optimization = get_entity_optimization(business_type, annual_revenue, has_employees, tax_year)
    
    # Add year-round tax planning
    year_round_planning = get_year_round_planning(business_type, tax_year)
    
    # Add quarterly estimated tax guidance
    quarterly_tax_guidance = get_quarterly_tax_guidance(business_type, annual_revenue, tax_year)
    
    # Professional referral network
    professional_referrals = {
        'title': 'Connect with Tax Professionals',
        'description': 'For complex situations, we can refer you to vetted tax professionals in our network.',
        'cta': 'Get a Referral',
        'link': '/professional-referrals'
    }
    
    # Complete the recommendations
    recommendations.update({
        'top_strategies': top_strategies,
        'custom_deductions': custom_deductions,
        'entity_optimization': entity_optimization,
        'year_round_planning': year_round_planning,
        'quarterly_tax_guidance': quarterly_tax_guidance,
        'professional_referrals': professional_referrals,
        'is_limited': False
    })
    
    return recommendations

def get_top_tax_strategies(business_type, annual_revenue, has_employees, tax_year):
    """Get top 3 tax strategies for a specific business type"""
    strategies = []
    
    # Strategies for sole proprietors
    if business_type == 'sole_proprietor':
        if annual_revenue > 40000:
            strategies.append({
                'name': 'S Corporation Election',
                'description': 'Elect S corporation status to potentially save on self-employment taxes by taking a reasonable salary plus distributions.',
                'estimated_savings': '$3,000-$10,000+ annually',
                'implementation_complexity': 'Moderate',
                'deadline': f'March 15, {tax_year} for current year election',
                'icon': 'building'
            })
        
        strategies.append({
            'name': 'Qualified Business Income Deduction',
            'description': 'Take advantage of the 20% QBI deduction available to pass-through entities under Section 199A.',
            'estimated_savings': 'Up to 20% of qualified business income',
            'implementation_complexity': 'Moderate',
            'deadline': 'Tax filing deadline',
            'icon': 'percentage'
        })
        
        strategies.append({
            'name': 'Retirement Plan Contribution',
            'description': f'Contribute to a Solo 401(k) or SEP IRA to reduce taxable income for {tax_year}.',
            'estimated_savings': 'Varies based on contribution and tax bracket',
            'implementation_complexity': 'Easy',
            'deadline': f'Solo 401(k) setup by Dec 31, {tax_year}; contribution by tax filing deadline',
            'icon': 'piggy-bank'
        })
    
    # Strategies for LLCs
    elif business_type in ['llc_single', 'llc_multi']:
        if business_type == 'llc_single':
            strategies.append({
                'name': 'S Corporation Election',
                'description': 'Elect S corporation tax treatment to potentially save on self-employment taxes.',
                'estimated_savings': '$3,000-$10,000+ annually',
                'implementation_complexity': 'Moderate',
                'deadline': f'March 15, {tax_year} for current year election',
                'icon': 'building'
            })
        
        strategies.append({
            'name': 'Qualified Business Income Deduction',
            'description': 'Take advantage of the 20% QBI deduction available to pass-through entities under Section 199A.',
            'estimated_savings': 'Up to 20% of qualified business income',
            'implementation_complexity': 'Moderate',
            'deadline': 'Tax filing deadline',
            'icon': 'percentage'
        })
        
        if has_employees:
            strategies.append({
                'name': 'Accountable Plan Implementation',
                'description': 'Implement an accountable plan to reimburse employees for business expenses in a tax-advantaged way.',
                'estimated_savings': 'Varies based on expenses',
                'implementation_complexity': 'Moderate',
                'deadline': f'December 31, {tax_year} to be effective for the year',
                'icon': 'receipt'
            })
        else:
            strategies.append({
                'name': 'Home Office Deduction',
                'description': 'Claim home office deduction if you use part of your home regularly and exclusively for business.',
                'estimated_savings': '$1,000-$3,000 annually',
                'implementation_complexity': 'Easy',
                'deadline': 'Tax filing deadline',
                'icon': 'home'
            })
    
    # Strategies for S Corporations
    elif business_type == 's_corp':
        strategies.append({
            'name': 'Optimize Owner Salary',
            'description': 'Set a reasonable salary for owner-employees to balance payroll taxes and qualified business income deduction.',
            'estimated_savings': '$5,000-$15,000 annually',
            'implementation_complexity': 'Moderate',
            'deadline': 'Should be set at beginning of year, but can be adjusted',
            'icon': 'money-bill-wave'
        })
        
        strategies.append({
            'name': 'Medical Reimbursement Plan',
            'description': 'Implement a Qualified Small Employer Health Reimbursement Arrangement (QSEHRA) or Individual Coverage HRA (ICHRA).',
            'estimated_savings': 'Up to $11,050 for family coverage annually',
            'implementation_complexity': 'Moderate',
            'deadline': f'Plan should be established before reimbursements begin',
            'icon': 'medkit'
        })
        
        strategies.append({
            'name': 'Retirement Plan Options',
            'description': f'Consider a 401(k), profit-sharing, or defined benefit plan for significant tax savings.',
            'estimated_savings': '$20,000-$100,000+ depending on plan',
            'implementation_complexity': 'Complex',
            'deadline': f'Plan must be established by Dec 31, {tax_year}, contributions by tax filing deadline',
            'icon': 'piggy-bank'
        })
    
    # Strategies for C Corporations
    elif business_type == 'c_corp':
        strategies.append({
            'name': 'Timing of Income and Expenses',
            'description': f'Time income and expenses between tax years to optimize corporate tax brackets.',
            'estimated_savings': '$5,000-$20,000 annually',
            'implementation_complexity': 'Moderate',
            'deadline': f'December 31, {tax_year}',
            'icon': 'calendar-alt'
        })
        
        strategies.append({
            'name': 'Comprehensive Benefits Package',
            'description': 'Provide tax-free fringe benefits to employees (including owners) such as health insurance, education assistance, and more.',
            'estimated_savings': '$10,000-$30,000 annually',
            'implementation_complexity': 'Moderate',
            'deadline': 'Benefits should be established before provided',
            'icon': 'gift'
        })
        
        if annual_revenue > 250000:
            strategies.append({
                'name': 'R&D Tax Credits',
                'description': 'If your business develops products, processes, or software, you may qualify for R&D tax credits.',
                'estimated_savings': '$20,000-$100,000+ depending on R&D expenses',
                'implementation_complexity': 'Complex',
                'deadline': 'Tax filing deadline',
                'icon': 'flask'
            })
        else:
            strategies.append({
                'name': 'Corporate Retirement Plan',
                'description': f'Establish a corporate retirement plan with potential for large contributions.',
                'estimated_savings': '$20,000-$100,000+ depending on plan',
                'implementation_complexity': 'Complex',
                'deadline': f'Plan must be established by Dec 31, {tax_year}',
                'icon': 'piggy-bank'
            })
    
    return strategies[:3]  # Limit to top 3 strategies

def get_custom_deductions(business_type, annual_revenue, has_employees):
    """Get custom deductions list based on business type"""
    deductions = {
        'common': [
            {
                'name': 'Business insurance',
                'description': 'Premiums for business insurance policies are fully deductible.',
                'tax_form': 'Schedule C Line 15 / Form 1120 Line 26',
                'documentation': 'Insurance policy statements and proof of payment'
            },
            {
                'name': 'Office supplies and expenses',
                'description': 'Items used for your business including software, supplies, and small equipment.',
                'tax_form': 'Schedule C Line 18 / Form 1120 Line 26',
                'documentation': 'Receipts with business purpose noted'
            },
            {
                'name': 'Professional services',
                'description': 'Fees paid to attorneys, accountants, consultants, etc.',
                'tax_form': 'Schedule C Line 17 / Form 1120 Line 26',
                'documentation': 'Invoices with description of services'
            }
        ],
        'business_specific': []
    }
    
    # Add business-specific deductions
    if business_type == 'sole_proprietor':
        deductions['business_specific'] = [
            {
                'name': 'Home office deduction',
                'description': 'Deduct expenses for the business use of your home if used regularly and exclusively for business.',
                'tax_form': 'Form 8829 / Schedule C Line 30',
                'documentation': 'Home measurements, expenses, photos of office space'
            },
            {
                'name': 'Self-employed health insurance',
                'description': 'Premiums for health, dental, and long-term care for you, spouse, and dependents.',
                'tax_form': 'Schedule 1 Line 17',
                'documentation': 'Insurance statements and proof of payment'
            },
            {
                'name': 'Self-employment tax deduction',
                'description': 'Deduct 50% of your self-employment tax.',
                'tax_form': 'Schedule 1 Line 15',
                'documentation': 'Schedule SE calculation'
            }
        ]
    elif business_type in ['llc_single', 'llc_multi']:
        deductions['business_specific'] = [
            {
                'name': 'Guaranteed payments (multi-member)',
                'description': 'Payments made to partners for services rendered are deductible by the LLC.',
                'tax_form': 'Form 1065 Line 10',
                'documentation': 'Partnership agreement, payment records'
            },
            {
                'name': 'LLC fees and taxes',
                'description': 'State LLC fees, franchise taxes, and annual report fees.',
                'tax_form': 'Schedule C Line 23 / Form 1065 Line 14',
                'documentation': 'State filings and payment receipts'
            }
        ]
    elif business_type == 's_corp':
        deductions['business_specific'] = [
            {
                'name': 'Shareholder health insurance',
                'description': 'Health insurance for 2%+ shareholders reported as wages but deductible on personal return.',
                'tax_form': 'Form 1120-S Line 18 (as wages) / Schedule 1 Line 17 (personal deduction)',
                'documentation': 'Insurance statements, payroll records'
            },
            {
                'name': 'Shareholder wages',
                'description': 'Reasonable wages paid to shareholder-employees.',
                'tax_form': 'Form 1120-S Line 8',
                'documentation': 'Payroll records, W-2 forms'
            }
        ]
    elif business_type == 'c_corp':
        deductions['business_specific'] = [
            {
                'name': 'Employee benefit programs',
                'description': 'Health plans, education assistance, dependent care, etc.',
                'tax_form': 'Form 1120 Line 24',
                'documentation': 'Plan documents, payment records'
            },
            {
                'name': 'Charitable contributions',
                'description': 'Donations to qualified organizations (up to 10% of taxable income).',
                'tax_form': 'Form 1120 Line 19',
                'documentation': 'Donation receipts from qualified organizations'
            }
        ]
    
    # Add employee-specific deductions
    if has_employees:
        deductions['business_specific'].append({
            'name': 'Employer payroll taxes',
            'description': 'The employer portion of Social Security and Medicare taxes.',
            'tax_form': 'Schedule C Line 23 / Form 1120 Line 17',
            'documentation': 'Payroll tax returns (941, 940, etc.)'
        })
        
        deductions['business_specific'].append({
            'name': 'Employee benefit programs',
            'description': 'Health insurance, retirement plans, and other benefits for employees.',
            'tax_form': 'Schedule C Line 14 / Form 1120 Line 24',
            'documentation': 'Plan documents, payment records'
        })
    
    return deductions

def get_entity_optimization(business_type, annual_revenue, has_employees, tax_year):
    """Get entity optimization recommendation based on business circumstances"""
    recommendation = {
        'current_entity': get_business_type_display(business_type),
        'details': {},
        'considerations': []
    }
    
    # Entity recommendations for sole proprietors
    if business_type == 'sole_proprietor':
        if annual_revenue > 50000:
            recommendation['details'] = {
                'recommended_entity': 'S Corporation',
                'description': 'Based on your revenue level, incorporating as an S Corporation could save on self-employment taxes while maintaining pass-through taxation.',
                'estimated_savings': f'$3,000-$10,000+ annually, depending on profitability',
                'implementation_timeline': f'2-3 months to form corporation and elect S status'
            }
            recommendation['considerations'] = [
                'You\'ll need to pay yourself a reasonable salary subject to payroll taxes',
                'Additional administrative requirements including separate tax return, payroll, and corporate formalities',
                'May create additional state filing requirements and fees',
                'Best for businesses with consistent profitability and sufficient income to offset additional costs'
            ]
        elif annual_revenue > 20000:
            recommendation['details'] = {
                'recommended_entity': 'Single-Member LLC',
                'description': 'An LLC provides liability protection while maintaining the tax simplicity of a sole proprietorship.',
                'estimated_savings': 'Primarily liability protection rather than tax savings',
                'implementation_timeline': '2-4 weeks to form LLC'
            }
            recommendation['considerations'] = [
                'Tax treatment remains the same (Schedule C) by default',
                'State filing fees and annual reports will be required',
                'Can later elect S Corporation taxation as revenue grows',
                'Provides liability protection for your personal assets'
            ]
        else:
            recommendation['details'] = {
                'recommended_entity': 'Remain Sole Proprietorship',
                'description': 'At your current revenue level, the simplicity and low cost of a sole proprietorship likely outweigh the benefits of changing.',
                'estimated_savings': 'N/A - Focus on growing business',
                'implementation_timeline': 'N/A'
            }
            recommendation['considerations'] = [
                'Simplest and lowest-cost entity structure',
                'Consider changing when revenue consistently exceeds $40,000-$50,000',
                'Be aware that personal assets are at risk for business liabilities',
                'Revisit this recommendation if you expect significant growth'
            ]
    
    # Entity recommendations for single-member LLCs
    elif business_type == 'llc_single':
        if annual_revenue > 80000:
            recommendation['details'] = {
                'recommended_entity': 'LLC taxed as S Corporation',
                'description': 'Electing S Corporation tax treatment could save significant self-employment taxes while maintaining liability protection.',
                'estimated_savings': f'$5,000-$15,000+ annually, depending on profitability',
                'implementation_timeline': f'1-2 months to file election and set up payroll'
            }
            recommendation['considerations'] = [
                'Requires filing Form 2553 with the IRS',
                'You\'ll need to pay yourself a reasonable salary subject to payroll taxes',
                'Additional administrative requirements including payroll and separate tax return',
                'Best for businesses with consistent profitability'
            ]
        else:
            recommendation['details'] = {
                'recommended_entity': 'Remain LLC (Disregarded Entity)',
                'description': 'At your current revenue level, the tax simplicity of a disregarded entity likely outweighs S Corporation benefits.',
                'estimated_savings': 'N/A - Current structure optimal',
                'implementation_timeline': 'N/A'
            }
            recommendation['considerations'] = [
                'Simple taxation while maintaining liability protection',
                'Consider S Corporation election when net income consistently exceeds $60,000-$80,000',
                'Revisit this recommendation if profitability increases significantly',
                'Current structure provides good balance of simplicity and protection'
            ]
    
    # Entity recommendations for multi-member LLCs
    elif business_type == 'llc_multi':
        if annual_revenue > 150000:
            recommendation['details'] = {
                'recommended_entity': 'LLC taxed as S Corporation',
                'description': 'Electing S Corporation tax treatment could save on self-employment taxes for managing members.',
                'estimated_savings': f'Varies based on member distribution and compensation structure',
                'implementation_timeline': f'1-2 months to file election and set up payroll'
            }
            recommendation['considerations'] = [
                'All members must consent to the S Corporation election',
                'Requires uniform distribution of profits based on ownership',
                'Working members must receive reasonable compensation as wages',
                'May impact special allocations and certain tax benefits of partnership taxation'
            ]
        else:
            recommendation['details'] = {
                'recommended_entity': 'Remain LLC (Partnership)',
                'description': 'Partnership taxation offers flexibility in allocations and distributions that may outweigh S Corporation benefits.',
                'estimated_savings': 'N/A - Current structure optimal',
                'implementation_timeline': 'N/A'
            }
            recommendation['considerations'] = [
                'Allows for special allocations of profits and losses',
                'Simpler than S Corporation administration',
                'Consider S Corporation election if managing members take significant guaranteed payments',
                'Current structure provides good balance of flexibility and protection'
            ]
    
    # S Corporation recommendations
    elif business_type == 's_corp':
        recommendation['details'] = {
            'recommended_entity': 'Remain S Corporation',
            'description': 'S Corporation status is generally optimal for most small businesses balancing tax savings and administrative requirements.',
            'estimated_savings': 'N/A - Current structure optimal',
            'implementation_timeline': 'N/A'
        }
        
        if annual_revenue > 500000:
            recommendation['considerations'] = [
                'Ensure shareholder-employee compensation is reasonable but not excessive',
                'Consider creating multiple classes of stock if planning to bring in investors',
                'Evaluate C Corporation if seeking significant outside investment',
                'Current structure is optimal for most small businesses'
            ]
        else:
            recommendation['considerations'] = [
                'Ensure shareholder-employee compensation is reasonable but not excessive',
                'Maintain corporate formalities to protect S Corporation status',
                'Consider shareholder-employee health insurance strategies',
                'Current structure is optimal for most small businesses'
            ]
    
    # C Corporation recommendations
    elif business_type == 'c_corp':
        if annual_revenue < 250000 and not has_employees:
            recommendation['details'] = {
                'recommended_entity': 'Consider S Corporation',
                'description': 'Unless you need to retain significant earnings or have multiple classes of stock, an S Corporation may offer tax advantages.',
                'estimated_savings': 'Varies based on dividend strategy and personal tax situation',
                'implementation_timeline': f'1 month to file S Corporation election (if eligible)'
            }
            recommendation['considerations'] = [
                'Avoid double taxation on distributed profits',
                'Pass-through of business losses to personal tax return',
                'Must meet S Corporation eligibility requirements',
                'May still retain C Corporation if significant earnings retention is planned'
            ]
        else:
            recommendation['details'] = {
                'recommended_entity': 'Remain C Corporation',
                'description': 'With your business profile, C Corporation status may be appropriate, especially with the 21% flat corporate tax rate.',
                'estimated_savings': 'N/A - Current structure may be optimal',
                'implementation_timeline': 'N/A'
            }
            recommendation['considerations'] = [
                'Optimal for businesses retaining significant earnings',
                'Consider compensation strategies to minimize double taxation',
                'Allows for more complex stock structures and investor relations',
                'Evaluate your specific situation with a tax professional'
            ]
    
    return recommendation

def get_year_round_planning(business_type, tax_year):
    """Get year-round tax planning calendar"""
    # Common tax planning events
    planning_calendar = [
        {
            'period': 'Q1 (Jan-Mar)',
            'tasks': [
                f'File previous year ({tax_year-1}) tax returns or extensions',
                'Implement new tax strategies for current year',
                'Set up retirement plan contributions for the year',
                'Organize tax documents from previous year'
            ]
        },
        {
            'period': 'Q2 (Apr-Jun)',
            'tasks': [
                'Review Q1 financials and adjust tax projections',
                'Make Q1 and Q2 estimated tax payments if required',
                'Plan major purchases to maximize Section 179 deduction',
                'Mid-year tax check-in with advisor'
            ]
        },
        {
            'period': 'Q3 (Jul-Sep)',
            'tasks': [
                'Review Q2 financials and adjust tax projections',
                'Make Q3 estimated tax payment if required',
                'Begin year-end tax planning',
                'Evaluate income and expenses, considering year-end timing'
            ]
        },
        {
            'period': 'Q4 (Oct-Dec)',
            'tasks': [
                'Final review of tax situation before year-end',
                'Implement income/expense timing strategies',
                'Make major business purchases before Dec 31',
                'Set up new retirement plans by Dec 31 deadline',
                'Make required retirement plan contributions'
            ]
        }
    ]
    
    # Add business-specific tasks
    if business_type == 'sole_proprietor':
        planning_calendar[0]['tasks'].append('Set up quarterly estimated tax payment schedule')
        planning_calendar[3]['tasks'].append('Evaluate home office and vehicle expenses')
    elif business_type in ['s_corp', 'c_corp']:
        planning_calendar[0]['tasks'].append('Review and set reasonable shareholder-employee salaries')
        planning_calendar[2]['tasks'].append('Consider shareholder/owner distributions timing')
    
    return planning_calendar

def get_quarterly_tax_guidance(business_type, annual_revenue, tax_year):
    """Get quarterly estimated tax payment guidance"""
    estimated_annual_tax = calculate_estimated_tax(business_type, annual_revenue)
    
    quarterly_tax_guidance = {
        'estimated_annual_tax': estimated_annual_tax,
        'quarterly_payment': round(estimated_annual_tax / 4, 2),
        'payment_schedule': [
            {'quarter': 'Q1', 'due_date': f'{tax_year}-04-15', 'amount': round(estimated_annual_tax / 4, 2)},
            {'quarter': 'Q2', 'due_date': f'{tax_year}-06-15', 'amount': round(estimated_annual_tax / 4, 2)},
            {'quarter': 'Q3', 'due_date': f'{tax_year}-09-15', 'amount': round(estimated_annual_tax / 4, 2)},
            {'quarter': 'Q4', 'due_date': f'{tax_year+1}-01-15', 'amount': round(estimated_annual_tax / 4, 2)}
        ],
        'payment_methods': [
            {'method': 'IRS Direct Pay', 'url': 'https://www.irs.gov/payments/direct-pay'},
            {'method': 'EFTPS', 'url': 'https://www.eftps.gov/'},
            {'method': 'IRS2Go App', 'url': 'https://www.irs.gov/newsroom/irs2goapp'},
            {'method': 'Payment Voucher', 'description': 'Form 1040-ES payment voucher with check by mail'}
        ],
        'safe_harbor_rules': [
            '100% of last year\'s tax liability',
            '90% of current year\'s tax liability',
            '110% of last year\'s tax if AGI was over $150,000'
        ]
    }
    
    # Add business-specific guidance
    if business_type in ['s_corp', 'c_corp']:
        quarterly_tax_guidance['additional_guidance'] = 'S and C corporations have different estimated tax requirements. Corporations use Form 1120-W for estimated payments.'
    elif business_type in ['llc_single', 'llc_multi']:
        quarterly_tax_guidance['additional_guidance'] = 'Single-member LLCs file estimated taxes as individuals using Form 1040-ES. Multi-member LLCs may need to pay estimates at both partnership and individual level.'
    
    return quarterly_tax_guidance

def calculate_estimated_tax(business_type, annual_revenue):
    """Calculate rough estimated tax for quarterly payment guidance"""
    # Very simplified estimate for demo purposes
    # In a real app, this would use more sophisticated calculations
    estimated_profit = annual_revenue * 0.7  # Assume 70% profit margin
    
    if business_type in ['sole_proprietor', 'llc_single']:
        # Approximate self-employment and income tax
        return round(estimated_profit * 0.35, 2)
    elif business_type in ['llc_multi', 's_corp']:
        # Approximate income tax only for pass-through
        return round(estimated_profit * 0.25, 2)
    elif business_type == 'c_corp':
        # Flat 21% corporate tax rate
        return round(estimated_profit * 0.21, 2)
    else:
        # Default calculation
        return round(estimated_profit * 0.3, 2)

def get_state_specific_tip(state, business_type):
    """Get state-specific tax tip"""
    state_tips = {
        'CA': {
            'tip': 'California LLC Fee Planning',
            'description': 'California LLCs pay an annual fee based on gross receipts, ranging from $800 to $11,790. Plan revenue timing to minimize this fee.',
            'estimated_savings': 'Up to $11,790 annually',
            'icon': 'landmark'
        },
        'NY': {
            'tip': 'New York MCTMT Consideration',
            'description': 'Self-employed individuals in the NYC metro area may be subject to Metropolitan Commuter Transportation Mobility Tax on net earnings.',
            'estimated_savings': 'Up to 0.34% of net earnings',
            'icon': 'subway'
        },
        'TX': {
            'tip': 'Texas Franchise Tax Planning',
            'description': 'Texas has no individual income tax, but businesses may be subject to franchise tax. Entities with revenue under $1.23M qualify for the No Tax Due Threshold.',
            'estimated_savings': 'Varies based on revenue',
            'icon': 'landmark'
        },
        'FL': {
            'tip': 'Florida Business Tax Benefits',
            'description': 'Florida has no individual income tax, but C corporations are subject to 5.5% corporate income tax. Consider pass-through entity to maximize state tax advantages.',
            'estimated_savings': 'Up to 5.5% of corporate income',
            'icon': 'sun'
        }
    }
    
    return state_tips.get(state)

def get_common_deduction_categories(business_type):
    """Get common deduction categories for a business type"""
    # Common categories for all businesses
    common_categories = [
        {
            'category': 'Office Expenses',
            'items': ['Office supplies', 'Postage', 'Printing', 'Office furniture under $2,500']
        },
        {
            'category': 'Technology',
            'items': ['Software subscriptions', 'Hardware', 'Website hosting', 'Internet service']
        },
        {
            'category': 'Professional Services',
            'items': ['Accounting fees', 'Legal fees', 'Consulting fees', 'Professional subscriptions']
        },
        {
            'category': 'Marketing & Advertising',
            'items': ['Digital advertising', 'Print materials', 'Business cards', 'Promotional items']
        }
    ]
    
    # Add business-type specific categories
    if business_type in ['sole_proprietor', 'llc_single']:
        common_categories.append({
            'category': 'Self-Employed Benefits',
            'items': ['Health insurance premiums', 'Dental insurance premiums', 'Long-term care premiums', 'HSA contributions']
        })
        common_categories.append({
            'category': 'Home Office',
            'items': ['Dedicated office space', 'Utilities percentage', 'Home insurance percentage', 'Maintenance percentage']
        })
    elif business_type in ['s_corp', 'c_corp']:
        common_categories.append({
            'category': 'Employee Benefits',
            'items': ['Health insurance', 'Retirement plans', 'Education assistance', 'Transportation benefits']
        })
        common_categories.append({
            'category': 'Corporate Formalities',
            'items': ['Board meeting expenses', 'Corporate filing fees', 'Registered agent fees', 'Corporate record keeping']
        })
    
    return common_categories

def get_business_type_display(business_type):
    """Convert business type code to display name"""
    display_names = {
        'sole_proprietor': 'Sole Proprietorship',
        'llc_single': 'Single-Member LLC',
        'llc_multi': 'Multi-Member LLC',
        's_corp': 'S Corporation',
        'c_corp': 'C Corporation',
        'partnership': 'Partnership'
    }
    
    return display_names.get(business_type, business_type)