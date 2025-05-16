"""
Advanced Tax Strategy AI Module

This module uses OpenAI to generate detailed, personalized tax strategies
based on business data and questionnaire responses.
"""

import os
import json
import logging
from datetime import datetime
from app.models import User, UserPlan
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
    # Determine strategy depth based on user plan
    strategy_depth = "basic"
    if user_plan == "fylr_plus":
        strategy_depth = "detailed"
    elif user_plan == "pro":
        strategy_depth = "comprehensive"
    
    # Create system message based on user's plan
    system_message = f"""You are an AI tax strategy assistant for the .fylr tax automation platform. 
Your role is to analyze business data and questionnaire answers to generate personalized tax strategy recommendations.
You should generate {strategy_depth} tax strategies based on the user's subscription level ({user_plan}).

For basic users: Provide general tax saving tips and broad strategies without detailed implementation steps.
For fylr_plus users: Provide more specific strategies with some implementation guidance.
For pro users: Provide comprehensive, detailed strategies with specific implementation steps and potential tax savings estimates.

Always preface your recommendations with a disclaimer that these are suggestions only and not professional tax advice.
All recommendations should be reviewed by a qualified tax professional before implementation.

Tax year for analysis: {tax_year}
"""

    # Create a combined user message with business data and questionnaire answers
    user_message = f"""Please analyze the following business information and questionnaire responses to generate personalized tax strategy recommendations:

BUSINESS INFORMATION:
{json.dumps(business_data, indent=2)}

QUESTIONNAIRE RESPONSES:
{json.dumps(questionnaire_answers, indent=2)}

Based on this information, please generate appropriate tax strategies for a user on the {user_plan} plan for tax year {tax_year}.
"""

    # Get OpenAI response
    try:
        response = get_openai_response(system_message, user_message)
        
        # Process the response to extract strategies
        strategies = parse_strategy_response(response, user_plan)
        
        # If no strategies were extracted, provide fallback strategies
        if not strategies:
            strategies = get_fallback_strategies(business_data, user_plan)
        
        return strategies
    except Exception as e:
        logging.error(f"Error generating tax strategies: {str(e)}")
        return get_fallback_strategies(business_data, user_plan)

def parse_strategy_response(response_text, user_plan):
    """
    Parse the AI response to extract structured strategy recommendations
    
    Args:
        response_text: The text response from OpenAI
        user_plan: The user's plan level
        
    Returns:
        List of strategy dictionaries
    """
    strategies = []
    
    # Try to parse if response already contains structured data
    try:
        # Look for JSON-like structure in the response
        if "```json" in response_text and "```" in response_text.split("```json")[1]:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
            parsed_data = json.loads(json_str)
            
            if isinstance(parsed_data, list):
                strategies = parsed_data
            elif isinstance(parsed_data, dict) and "strategies" in parsed_data:
                strategies = parsed_data["strategies"]
                
        # If strategies were successfully parsed, ensure they have all required fields
        if strategies:
            for strategy in strategies:
                if "strategy_name" not in strategy:
                    strategy["strategy_name"] = "Tax Saving Strategy"
                if "description" not in strategy:
                    strategy["description"] = "A strategy to help reduce tax liability."
                if "estimated_savings" not in strategy:
                    strategy["estimated_savings"] = None
                if "implementation_steps" not in strategy:
                    strategy["implementation_steps"] = []
                if "qualifications" not in strategy:
                    strategy["qualifications"] = []
                if "tier" not in strategy:
                    strategy["tier"] = user_plan
                strategy["created_at"] = datetime.now().isoformat()
    except Exception as e:
        logging.error(f"Error parsing strategy response: {str(e)}")
    
    # If we couldn't parse structured data, try to extract strategies from text
    if not strategies:
        try:
            # Split by numbered sections or headers
            sections = []
            lines = response_text.split("\n")
            current_section = []
            
            for line in lines:
                # Look for patterns like "1.", "Strategy 1:", etc.
                if (line.strip().startswith(("#", "##")) or 
                    any(pattern in line for pattern in ["Strategy", "Recommendation"]) or
                    (line.strip() and line.strip()[0].isdigit() and line.strip()[1:3] in [". ", ") ", ": "])):
                    
                    if current_section:
                        sections.append("\n".join(current_section))
                        current_section = []
                
                current_section.append(line)
            
            if current_section:
                sections.append("\n".join(current_section))
            
            # Process each section into a strategy
            for i, section in enumerate(sections):
                if i == 0 and "disclaimer" in section.lower():
                    continue  # Skip disclaimer section
                
                # Extract strategy name and description
                lines = section.split("\n")
                strategy_name = lines[0].strip().strip("#:.-1234567890 ")
                
                if not strategy_name or len(strategy_name) > 100:
                    strategy_name = f"Tax Strategy {i+1}"
                
                description = "\n".join(lines[1:]).strip()
                
                strategy = {
                    "strategy_name": strategy_name,
                    "description": description,
                    "estimated_savings": None,
                    "implementation_steps": [],
                    "qualifications": [],
                    "tier": user_plan,
                    "created_at": datetime.now().isoformat()
                }
                
                strategies.append(strategy)
        except Exception as e:
            logging.error(f"Error extracting strategies from text: {str(e)}")
    
    return strategies

