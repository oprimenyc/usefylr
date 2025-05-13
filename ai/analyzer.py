import os
import json
import logging
from ai.openai_interface import get_openai_response

def load_prompts():
    """Load prompts from prompts.json"""
    try:
        with open(os.path.join(os.path.dirname(__file__), 'prompts.json'), 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading prompts: {str(e)}")
        return {}

def analyze_tax_answers(answers):
    """Analyze tax questionnaire answers and provide strategies"""
    try:
        prompts = load_prompts()
        if not prompts:
            return None
        
        # Format answers for the prompt
        answers_text = "\n".join([f"- {q}: {'Yes' if v else 'No'}" for q, v in answers.items()])
        
        # Get the strategy analyzer prompt
        strategy_prompt = prompts.get("strategy_analyzer", {})
        if not strategy_prompt:
            return None
        
        # Format the user message
        user_message = strategy_prompt["user_template"].format(answers=answers_text)
        
        # Get response from OpenAI
        response = get_openai_response(
            system_message=strategy_prompt["system"],
            user_message=user_message,
            model="gpt-4o",  # The newest OpenAI model is "gpt-4o" which was released May 13, 2024
            json_response=True
        )
        
        if response and 'strategies' in response:
            return response['strategies']
        else:
            return None
    except Exception as e:
        logging.error(f"Error analyzing tax answers: {str(e)}")
        return None

def generate_tax_strategies(answers):
    """Generate tax strategies based on questionnaire answers"""
    try:
        # Convert answer keys to full questions for better context
        question_map = {
            "do_you_have": "Do you have any employees besides yourself?",
            "did_you_purchase": "Did you purchase any new equipment this year?",
            "do_you_rent": "Do you rent or own your office/workspace?",
            "did_you_earn": "Did you earn income from software, consulting, or digital services?",
            "do_you_have": "Do you have a retirement plan through your business?",
            "do_you_work": "Do you work from home at least 20 hours a week?",
            "was_your_net": "Was your net income above $50,000 this year?",
            "did_you_pay": "Did you pay yourself via payroll or owner draws?"
        }
        
        # Build formatted answers
        formatted_answers = {}
        for key, value in answers.items():
            question = question_map.get(key, key)
            formatted_answers[question] = "Yes" if value else "No"
        
        # Try to use AI for strategy generation
        ai_strategies = analyze_tax_answers(formatted_answers)
        
        if ai_strategies:
            return ai_strategies
        
        # Fallback to simple strategy logic if AI fails
        strategies = []
        
        if answers.get("do_you_work", False):
            strategies.append({
                "name": "Home Office Deduction",
                "description": "You may qualify for the home office deduction since you work from home at least 20 hours per week. This allows you to deduct a portion of your home expenses including rent/mortgage, utilities, and insurance as business expenses.",
                "estimated_savings": 1200
            })
        
        if answers.get("did_you_purchase", False):
            strategies.append({
                "name": "Section 179 Deduction",
                "description": "Since you purchased new equipment this year, you might qualify for Section 179 deduction, allowing you to immediately expense up to $1,050,000 of qualifying equipment rather than depreciating it over several years.",
                "estimated_savings": 5000
            })
        
        if answers.get("do_you_have", False):
            strategies.append({
                "name": "Retirement Plan Contributions",
                "description": "Maximize contributions to your business retirement plan. For a SEP IRA, you can contribute up to 25% of your net self-employment income (maximum $58,000 for 2021). These contributions are tax-deductible and allow you to build retirement savings.",
                "estimated_savings": 4000
            })
        
        if answers.get("did_you_earn", False):
            strategies.append({
                "name": "Qualified Business Income (QBI) Deduction",
                "description": "As a provider of software, consulting, or digital services, you may qualify for the QBI deduction under Section 199A, which allows eligible business owners to deduct up to 20% of their qualified business income from their taxable income.",
                "estimated_savings": 5000
            })
        
        return strategies
    except Exception as e:
        logging.error(f"Error generating tax strategies: {str(e)}")
        return []

def get_form_field_help(form_type, field_name, business_context, tax_year):
    """Get AI-generated help for a specific tax form field"""
    try:
        prompts = load_prompts()
        if not prompts:
            return None
        
        # Get the tax form assistant prompt
        form_prompt = prompts.get("tax_form_assistant", {})
        if not form_prompt:
            return None
        
        # Format the user message
        user_message = form_prompt["user_template"].format(
            form_type=form_type,
            tax_year=tax_year,
            field_name=field_name,
            business_context=business_context
        )
        
        # Get response from OpenAI
        response = get_openai_response(
            system_message=form_prompt["system"],
            user_message=user_message,
            model="gpt-4o",  # The newest OpenAI model is "gpt-4o" which was released May 13, 2024
            json_response=False
        )
        
        return response
    except Exception as e:
        logging.error(f"Error getting form field help: {str(e)}")
        return "Sorry, we couldn't generate help for this field at the moment. Please try again later."

def get_entity_recommendation(business_info):
    """Get AI-generated entity structure recommendation"""
    try:
        prompts = load_prompts()
        if not prompts:
            return None
        
        # Get the entity optimizer prompt
        entity_prompt = prompts.get("entity_optimizer", {})
        if not entity_prompt:
            return None
        
        # Format the user message
        user_message = entity_prompt["user_template"].format(
            business_type=business_info.get("business_type", ""),
            revenue=business_info.get("revenue", ""),
            employees=business_info.get("employees", ""),
            current_entity=business_info.get("current_entity", ""),
            personal_income=business_info.get("personal_income", ""),
            growth_plans=business_info.get("growth_plans", "")
        )
        
        # Get response from OpenAI
        response = get_openai_response(
            system_message=entity_prompt["system"],
            user_message=user_message,
            model="gpt-4o",  # The newest OpenAI model is "gpt-4o" which was released May 13, 2024
            json_response=True
        )
        
        return response
    except Exception as e:
        logging.error(f"Error getting entity recommendation: {str(e)}")
        return None
