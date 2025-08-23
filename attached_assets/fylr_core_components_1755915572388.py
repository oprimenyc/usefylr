# .fylr Core Development Components
# Heavy-lifting code for rapid completion

from flask import Flask, request, jsonify, session
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import openai
import json
from datetime import datetime
from typing import Dict, List, Optional
import stripe
from werkzeug.security import generate_password_hash, check_password_hash

# =============================================================================
# DATABASE MODELS - Complete tax form and user system
# =============================================================================

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    subscription_tier = Column(String(50), default='trial')  # trial, guided, premium
    stripe_customer_id = Column(String(255))
    business_profile = Column(JSON)  # Store entity type, industry, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
class TaxForm(Base):
    __tablename__ = 'tax_forms'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    form_type = Column(String(50), nullable=False)  # schedule_c, schedule_se, 1065, etc.
    form_data = Column(JSON, nullable=False)  # All form field data
    completion_percentage = Column(Float, default=0.0)
    estimated_savings = Column(Float, default=0.0)
    ai_recommendations = Column(JSON)  # AI-generated suggestions
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
class SmartLedgerEntry(Base):
    __tablename__ = 'smart_ledger_entries'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String(500), nullable=False)
    category = Column(String(100))  # AI-suggested category
    tax_deductible = Column(Boolean, default=False)
    ai_confidence = Column(Float, default=0.0)  # How confident AI is in categorization
    receipt_url = Column(String(500))
    date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# =============================================================================
# AI TAX ASSISTANT - Core intelligence engine
# =============================================================================

