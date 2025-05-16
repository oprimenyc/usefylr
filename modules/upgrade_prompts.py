"""
Upgrade Prompts Module

This module provides functions to determine when to show upgrade prompts
based on user data and business complexity.
"""

def should_show_upgrade_prompt(user, business_data):
    """
    Determine if an upgrade prompt should be shown based on user plan and business data
    
    Args:
        user: The current user object
        business_data: Dictionary containing business information
        
    Returns:
        Boolean indicating whether to show upgrade prompt
    """
    # Don't show prompts for users who already have the concierge plan (highest tier)
    if user.plan == 'concierge':
        return False
    
    # Check if the business type is eligible for higher tiers
    business_type = business_data.get('entity_type', 'sole_proprietor')
    current_tier = user.plan
    
    # S-corps and C-corps require at least guided tier
    if business_type in ['s_corp', 'c_corp'] and current_tier == 'self_service':
        return True
    
    # Check if any upgrade triggers apply based on current tier
    if current_tier == 'self_service':
        if any([
            has_high_audit_risk(business_data),
            has_inconsistent_documentation(business_data),
            has_entity_complexity_trigger(business_data)
        ]):
            return True
    
    if current_tier in ['self_service', 'guided']:
        if any([
            has_optimization_opportunity(business_data),
            has_employee_trigger(business_data),
            has_capital_gains(business_data)
        ]):
            return True
    
    return False

def get_upgrade_prompt_message(user, business_data, context=None):
    """
    Get an appropriate upgrade prompt message based on the detected triggers
    
    Args:
        user: The current user object
        business_data: Dictionary containing business information
        context: Optional context string (e.g., 'tax_strategy', 'form_filling')
        
    Returns:
        Tuple of (prompt_message, prompt_title, prompt_cta)
    """
    current_tier = user.plan
    business_type = business_data.get('entity_type', 'sole_proprietor')
    
    # Default message
    message = "Looks like your business may benefit from advanced strategy. Unlock audit protection and detailed filing review with .fylr Guided or Concierge Plans."
    title = "Upgrade Recommended"
    cta = "Explore Premium Plans"
    next_tier = "guided"  # Default next tier
    
    # Business type restrictions for S-corps and C-corps
    if business_type in ['s_corp', 'c_corp'] and current_tier == 'self_service':
        message = f"Your {business_type.replace('_', ' ').title()} requires our Guided or Concierge plan for proper handling. Upgrade to access specialized entity support, compliance checks, and AI-powered tax strategies."
        title = "Entity Type Requires Upgrade"
        next_tier = "guided"
    
    # Self-service tier upgrade triggers
    elif current_tier == 'self_service':
        if has_high_audit_risk(business_data):
            message = "We've detected a higher audit risk pattern in your business data. Upgrade to our Guided plan to access AI-powered review checklist with compliance warnings and smart alerts for deductions and credits."
            title = "Reduce Audit Risk"
            next_tier = "guided"
            
        elif has_inconsistent_documentation(business_data):
            message = "We've noticed potential gaps in your documentation. Our Guided plan provides smart alerts and a review checklist to ensure your filing is complete and compliant."
            title = "Documentation Assistance Available"
            next_tier = "guided"
            
        elif has_entity_complexity_trigger(business_data):
            message = "Your business structure suggests increased complexity. Upgrade to our Guided plan for AI-powered tax strategy recommendations and compliance warnings tailored to your entity type."
            title = "Entity-Optimized Tax Strategies Available"
            next_tier = "guided"
    
    # Concierge upgrade triggers for both self-service and guided tiers
    elif current_tier in ['self_service', 'guided']:
        if has_optimization_opportunity(business_data):
            message = "We've identified significant optimization opportunities. Our Concierge plan offers AI-reviewed tax packages and advanced tax strategies that could maximize your savings."
            title = "Tax Optimization Opportunity"
            next_tier = "concierge"
            
        elif has_employee_trigger(business_data):
            message = "Businesses with employees or contractors face additional compliance requirements. Our Concierge plan includes automated document collection and audit protection to handle complex employment tax situations."
            title = "Employee Tax Support Available"
            next_tier = "concierge"
            
        elif has_capital_gains(business_data):
            message = "We've noticed capital gains or losses in your business activity. Our Concierge plan offers advanced tax strategies and AI-reviewed filing to optimize capital gains treatment."
            title = "Capital Gains Optimization Available"
            next_tier = "concierge"
    
    # Customize call-to-action based on context
    if context == 'tax_strategy':
        if next_tier == "guided":
            cta = "Unlock AI Tax Strategies"
        else:
            cta = "Get Advanced Tax Optimization"
    elif context == 'form_filling':
        if next_tier == "guided":
            cta = "Get Smart Alerts & Review"
        else:
            cta = "Upgrade to AI-Reviewed Filing"
    elif context == 'audit_risk':
        if next_tier == "concierge":
            cta = "Get Audit Protection Plan"
        else:
            cta = "Reduce Audit Risk"
    else:
        # Default CTAs based on next tier
        if next_tier == "guided":
            cta = f"Upgrade to Guided Plan ($197)"
        else:
            cta = f"Upgrade to Concierge Plan ($497)"
    
    return (message, title, cta)

# Trigger detection functions
def has_high_audit_risk(business_data):
    """Check if business has indicators of high audit risk"""
    risk_factors = [
        business_data.get('high_cash_transactions', False),
        business_data.get('home_office_deduction', False) and business_data.get('annual_revenue', 0) > 100000,
        business_data.get('reported_losses', 0) >= 3,  # Multiple years of losses
        business_data.get('large_charitable_contributions', False),
        business_data.get('vehicle_deduction', 0) > 10000,
    ]
    return sum(risk_factors) >= 2

def has_inconsistent_documentation(business_data):
    """Check if business has inconsistent or incomplete documentation"""
    return business_data.get('missing_receipts', False) or business_data.get('incomplete_records', False)

def has_entity_complexity_trigger(business_data):
    """Check if business has a complex entity structure"""
    entity_type = business_data.get('entity_type', '').lower()
    return entity_type in ['s_corp', 'c_corp', 'partnership', 'llc_multi']

def has_optimization_opportunity(business_data):
    """Check if business has significant optimization opportunities"""
    revenue = business_data.get('annual_revenue', 0)
    expense_ratio = business_data.get('expense_ratio', 0.5)
    deduction_opportunities = business_data.get('potential_deductions', [])
    
    return (revenue > 150000 or 
            expense_ratio < 0.4 or  # Low expense ratio suggests missed deductions
            len(deduction_opportunities) >= 3)

def has_employee_trigger(business_data):
    """Check if business has employees or contractors"""
    employee_count = business_data.get('employee_count', 0)
    contractor_count = business_data.get('contractor_count', 0)
    return employee_count > 0 or contractor_count > 1

def has_capital_gains(business_data):
    """Check if business has capital gains or losses"""
    return business_data.get('has_capital_gains', False) or business_data.get('has_capital_losses', False)