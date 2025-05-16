"""
Advanced Tax Strategy AI Module

This module uses OpenAI to generate detailed, personalized tax strategies
based on business data and questionnaire responses.
"""

import os
import json
from datetime import datetime
from ai.openai_interface import get_openai_response

def generate_detailed_strategies(business_data, questionnaire_answers, tax_year, user_plan="basic"):
    """
    Generate detailed tax strategies based on business data and questionnaire answers
    
    Args:
        business_data: Dictionary containing business information
        questionnaire_answers: Dictionary containing questionnaire responses
        tax_year: The tax year for which strategies are generated
        user_plan: The user's plan level (basic, fylr_plus, pro)
        
    Returns:
        List of tax strategy recommendations
    """
    # Create a context object with all relevant information
    context = {
        "business_data": business_data,
        "questionnaire_answers": questionnaire_answers,
        "tax_year": tax_year,
        "current_date": datetime.now().strftime("%Y-%m-%d"),
        "user_plan": user_plan
    }
    
    # Define the detail level based on user plan
    if user_plan == "basic":
        detail_level = "basic"
        max_strategies = 3
    elif user_plan == "fylr_plus":
        detail_level = "intermediate"
        max_strategies = 6
    else:  # Pro plan
        detail_level = "advanced"
        max_strategies = 10
    
    # Create the system prompt for the AI
    system_prompt = f"""
    You are an AI tax strategy expert for the .fylr tax automation platform.
    Generate {max_strategies} personalized tax strategies based on the business information
    and questionnaire answers provided. The recommendations should be appropriate for
    a {detail_level} level of detail.
    
    For each strategy, include:
    1. A descriptive title
    2. A detailed explanation of the strategy
    3. Estimated potential tax savings (as a range or percentage)
    4. Implementation complexity (Easy, Moderate, Complex)
    5. Required documentation
    6. Relevant tax code references
    7. Risk level (Low, Medium, High)
    
    Focus on legitimate tax strategies that are compliant with current tax law.
    Consider the specific business type, revenue level, and industry.
    """
    
    # Create the user message with the context
    user_message = f"""
    Generate tax strategies for the following business:
    
    Business Type: {business_data.get('business_type', 'Unknown')}
    Industry: {business_data.get('industry', 'Unknown')}
    Revenue: {business_data.get('revenue', 'Unknown')}
    Number of Employees: {business_data.get('employees', 0)}
    State: {business_data.get('state', 'Unknown')}
    Tax Year: {tax_year}
    
    Questionnaire answers:
    {json.dumps(questionnaire_answers, indent=2)}
    
    Provide strategies appropriate for a user on the {user_plan} plan with {detail_level} detail level.
    """
    
    # Get response from OpenAI
    response = get_openai_response(system_prompt, user_message, json_response=True)
    
    # Process and format the response
    strategies = []
    if isinstance(response, list):
        for strategy in response:
            strategies.append({
                "title": strategy.get("title", "Tax Strategy"),
                "description": strategy.get("explanation", ""),
                "potential_savings": strategy.get("potential_savings", "Varies"),
                "complexity": strategy.get("implementation_complexity", "Moderate"),
                "documentation": strategy.get("required_documentation", []),
                "tax_code_references": strategy.get("tax_code_references", []),
                "risk_level": strategy.get("risk_level", "Medium"),
                "implementation_steps": strategy.get("implementation_steps", [])
            })
    
    return strategies