class AITaxAssistant:
    def __init__(self, openai_api_key: str):
        openai.api_key = openai_api_key
        self.prompts = self._load_prompts()
    
    def _load_prompts(self) -> Dict:
        """Load AI prompts for different tax scenarios"""
        return {
            "schedule_c_guidance": """
            You are an expert tax advisor specializing in small business taxes. 
            Analyze the user's business information and provide specific guidance for Schedule C.
            
            User Profile: {user_profile}
            Current Form Data: {form_data}
            
            Provide:
            1. Line-by-line guidance for incomplete fields
            2. Deduction opportunities they might be missing
            3. Risk assessment for audit flags
            4. Estimated tax savings
            
            Format as JSON with clear, actionable advice.
            """,
            
            "deduction_finder": """
            You are a tax deduction specialist. Analyze the business expenses and identify all possible deductions.
            
            Business Type: {business_type}
            Industry: {industry}
            Expenses: {expenses}
            
            For each expense, determine:
            1. Deductible amount (percentage if partial)
            2. Tax form line item
            3. IRS code reference
            4. Audit risk level (low/medium/high)
            
            Return as structured JSON.
            """,
            
            "entity_optimization": """
            You are a business structure advisor. Analyze if the current entity type is optimal.
            
            Current Entity: {current_entity}
            Annual Revenue: {revenue}
            Business Expenses: {expenses}
            Owner Details: {owner_details}
            
            Provide:
            1. Tax efficiency analysis of current structure
            2. Alternative entity recommendations
            3. Projected tax savings/costs of switching
            4. Implementation complexity
            
            Be specific with dollar amounts and percentages.
            """
        }
    
    def get_schedule_c_guidance(self, user_profile: Dict, form_data: Dict) -> Dict:
        """Generate AI guidance for Schedule C completion"""
        prompt = self.prompts["schedule_c_guidance"].format(
            user_profile=json.dumps(user_profile),
            form_data=json.dumps(form_data)
        )
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return {"error": "Failed to parse AI response", "raw": response.choices[0].message.content}
    
    def find_deductions(self, business_type: str, industry: str, expenses: List[Dict]) -> Dict:
        """AI-powered deduction analysis"""
        prompt = self.prompts["deduction_finder"].format(
            business_type=business_type,
            industry=industry,
            expenses=json.dumps(expenses)
        )
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1500
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return {"error": "Failed to parse deduction analysis"}
    
    def categorize_expense(self, description: str, amount: float, business_type: str) -> Dict:
        """AI categorization for Smart Ledger entries"""
        prompt = f"""
        Categorize this business expense for tax purposes:
        
        Description: {description}
        Amount: ${amount}
        Business Type: {business_type}
        
        Return JSON with:
        - category: IRS tax category
        - deductible_percentage: 0-100
        - tax_form_line: specific line item
        - confidence: 0-1 confidence score
        - notes: brief explanation
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=300
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return {
                "category": "Other Business Expenses",
                "deductible_percentage": 100,
                "confidence": 0.5,
                "notes": "Manual review recommended"
            }

# =============================================================================
# SMART LEDGER - Monthly expense tracking with AI
# =============================================================================

class SmartLedger:
    def __init__(self, db_session, ai_assistant: AITaxAssistant):
        self.db = db_session
        self.ai = ai_assistant
    
    def add_expense(self, user_id: int, amount: float, description: str, date: datetime, 
                   business_type: str = "sole_proprietorship") -> Dict:
        """Add expense with AI categorization"""
        
        # Get AI categorization
        ai_analysis = self.ai.categorize_expense(description, amount, business_type)
        
        # Create ledger entry
        entry = SmartLedgerEntry(
            user_id=user_id,
            amount=amount,
            description=description,
            category=ai_analysis.get('category'),
            tax_deductible=ai_analysis.get('deductible_percentage', 0) > 0,
            ai_confidence=ai_analysis.get('confidence', 0.5),
            date=date
        )
        
        self.db.add(entry)
        self.db.commit()
        
        return {
            "entry_id": entry.id,
            "ai_analysis": ai_analysis,
            "tax_savings_estimate": self._calculate_tax_savings(amount, ai_analysis.get('deductible_percentage', 0))
        }
    
    def _calculate_tax_savings(self, amount: float, deductible_percentage: float) -> float:
        """Estimate tax savings from deduction"""
        deductible_amount = amount * (deductible_percentage / 100)
        # Assume combined tax rate of 35% (federal + state + self-employment)
        return deductible_amount * 0.35
    
    def get_tax_readiness_score(self, user_id: int) -> Dict:
        """Calculate how tax-ready the user's records are"""
        entries = self.db.query(SmartLedgerEntry).filter_by(user_id=user_id).all()
        
        if not entries:
            return {"score": 0, "message": "No expenses tracked yet"}
        
        total_entries = len(entries)
        categorized_entries = len([e for e in entries if e.category and e.ai_confidence > 0.7])
        entries_with_receipts = len([e for e in entries if e.receipt_url])
        
        # Scoring algorithm
        categorization_score = (categorized_entries / total_entries) * 40
        receipt_score = (entries_with_receipts / total_entries) * 30
        volume_score = min(total_entries / 50, 1) * 30  # More entries = better tracking
        
        total_score = categorization_score + receipt_score + volume_score
        
        return {
            "score": round(total_score, 1),
            "total_entries": total_entries,
            "categorized_entries": categorized_entries,
            "entries_with_receipts": entries_with_receipts,
            "recommendations": self._get_improvement_recommendations(total_score)
        }
    
    def _get_improvement_recommendations(self, score: float) -> List[str]:
        """Suggest improvements based on tax readiness score"""
        recommendations = []
        
        if score < 30:
            recommendations.extend([
                "Start tracking expenses regularly",
                "Upload receipts for major purchases",
                "Review AI categorizations monthly"
            ])
        elif score < 60:
            recommendations.extend([
                "Upload missing receipts",
                "Review and confirm AI categorizations",
                "Track business mileage"
            ])
        elif score < 80:
            recommendations.extend([
                "Ensure all receipts are uploaded",
                "Review quarterly for missed deductions"
            ])
        else:
            recommendations.append("Great job! Your records are tax-ready")
        
        return recommendations

# =============================================================================
# FORM GENERATOR - Dynamic tax form creation
# =============================================================================

