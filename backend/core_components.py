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
import os

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
    def __init__(self, openai_api_key: str = None):
        if openai_api_key:
            openai.api_key = openai_api_key
        self.prompts = self._load_prompts()
        self.entity_specific_prompts = self._load_entity_prompts()
        self.advanced_tax_categories = self._load_tax_categories()
    
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
    
    def _load_entity_prompts(self) -> Dict:
        """Entity-specific tax intelligence prompts"""
        return {
            'sole_proprietorship': {
                'guidance_prompt': """
                You are analyzing a sole proprietorship Schedule C. This entity:
                - Pays income tax + 15.3% self-employment tax
                - Can deduct business expenses on Schedule C
                - Must make quarterly estimated payments if owing >$1000
                - Home office deduction available (simplified or actual method)
                - Business meals 50% deductible in 2023-2024
                
                Based on this data: {form_data}
                Revenue: {revenue}, Expenses: {expenses}
                
                Provide specific advice on:
                1. Missed deductions (be specific with amounts)
                2. Quarterly payment strategy 
                3. Tax optimization opportunities
                4. Audit risk assessment
                
                Calculate exact dollar savings for each recommendation.
                """,
                'risk_factors': ['hobby_loss_rule', 'excessive_home_office', 'round_numbers'],
                'common_deductions': ['home_office', 'business_meals', 'equipment', 'professional_development']
            },
            's_corp': {
                'guidance_prompt': """
                You are analyzing an S-Corp return. This entity:
                - Requires reasonable salary subject to payroll taxes
                - Distributions above salary avoid SE tax
                - Pass-through taxation to shareholders
                - Basis limitations on losses and distributions
                
                Based on this data: {form_data}
                Revenue: {revenue}, Officer Salary: {salary}
                
                Analyze:
                1. Salary adequacy (IRS reasonable compensation test)
                2. Salary vs distribution optimization
                3. Basis tracking requirements
                4. Tax savings vs sole prop/LLC
                
                Provide dollar amounts for salary adjustments and tax impact.
                """,
                'risk_factors': ['unreasonable_compensation', 'basis_tracking', 'built_in_gains'],
                'optimization_strategies': ['salary_optimization', 'distribution_timing', 'fringe_benefits']
            },
            'llc': {
                'guidance_prompt': """
                You are analyzing an LLC tax return. This entity:
                - Default single-member LLC = sole prop tax treatment
                - Multi-member LLC = partnership taxation
                - Can elect S-Corp or C-Corp taxation
                - Self-employment tax applies unless S-Corp election
                
                Based on this data: {form_data}
                Revenue: {revenue}, Members: {members}
                
                Analyze:
                1. Current tax election optimization
                2. SE tax minimization strategies
                3. Entity election recommendations
                4. Member allocation considerations
                
                Calculate tax impact of different elections.
                """,
                'risk_factors': ['se_tax_exposure', 'allocation_disputes', 'basis_tracking'],
                'optimization_strategies': ['s_corp_election', 'guaranteed_payments', 'distributions']
            }
        }
    
    def _load_tax_categories(self) -> Dict:
        """Advanced tax categorization with current tax law"""
        return {
            'business_meals': {
                'deductible_percentage': 50,  # 100% for 2021-2022, 50% for 2023+
                'schedule_c_line': '24b',
                'documentation': 'receipt + business purpose + attendees',
                'audit_risk': 'medium',
                'irs_guidance': 'Must be ordinary and necessary, not lavish',
                'common_errors': ['personal meals', 'entertainment disguised as meals']
            },
            'home_office': {
                'calculation_methods': {
                    'simplified': '$5 per sq ft, max 300 sq ft = $1,500',
                    'actual': 'percentage of home expenses'
                },
                'deductible_percentage': 100,
                'audit_risk': 'high',
                'requirements': ['exclusive business use', 'regular business use'],
                'red_flags': ['too high percentage', 'inconsistent use']
            },
            'equipment': {
                'section_179_eligible': True,
                'section_179_limit_2024': 1160000,
                'bonus_depreciation': '80% in 2023, 60% in 2024',
                'regular_depreciation': 'MACRS over useful life',
                'strategy': 'Compare Section 179 vs bonus depreciation vs regular',
                'deductible_percentage': 100
            },
            'software': {
                'deductible_percentage': 100,
                'schedule_c_line': '18',
                'audit_risk': 'low',
                'special_rules': 'Software >$2,500 may need to be depreciated',
                'common_deductions': ['SaaS subscriptions', 'business software licenses']
            },
            'travel': {
                'deductible_percentage': 100,
                'requirements': ['business purpose', 'overnight away from home'],
                'mileage_rate_2024': 0.67,
                'audit_risk': 'medium',
                'red_flags': ['excessive travel', 'luxury accommodations']
            }
        }
    
    def get_schedule_c_guidance(self, user_profile: Dict, form_data: Dict) -> Dict:
        """Generate AI guidance for Schedule C completion"""
        # Mock response for demo (replace with actual OpenAI when API key is configured)
        return {
            "guidance": {
                "next_steps": ["Complete business income section", "Review deduction categories"],
                "recommendations": ["Consider home office deduction", "Track business meals"],
                "warnings": ["Ensure business/personal separation"],
                "estimated_savings": 2400
            },
            "completion_tips": {
                "business_income": "Report all business income received",
                "business_expenses": "Only deduct legitimate business expenses"
            },
            "confidence": 87
        }
    
    def find_deductions(self, business_type: str, industry: str, expenses: List[Dict]) -> Dict:
        """AI-powered deduction analysis"""
        # Mock response for demo
        total_deductions = sum(exp.get('amount', 0) for exp in expenses)
        return {
            "total_deductible": total_deductions * 0.85,
            "categories": {
                "office_expenses": {"amount": total_deductions * 0.3, "confidence": 0.9},
                "travel": {"amount": total_deductions * 0.2, "confidence": 0.8},
                "software": {"amount": total_deductions * 0.35, "confidence": 0.95}
            },
            "missed_opportunities": ["Home office deduction", "Business meals"],
            "audit_risk": "low"
        }
    
    def categorize_expense(self, description: str, amount: float, business_type: str) -> Dict:
        """Enhanced AI categorization with tax law knowledge"""
        description_lower = description.lower()
        
        # Enhanced keyword matching with tax categories
        category_mappings = {
            'business_meals': ['restaurant', 'lunch', 'dinner', 'meal', 'coffee', 'food'],
            'home_office': ['home office', 'utilities', 'internet', 'phone'],
            'equipment': ['computer', 'laptop', 'printer', 'equipment', 'machinery'],
            'software': ['software', 'subscription', 'saas', 'license', 'app'],
            'travel': ['travel', 'hotel', 'airline', 'flight', 'uber', 'gas', 'mileage'],
            'office_supplies': ['office', 'supply', 'staples', 'paper', 'pens'],
            'professional_development': ['course', 'training', 'conference', 'education', 'seminar']
        }
        
        detected_category = 'general_business'
        confidence = 0.75
        
        for category, keywords in category_mappings.items():
            if any(keyword in description_lower for keyword in keywords):
                detected_category = category
                confidence = 0.90
                break
        
        # Get tax treatment information
        tax_treatment = self.advanced_tax_categories.get(detected_category, {
            'deductible_percentage': 100,
            'audit_risk': 'low',
            'documentation': 'receipt'
        })
        
        # Calculate actual tax savings
        deductible_amount = amount * (tax_treatment.get('deductible_percentage', 100) / 100)
        tax_savings = self.calculate_tax_savings_for_expense(deductible_amount, business_type)
        
        return {
            "category": detected_category.replace('_', ' ').title(),
            "deductible_percentage": tax_treatment.get('deductible_percentage', 100),
            "deductible_amount": deductible_amount,
            "tax_savings_estimate": tax_savings,
            "audit_risk": tax_treatment.get('audit_risk', 'low'),
            "documentation_needed": tax_treatment.get('documentation', 'receipt'),
            "schedule_c_line": tax_treatment.get('schedule_c_line', '18'),
            "irs_guidance": tax_treatment.get('irs_guidance', ''),
            "confidence": confidence,
            "notes": f"Categorized as {detected_category} with {confidence*100:.0f}% confidence"
        }
    
    def calculate_tax_savings_for_expense(self, deductible_amount: float, business_type: str) -> float:
        """Calculate actual tax savings using current tax law"""
        # 2024 tax assumptions (would be more sophisticated in production)
        tax_rates = {
            'sole_proprietorship': {
                'income_tax': 0.22,  # Marginal rate assumption
                'self_employment': 0.153,
                'state': 0.05  # Average state rate
            },
            's_corp': {
                'income_tax': 0.22,
                'self_employment': 0,  # No SE tax on distributions
                'state': 0.05
            },
            'llc': {
                'income_tax': 0.22,
                'self_employment': 0.153,
                'state': 0.05
            }
        }
        
        rates = tax_rates.get(business_type, tax_rates['sole_proprietorship'])
        
        # Calculate total tax savings
        federal_savings = deductible_amount * rates['income_tax']
        se_savings = deductible_amount * rates['self_employment'] * 0.9235  # SE tax calculation
        state_savings = deductible_amount * rates['state']
        
        return federal_savings + se_savings + state_savings
    
    def get_entity_specific_guidance(self, entity_type: str, form_data: Dict, user_profile: Dict) -> Dict:
        """Get entity-specific tax guidance"""
        entity_config = self.entity_specific_prompts.get(entity_type, {})
        
        if not entity_config:
            return {"error": f"Entity type {entity_type} not supported"}
        
        # Extract key financial data
        revenue = form_data.get('income', {}).get('gross_receipts', 0)
        expenses = sum(form_data.get('expenses', {}).values()) if form_data.get('expenses') else 0
        
        # Generate entity-specific insights
        insights = {
            'entity_type': entity_type,
            'revenue': revenue,
            'expenses': expenses,
            'net_profit': revenue - expenses,
            'risk_factors': entity_config.get('risk_factors', []),
            'optimization_strategies': entity_config.get('optimization_strategies', []),
            'recommended_deductions': entity_config.get('common_deductions', [])
        }
        
        # Calculate specific recommendations based on entity type
        if entity_type == 'sole_proprietorship':
            insights.update(self._sole_prop_analysis(revenue, expenses))
        elif entity_type == 's_corp':
            insights.update(self._s_corp_analysis(revenue, expenses, form_data))
        
        return insights
    
    def _sole_prop_analysis(self, revenue: float, expenses: float) -> Dict:
        """Specific analysis for sole proprietorships"""
        net_profit = revenue - expenses
        se_tax = net_profit * 0.153 * 0.9235  # SE tax calculation
        
        return {
            'self_employment_tax': se_tax,
            'quarterly_payment_required': net_profit > 1000,
            'estimated_quarterly_payment': (net_profit * 0.25) / 4,  # Rough estimate
            'home_office_opportunity': min(1500, 300 * 5),  # Simplified method
            'retirement_contribution_limit': min(61000, net_profit * 0.25)  # SEP-IRA limit
        }
    
    def _s_corp_analysis(self, revenue: float, expenses: float, form_data: Dict) -> Dict:
        """Specific analysis for S-Corps"""
        net_profit = revenue - expenses
        officer_salary = form_data.get('officer_compensation', 0)
        
        # Reasonable compensation analysis
        industry_salary_benchmark = net_profit * 0.4  # Rough benchmark
        
        return {
            'officer_salary': officer_salary,
            'recommended_salary_range': {
                'minimum': min(net_profit * 0.3, 60000),
                'maximum': min(net_profit * 0.6, 160000)
            },
            'salary_optimization_savings': max(0, (officer_salary - industry_salary_benchmark) * 0.153),
            'distribution_opportunity': max(0, net_profit - industry_salary_benchmark),
            'payroll_tax_exposure': officer_salary * 0.153
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
                            "office_expenses": {"type": "currency", "required": False, "label": "Office expenses"},
                            "travel": {"type": "currency", "required": False, "label": "Travel"},
                            "utilities": {"type": "currency", "required": False, "label": "Utilities"}
                        }
                    }
                }
            }
        }
    
    def create_form(self, form_type: str, user_id: int) -> Dict:
        """Create a new form instance"""
        template = self.form_templates.get(form_type)
        if not template:
            raise ValueError(f"Form type {form_type} not supported")
        
        # Initialize empty form data
        form_data = {}
        for section_name, section in template["sections"].items():
            form_data[section_name] = {}
            for field_name in section["fields"].keys():
                form_data[section_name][field_name] = ""
        
        return {
            "template": template,
            "data": form_data,
            "completion_percentage": 0
        }
    
    def _calculate_completion(self, form_data: Dict, template: Dict) -> float:
        """Calculate form completion percentage"""
        total_required = 0
        completed = 0
        
        for section_name, section in template["sections"].items():
            for field_name, field_config in section["fields"].items():
                if field_config.get("required", False):
                    total_required += 1
                    value = form_data.get(section_name, {}).get(field_name, "")
                    if value and str(value).strip():
                        completed += 1
        
        return round((completed / total_required) * 100) if total_required > 0 else 0