def get_fallback_strategies(business_data, user_plan):
    """
    Generate fallback strategies if AI generation fails
    
    Args:
        business_data: Dictionary containing business information
        user_plan: The user's plan level
        
    Returns:
        List of strategy dictionaries
    """
    # Common strategies for all business types
    common_strategies = [
        {
            "strategy_name": "Maximize Business Deductions",
            "description": "Ensure you're taking all eligible business deductions including home office, travel, meals, and vehicle expenses.",
            "estimated_savings": None,
            "implementation_steps": [
                "Track all business expenses throughout the year",
                "Keep thorough documentation of receipts and business purpose",
                "Review IRS Publication 535 for eligible business deductions"
            ],
            "qualifications": [],
            "tier": "basic",
            "created_at": datetime.now().isoformat()
        },
        {
            "strategy_name": "Retirement Plan Contributions",
            "description": "Contribute to retirement plans like a SEP IRA, Solo 401(k), or SIMPLE IRA to reduce taxable income.",
            "estimated_savings": None,
            "implementation_steps": [
                "Determine which retirement plan best fits your business",
                "Calculate maximum allowable contribution",
                "Set up automatic contributions on a regular schedule"
            ],
            "qualifications": [],
            "tier": "basic",
            "created_at": datetime.now().isoformat()
        }
    ]
    
    # Strategies for fylr_plus and pro users
    advanced_strategies = [
        {
            "strategy_name": "Strategic Business Entity Selection",
            "description": "Review your business entity structure to ensure it provides optimal tax benefits for your specific situation.",
            "estimated_savings": "Varies",
            "implementation_steps": [
                "Analyze current entity structure tax implications",
                "Compare potential savings of alternative structures",
                "Consult with tax professional about costs and benefits of changing"
            ],
            "qualifications": [
                "Entity changes should typically be made at the beginning of a tax year",
                "Consider both federal and state tax implications"
            ],
            "tier": "fylr_plus",
            "created_at": datetime.now().isoformat()
        },
        {
            "strategy_name": "Cost Segregation Study",
            "description": "For businesses with significant property assets, consider a cost segregation study to accelerate depreciation deductions.",
            "estimated_savings": "$10,000+",
            "implementation_steps": [
                "Engage a specialized cost segregation firm",
                "Have them analyze your property and reclassify assets",
                "Apply accelerated depreciation to eligible components"
            ],
            "qualifications": [
                "Most beneficial for commercial real estate with acquisition cost over $500,000",
                "Particularly valuable in first few years of ownership"
            ],
            "tier": "pro",
            "created_at": datetime.now().isoformat()
        },
        {
            "strategy_name": "Qualified Business Income Deduction Optimization",
            "description": "Maximize your Section 199A Qualified Business Income Deduction through strategic income planning.",
            "estimated_savings": "Up to 20% of qualified business income",
            "implementation_steps": [
                "Analyze current income levels and threshold limitations",
                "Consider adjusting W-2 wages or qualified property basis if beneficial",
                "Evaluate potential business restructuring to maximize deduction"
            ],
            "qualifications": [
                "Benefits phase out for certain service businesses over income thresholds",
                "Complex rules apply based on business type and income level"
            ],
            "tier": "pro",
            "created_at": datetime.now().isoformat()
        }
    ]
    
    # Determine which strategies to include based on user's plan
    if user_plan == "basic":
        return common_strategies
    elif user_plan == "fylr_plus":
        return common_strategies + [s for s in advanced_strategies if s["tier"] == "fylr_plus"]
    else:  # pro
        return common_strategies + advanced_strategies