class TaxFormGenerator:
    def __init__(self):
        self.form_templates = self._load_form_templates()
    
    def _load_form_templates(self) -> Dict:
        """Load form templates with validation rules"""
        return {
            "schedule_c": {
                "form_name": "Schedule C - Profit or Loss From Business",
                "sections": {
                    "business_info": {
                        "title": "Business Information",
                        "fields": {
                            "business_name": {"type": "text", "required": True, "label": "Principal business or profession"},
                            "business_code": {"type": "number", "required": True, "label": "Business code"},
                            "ein": {"type": "ein", "required": False, "label": "Employer ID number"},
                            "accounting_method": {"type": "select", "required": True, 
                                                "options": ["Cash", "Accrual"], "label": "Accounting method"}
                        }
                    },
                    "income": {
                        "title": "Income",
                        "fields": {
                            "gross_receipts": {"type": "currency", "required": True, "label": "Gross receipts or sales"},
                            "returns_allowances": {"type": "currency", "required": False, "label": "Returns and allowances"},
                            "other_income": {"type": "currency", "required": False, "label": "Other income"}
                        }
                    },
                    "expenses": {
                        "title": "Expenses",
                        "fields": {
                            "advertising": {"type": "currency", "required": False, "label": "Advertising"},
                            "car_truck": {"type": "currency", "required": False, "label": "Car and truck expenses"},
                            "commissions": {"type": "currency", "required": False, "label": "Commissions and fees"},
                            "contract_labor": {"type": "currency", "required": False, "label": "Contract labor"},
                            "depletion": {"type": "currency", "required": False, "label": "Depletion"},
                            "depreciation": {"type": "currency", "required": False, "label": "Depreciation"},
                            "employee_benefits": {"type": "currency", "required": False, "label": "Employee benefit programs"},
                            "insurance": {"type": "currency", "required": False, "label": "Insurance (other than health)"},
                            "interest_mortgage": {"type": "currency", "required": False, "label": "Mortgage interest"},
                            "interest_other": {"type": "currency", "required": False, "label": "Other interest"},
                            "legal_professional": {"type": "currency", "required": False, "label": "Legal and professional services"},
                            "office_expense": {"type": "currency", "required": False, "label": "Office expense"},
                            "pension_plans": {"type": "currency", "required": False, "label": "Pension and profit-sharing plans"},
                            "rent_lease_vehicles": {"type": "currency", "required": False, "label": "Rent or lease (vehicles)"},
                            "rent_lease_other": {"type": "currency", "required": False, "label": "Rent or lease (other)"},
                            "repairs": {"type": "currency", "required": False, "label": "Repairs and maintenance"},
                            "supplies": {"type": "currency", "required": False, "label": "Supplies"},
                            "taxes_licenses": {"type": "currency", "required": False, "label": "Taxes and licenses"},
                            "travel": {"type": "currency", "required": False, "label": "Travel"},
                            "meals": {"type": "currency", "required": False, "label": "Meals"},
                            "utilities": {"type": "currency", "required": False, "label": "Utilities"},
                            "wages": {"type": "currency", "required": False, "label": "Wages"},
                            "other_expenses": {"type": "currency", "required": False, "label": "Other expenses"}
                        }
                    }
                }
            },
            
            "schedule_se": {
                "form_name": "Schedule SE - Self-Employment Tax",
                "sections": {
                    "self_employment": {
                        "title": "Self-Employment Tax Calculation",
                        "fields": {
                            "net_profit_loss": {"type": "currency", "required": True, "label": "Net profit (or loss) from Schedule C"},
                            "church_employee": {"type": "boolean", "required": False, "label": "Church employee income"},
                            "other_se_income": {"type": "currency", "required": False, "label": "Other self-employment income"}
                        }
                    }
                }
            }
        }
    
    def create_form(self, form_type: str, user_id: int, prefill_data: Optional[Dict] = None) -> Dict:
        """Create a new tax form instance"""
        if form_type not in self.form_templates:
            raise ValueError(f"Unknown form type: {form_type}")
        
        template = self.form_templates[form_type]
        form_data = {}
        
        # Initialize form with empty values or prefill data
        for section_name, section in template["sections"].items():
            form_data[section_name] = {}
            for field_name, field_config in section["fields"].items():
                if prefill_data and section_name in prefill_data and field_name in prefill_data[section_name]:
                    form_data[section_name][field_name] = prefill_data[section_name][field_name]
                else:
                    form_data[section_name][field_name] = self._get_default_value(field_config["type"])
        
        return {
            "form_type": form_type,
            "template": template,
            "data": form_data,
            "completion_percentage": self._calculate_completion(form_data, template)
        }
    
    def _get_default_value(self, field_type: str):
        """Get default value based on field type"""
        defaults = {
            "text": "",
            "number": 0,
            "currency": 0.00,
            "boolean": False,
            "select": "",
            "ein": "",
            "ssn": "",
            "percentage": 0.0
        }
        return defaults.get(field_type, "")
    
    def _calculate_completion(self, form_data: Dict, template: Dict) -> float:
        """Calculate what percentage of required fields are completed"""
        total_required = 0
        completed_required = 0
        
        for section_name, section in template["sections"].items():
            for field_name, field_config in section["fields"].items():
                if field_config.get("required", False):
                    total_required += 1
                    field_value = form_data.get(section_name, {}).get(field_name)
                    if field_value and str(field_value).strip():
                        completed_required += 1
        
        return (completed_required / total_required * 100) if total_required > 0 else 0