# =============================================================================
# SUBSCRIPTION MANAGER - Stripe integration
# =============================================================================

class SubscriptionManager:
    def __init__(self, stripe_secret_key: str = None):
        if stripe_secret_key:
            stripe.api_key = stripe_secret_key
        
        self.pricing_tiers = {
            "trial": {"price": 0, "features": ["basic_forms", "limited_ai"]},
            "guided": {"price": 19700, "features": ["full_forms", "ai_guidance", "export"]},  # $197.00
            "premium": {"price": 49700, "features": ["everything", "priority_support", "audit_protection"]}  # $497.00
        }
    
    def create_subscription(self, user_email: str, tier: str) -> Dict:
        """Create Stripe subscription"""
        try:
            if not stripe.api_key:
                # Mock response for demo
                return {
                    "subscription_id": f"sub_mock_{tier}",
                    "status": "active",
                    "tier": tier,
                    "mock": True
                }
            
            # Real Stripe integration would go here
            customer = stripe.Customer.create(email=user_email)
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{"price": self.pricing_tiers[tier]["price_id"]}]
            )
            
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "customer_id": customer.id
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def check_upgrade_trigger(self, current_tier: str, estimated_savings: float, completion_percentage: float) -> Dict:
        """Check if user should see upgrade prompt"""
        if current_tier == "premium":
            return {"trigger": None}
        
        triggers = []
        
        # Savings-based trigger
        if estimated_savings > 1000 and current_tier == "trial":
            triggers.append({
                "type": "savings",
                "message": f"You've found ${estimated_savings:,.0f} in potential savings! Upgrade to unlock advanced strategies.",
                "cta": "Upgrade to Guided - $197",
                "suggested_tier": "guided",
                "urgency": "high"
            })
        
        # Completion-based trigger
        if completion_percentage > 50 and current_tier == "trial":
            triggers.append({
                "type": "completion",
                "message": f"You're {completion_percentage}% complete! Upgrade for AI-guided completion and export.",
                "cta": "Upgrade to Guided - $197",
                "suggested_tier": "guided",
                "urgency": "medium"
            })
        
        return {"trigger": triggers[0] if triggers else None}