def get_entity_optimization(business_data, questionnaire_answers):
    """
    Generate recommendations for optimal business entity structure
    
    Args:
        business_data: Dictionary containing business information
        questionnaire_answers: Dictionary containing questionnaire responses
        
    Returns:
        Dictionary with entity recommendations and comparisons
    """
    current_entity = business_data.get("entity_type", "sole_proprietor")
    annual_revenue = business_data.get("annual_revenue", 100000)
    has_employees = business_data.get("has_employees", False)
    industry = business_data.get("industry", "service")
    risk_level = questionnaire_answers.get("risk_level", "medium")
    tax_preferences = questionnaire_answers.get("tax_preferences", {})
    
    # Create system message
    system_message = """You are an AI tax entity optimization assistant for the .fylr tax automation platform.
Your role is to analyze business data and questionnaire answers to recommend the optimal business entity structure.
Provide a thorough comparison of entity options with pros and cons for each, including tax implications.

Include these entity types in your analysis:
- Sole Proprietorship
- Single-Member LLC
- Multi-Member LLC
- S Corporation
- C Corporation

For each entity type, address:
1. Tax implications
2. Liability protection
3. Administrative complexity
4. Cost to establish and maintain
5. Flexibility and growth considerations

Provide your recommendation in a structured format that can be parsed as JSON.
"""

    # Create user message
    user_message = f"""Please analyze the following business information and questionnaire responses to recommend the optimal business entity structure:

BUSINESS INFORMATION:
Current Entity Type: {current_entity}
Annual Revenue: ${annual_revenue}
Has Employees: {has_employees}
Industry: {industry}

QUESTIONNAIRE RESPONSES:
Risk Tolerance: {risk_level}
Tax Preferences: {json.dumps(tax_preferences, indent=2)}

Based on this information, please recommend the optimal business entity structure with a detailed comparison of options.
"""

    # Get OpenAI response
    try:
        response = get_openai_response(system_message, user_message, json_response=True)
        
        # Ensure the response has the expected structure
        if not isinstance(response, dict):
            response = {
                "recommended_entity": "Unknown",
                "recommendation_summary": "Unable to generate recommendation",
                "entity_comparisons": []
            }
        
        if "recommended_entity" not in response:
            response["recommended_entity"] = "Unknown"
        
        if "recommendation_summary" not in response:
            response["recommendation_summary"] = "Unable to generate recommendation summary"
        
        if "entity_comparisons" not in response or not isinstance(response["entity_comparisons"], list):
            response["entity_comparisons"] = []
        
        return response
    except Exception as e:
        logging.error(f"Error generating entity optimization: {str(e)}")
        
        # Return fallback response
        return {
            "recommended_entity": "Consult Professional",
            "recommendation_summary": "We were unable to generate an automated recommendation at this time. Please consult with a tax professional for personalized entity structure advice.",
            "entity_comparisons": [
                {
                    "entity_type": "Sole Proprietorship",
                    "pros": [
                        "Simple to form and operate",
                        "No separate business tax return",
                        "Easy to dissolve"
                    ],
                    "cons": [
                        "No liability protection",
                        "Subject to self-employment tax on all profits",
                        "May limit funding opportunities"
                    ]
                },
                {
                    "entity_type": "LLC",
                    "pros": [
                        "Liability protection",
                        "Pass-through taxation by default",
                        "Flexible management structure"
                    ],
                    "cons": [
                        "More formalities than sole proprietorship",
                        "Subject to self-employment tax on all profits",
                        "Annual fees in some states"
                    ]
                },
                {
                    "entity_type": "S Corporation",
                    "pros": [
                        "Liability protection",
                        "Potential self-employment tax savings",
                        "Pass-through taxation"
                    ],
                    "cons": [
                        "More formalities and compliance requirements",
                        "Ownership restrictions",
                        "Must pay reasonable salary subject to payroll taxes"
                    ]
                },
                {
                    "entity_type": "C Corporation",
                    "pros": [
                        "Liability protection",
                        "No ownership restrictions",
                        "Attractive to investors"
                    ],
                    "cons": [
                        "Double taxation on dividends",
                        "Most complex entity type",
                        "Higher compliance and administrative costs"
                    ]
                }
            ]
        }

