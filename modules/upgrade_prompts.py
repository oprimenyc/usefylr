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
    # Don't show prompts for users who already have premium plans
    if user.plan in ['pro', 'concierge']:
        return False
    
    # Check if any upgrade triggers apply
    if any([
        has_high_revenue_trigger(business_data),
        has_multiple_states_trigger(business_data),
        has_entity_complexity_trigger(business_data),
        has_employee_trigger(business_data),
        has_deduction_opportunity_trigger(business_data)
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
    # Default message
    message = "Looks like your business may benefit from advanced strategy. Unlock audit protection and detailed filing review with .fylr Pro or Concierge Plans."
    title = "Upgrade Recommended"
    cta = "Explore Premium Plans"
    
    # Customize message based on the highest priority trigger
    if has_high_revenue_trigger(business_data):
        message = "Your business revenue level suggests increased tax complexity. Upgrade to .fylr Pro to unlock advanced tax strategies, audit protection, and personalized recommendations that could increase your deductions."
        title = "Revenue-Optimized Tax Strategies Available"
        
    elif has_multiple_states_trigger(business_data):
        message = "Operating in multiple states creates complex tax obligations. Upgrade to .fylr Pro for multi-state filing guidance, nexus analysis, and state-specific deduction strategies."
        title = "Multi-State Tax Support Available"
        
    elif has_entity_complexity_trigger(business_data):
        message = "Your business structure requires specialized tax planning. Upgrade to .fylr Pro for S-Corp tax optimization, entity-specific strategies, and compliance support."
        title = "Entity-Optimized Tax Strategies Available"
        
    elif has_employee_trigger(business_data):
        message = "Businesses with employees face additional tax requirements. Upgrade to .fylr Pro for payroll tax guidance, employee benefit strategies, and compliance assistance."
        title = "Employee Tax Optimization Available"
        
    elif has_deduction_opportunity_trigger(business_data):
        message = "We've identified potential tax saving opportunities. Upgrade to .fylr Pro to unlock AI-powered deduction finding and tax strategy recommendations."
        title = "Potential Tax Savings Identified"
    
    # Customize further based on context
    if context == 'tax_strategy':
        cta = "Unlock Advanced Strategies"
    elif context == 'form_filling':
        cta = "Access Premium Forms"
    elif context == 'audit_risk':
        cta = "Get Audit Protection"
    
    return (message, title, cta)

# Trigger detection functions
def has_high_revenue_trigger(business_data):
    """Check if business has high revenue that warrants an upgrade prompt"""
    revenue = business_data.get('annual_revenue', 0)
    return revenue >= 100000

def has_multiple_states_trigger(business_data):
    """Check if business operates in multiple states"""
    states = business_data.get('states', [])
    return len(states) > 1

def has_entity_complexity_trigger(business_data):
    """Check if business has a complex entity structure"""
    entity_type = business_data.get('entity_type', '').lower()
    return entity_type in ['s_corp', 'c_corp', 'partnership', 'llc_multi']

def has_employee_trigger(business_data):
    """Check if business has employees"""
    employee_count = business_data.get('employee_count', 0)
    return employee_count > 0

def has_deduction_opportunity_trigger(business_data):
    """Check if business has potential for significant deductions"""
    has_home_office = business_data.get('has_home_office', False)
    has_vehicle = business_data.get('has_vehicle', False)
    has_travel = business_data.get('has_travel_expenses', False)
    has_equipment = business_data.get('has_equipment_purchases', False)
    
    # If at least 3 potential deduction categories, show upgrade prompt
    deduction_factors = [has_home_office, has_vehicle, has_travel, has_equipment]
    return sum(deduction_factors) >= 3