# =============================================================================
# SUBSCRIPTION MANAGER - Handle pricing tiers and features
# =============================================================================

class SubscriptionManager:
    def __init__(self, stripe_api_key: str):
        stripe.api_key = stripe_api_key
        self.tiers = {
            "trial": {
                "price": 0,
                "features": ["ai_preview", "form_preview", "strategy_preview"],
                "export_enabled": False,
                "form_limit": 1
            },
            "guided": {
                "price": 19700,  # $197.00 in cents
                "features": ["ai_full", "form_export", "strategy_download", "smart_ledger_basic"],
                "export_enabled": True,
                "form_limit": 10
            },
            "premium": {
                "price": 49700,  # $497.00 in cents
                "features": ["ai_full", "form_export", "strategy_download", "smart_ledger_full", 
                           "audit_protection", "expert_review", "complex_entities"],
                "export_enabled": True,
                "form_limit": -1  # unlimited
            }
        }
    
    def check_feature_access(self, user_tier: str, feature: str) -> bool:
        """Check if user's tier has access to specific feature"""
        return feature in self.tiers.get(user_tier, {}).get("features", [])
    
    def get_upgrade_trigger(self, user_tier: str, estimated_savings: float, completion_percentage: float) -> Optional[Dict]:
        """Generate upgrade prompts based on user activity"""
        
        if user_tier == "trial":
            if estimated_savings > 500:
                return {
                    "message": f"You've uncovered ${estimated_savings:,.0f} in potential savings — ready to lock it in?",
                    "cta": "Upgrade to Guided ($197/year)",
                    "urgency": "high"
                }
            elif completion_percentage > 80:
                return {
                    "message": f"Your return is {completion_percentage:.0f}% complete. Let's finalize and export it!",
                    "cta": "Upgrade to Export",
                    "urgency": "medium"
                }
        
        elif user_tier == "guided" and estimated_savings > 2000:
            return {
                "message": f"With ${estimated_savings:,.0f} in savings, Premium features could optimize even more.",
                "cta": "Upgrade to Premium ($497/year)",
                "urgency": "low"
            }
        
        return None
    
    def create_subscription(self, customer_email: str, tier: str) -> Dict:
        """Create Stripe subscription"""
        try:
            # Create customer
            customer = stripe.Customer.create(email=customer_email)
            
            # Create subscription
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{"price": f"price_{tier}"}],  # You'll need to create these in Stripe
            )
            
            return {
                "success": True,
                "customer_id": customer.id,
                "subscription_id": subscription.id
            }
        except stripe.error.StripeError as e:
            return {"success": False, "error": str(e)}

# =============================================================================
# USAGE EXAMPLE - Putting it all together
# =============================================================================

def example_usage():
    """Example of how to use these components together"""
    
    # Initialize components
    ai_assistant = AITaxAssistant("your-openai-api-key")
    smart_ledger = SmartLedger(db_session, ai_assistant)
    form_generator = TaxFormGenerator()
    subscription_manager = SubscriptionManager("your-stripe-api-key")
    
    # Example: New user creates Schedule C form
    user_profile = {
        "entity_type": "sole_proprietorship",
        "industry": "consulting",
        "annual_revenue": 75000
    }
    
    # Create form
    schedule_c = form_generator.create_form("schedule_c", user_id=1)
    
    # Get AI guidance
    ai_guidance = ai_assistant.get_schedule_c_guidance(user_profile, schedule_c["data"])
    
    # Add smart ledger expense
    expense_result = smart_ledger.add_expense(
        user_id=1,
        amount=500.00,
        description="MacBook Pro for business",
        date=datetime.now(),
        business_type="consulting"
    )
    
    # Check tax readiness
    readiness_score = smart_ledger.get_tax_readiness_score(user_id=1)
    
    # Check for upgrade triggers
    upgrade_prompt = subscription_manager.get_upgrade_trigger(
        user_tier="trial",
        estimated_savings=1200.00,
        completion_percentage=85.0
    )
    
    print("AI Guidance:", ai_guidance)
    print("Expense Analysis:", expense_result)
    print("Tax Readiness:", readiness_score)
    print("Upgrade Prompt:", upgrade_prompt)

if __name__ == "__main__":
    example_usage()