def get_entity_optimization(business_data, questionnaire_answers):
    """
    Generate recommendations for optimal business entity structure
    
    Args:
        business_data: Dictionary containing business information
        questionnaire_answers: Dictionary containing questionnaire responses
        
    Returns:
        Dictionary with entity recommendations and comparisons
    """
    # Create the system prompt for the AI
    system_prompt = """
    You are an AI tax entity specialist for the .fylr tax automation platform.
    Analyze the provided business information and recommend the optimal business
    entity structure (Sole Proprietorship, LLC, S-Corporation, C-Corporation, or Partnership).
    
    Your response should include:
    1. The recommended entity type
    2. Pros and cons of the recommended entity
    3. Comparison with current entity structure (if different)
    4. Estimated tax savings from entity change
    5. Implementation requirements and timeline
    6. Potential pitfalls to consider
    """
    
    # Create the user message with the context
    user_message = f"""
    Analyze the optimal entity structure for this business:
    
    Current Entity Type: {business_data.get('business_type', 'Unknown')}
    Industry: {business_data.get('industry', 'Unknown')}
    Revenue: {business_data.get('revenue', 'Unknown')}
    Net Profit: {business_data.get('net_profit', 'Unknown')}
    Number of Employees: {business_data.get('employees', 0)}
    Number of Owners: {business_data.get('owners', 1)}
    Owner Compensation: {business_data.get('owner_compensation', 'Unknown')}
    State: {business_data.get('state', 'Unknown')}
    Growth Plans: {questionnaire_answers.get('growth_plans', 'Unknown')}
    
    Additional information:
    {json.dumps(questionnaire_answers, indent=2)}
    """
    
    # Get response from OpenAI
    response = get_openai_response(system_prompt, user_message, json_response=True)
    
    return response

def analyze_expense_categories(expenses_data):
    """
    Analyze expense categories and identify potential deduction opportunities
    
    Args:
        expenses_data: Dictionary containing business expense data
        
    Returns:
        Dictionary with optimization opportunities
    """
    # Create the system prompt for the AI
    system_prompt = """
    You are an AI expense optimization specialist for the .fylr tax automation platform.
    Analyze the provided business expense data and identify potential deduction
    opportunities, misclassifications, or audit risk areas.
    
    Your response should include:
    1. Potentially missed deductions
    2. Expense categories that appear to be misclassified
    3. Expenses that may trigger audit flags
    4. Recommendations for better expense tracking
    5. Industry-specific expense optimizations
    """
    
    # Create the user message with the context
    user_message = f"""
    Analyze these business expenses for optimization opportunities:
    
    Industry: {expenses_data.get('industry', 'Unknown')}
    Business Type: {expenses_data.get('business_type', 'Unknown')}
    
    Expense Categories:
    {json.dumps(expenses_data.get('categories', {}), indent=2)}
    
    Top Vendors by Spend:
    {json.dumps(expenses_data.get('top_vendors', []), indent=2)}
    
    Provide specific recommendations for optimizing tax deductions based on this data.
    """
    
    # Get response from OpenAI
    response = get_openai_response(system_prompt, user_message, json_response=True)
    
    return response

def generate_estimated_tax_plan(income_projections, quarterly_data):
    """
    Generate a quarterly estimated tax payment plan
    
    Args:
        income_projections: Dictionary with projected income by quarter
        quarterly_data: Historical quarterly financial data
        
    Returns:
        Dictionary with quarterly tax payment recommendations
    """
    # Create the system prompt for the AI
    system_prompt = """
    You are an AI estimated tax specialist for the .fylr tax automation platform.
    Generate a quarterly estimated tax payment plan based on income projections
    and historical data to help the business avoid underpayment penalties while
    optimizing cash flow.
    
    Your response should include:
    1. Recommended quarterly payment amounts
    2. Safe harbor analysis
    3. Cash flow optimization strategies
    4. Payment deadline reminders
    5. State estimated tax considerations
    """
    
    # Create the user message with the context
    user_message = f"""
    Generate a quarterly estimated tax plan for this business:
    
    Income Projections:
    {json.dumps(income_projections, indent=2)}
    
    Historical Quarterly Data:
    {json.dumps(quarterly_data, indent=2)}
    
    Provide recommendations for optimal quarterly tax payments that avoid penalties
    while preserving cash flow.
    """
    
    # Get response from OpenAI
    response = get_openai_response(system_prompt, user_message, json_response=True)
    
    return response