def analyze_expense_categories(expenses_data):
    """
    Analyze expense categories and identify potential deduction opportunities
    
    Args:
        expenses_data: Dictionary containing business expense data
        
    Returns:
        Dictionary with optimization opportunities
    """
    system_message = """You are an AI expense optimization assistant for the .fylr tax automation platform.
Your role is to analyze business expense data and identify potential tax deduction opportunities or areas of concern.
Look for:

1. Missing common deductions in the industry
2. Expense categories that may need reclassification for better tax treatment
3. Expenses that might trigger audit flags
4. Opportunities to accelerate or defer expenses for optimal tax planning

Provide your analysis in a structured JSON format with identified opportunities.
"""

    user_message = f"""Please analyze the following business expense data to identify potential tax deduction opportunities:

EXPENSE DATA:
{json.dumps(expenses_data, indent=2)}

Based on this information, please identify optimization opportunities, potential issues, and actionable recommendations.
"""

    # Get OpenAI response
    try:
        response = get_openai_response(system_message, user_message, json_response=True)
        
        # Ensure the response has the expected structure
        if not isinstance(response, dict):
            response = {
                "optimization_summary": "Unable to generate optimization analysis",
                "identified_opportunities": [],
                "potential_issues": [],
                "recommendations": []
            }
        
        if "optimization_summary" not in response:
            response["optimization_summary"] = "Unable to generate optimization summary"
        
        if "identified_opportunities" not in response or not isinstance(response["identified_opportunities"], list):
            response["identified_opportunities"] = []
        
        if "potential_issues" not in response or not isinstance(response["potential_issues"], list):
            response["potential_issues"] = []
            
        if "recommendations" not in response or not isinstance(response["recommendations"], list):
            response["recommendations"] = []
        
        return response
    except Exception as e:
        logging.error(f"Error analyzing expense categories: {str(e)}")
        
        # Return fallback response
        return {
            "optimization_summary": "We were unable to perform an automated expense analysis at this time. Consider reviewing your expense categories manually.",
            "identified_opportunities": [
                {
                    "category": "General",
                    "opportunity": "Review expense categorization",
                    "potential_benefit": "Improved accuracy and potentially increased deductions"
                }
            ],
            "potential_issues": [
                {
                    "category": "General",
                    "issue": "Unable to analyze specific expense categories",
                    "recommendation": "Review expense categorization manually"
                }
            ],
            "recommendations": [
                "Consult with a tax professional for a detailed expense analysis",
                "Ensure all business expenses are properly documented with receipts and business purpose notes",
                "Consider implementing an expense tracking system for more detailed categorization"
            ]
        }

def generate_estimated_tax_plan(income_projections, quarterly_data):
    """
    Generate a quarterly estimated tax payment plan
    
    Args:
        income_projections: Dictionary with projected income by quarter
        quarterly_data: Historical quarterly financial data
        
    Returns:
        Dictionary with quarterly tax payment recommendations
    """
    system_message = """You are an AI estimated tax planning assistant for the .fylr tax automation platform.
Your role is to analyze projected income and historical data to recommend quarterly estimated tax payments.
Consider:

1. Projected quarterly income and expenses
2. Historical quarterly patterns
3. Safe harbor rules for estimated taxes
4. Cash flow considerations

Provide a detailed quarterly payment plan in a structured JSON format.
"""

    user_message = f"""Please analyze the following income projections and historical data to generate a quarterly estimated tax payment plan:

INCOME PROJECTIONS:
{json.dumps(income_projections, indent=2)}

HISTORICAL QUARTERLY DATA:
{json.dumps(quarterly_data, indent=2)}

Based on this information, please generate a recommended quarterly estimated tax payment plan.
"""

    # Get OpenAI response
    try:
        response = get_openai_response(system_message, user_message, json_response=True)
        
        # Ensure the response has the expected structure
        if not isinstance(response, dict):
            response = {
                "plan_summary": "Unable to generate estimated tax plan",
                "estimated_annual_tax": 0,
                "quarterly_payments": [],
                "considerations": []
            }
        
        if "plan_summary" not in response:
            response["plan_summary"] = "Unable to generate plan summary"
        
        if "estimated_annual_tax" not in response:
            response["estimated_annual_tax"] = 0
        
        if "quarterly_payments" not in response or not isinstance(response["quarterly_payments"], list):
            response["quarterly_payments"] = []
            
        if "considerations" not in response or not isinstance(response["considerations"], list):
            response["considerations"] = []
        
        return response
    except Exception as e:
        logging.error(f"Error generating estimated tax plan: {str(e)}")
        
        # Return fallback response
        current_year = datetime.now().year
        
        # Calculate simple quarterly payments based on projected annual income
        annual_income = sum(quarter.get("projected_income", 0) for quarter in income_projections.values())
        estimated_annual_tax = annual_income * 0.25  # Simple approximation
        quarterly_payment = estimated_annual_tax / 4
        
        return {
            "plan_summary": "Basic estimated tax payment plan based on projected annual income",
            "estimated_annual_tax": estimated_annual_tax,
            "quarterly_payments": [
                {
                    "quarter": "Q1",
                    "due_date": f"{current_year}-04-15",
                    "amount": quarterly_payment,
                    "notes": "First quarter estimated payment"
                },
                {
                    "quarter": "Q2",
                    "due_date": f"{current_year}-06-15",
                    "amount": quarterly_payment,
                    "notes": "Second quarter estimated payment"
                },
                {
                    "quarter": "Q3",
                    "due_date": f"{current_year}-09-15",
                    "amount": quarterly_payment,
                    "notes": "Third quarter estimated payment"
                },
                {
                    "quarter": "Q4",
                    "due_date": f"{current_year}-01-15",
                    "amount": quarterly_payment,
                    "notes": "Fourth quarter estimated payment"
                }
            ],
            "considerations": [
                "This is a basic estimate only. Consult with a tax professional for more accurate projections.",
                "Consider safe harbor rules to avoid underpayment penalties.",
                "Adjust quarterly payments if income differs significantly from projections."
            ]
        }