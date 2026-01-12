"""
Dynamic Tax Engine & Context Parser

This module provides AI-powered parsing of natural language expense descriptions
into actionable tax data with IRS categories, Schedule C lines, and complexity detection.
"""

import os
import json
import re
from typing import Dict, List, Optional, Tuple
from decimal import Decimal

# Optional AI integration
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    anthropic = None
    HAS_ANTHROPIC = False


# Schedule C line item mappings
SCHEDULE_C_LINES = {
    'advertising': {'line': 8, 'description': 'Advertising'},
    'car_truck': {'line': 9, 'description': 'Car and truck expenses'},
    'commissions': {'line': 10, 'description': 'Commissions and fees'},
    'contract_labor': {'line': 11, 'description': 'Contract labor'},
    'depletion': {'line': 12, 'description': 'Depletion'},
    'depreciation': {'line': 13, 'description': 'Depreciation and section 179 expense deduction'},
    'employee_benefit': {'line': 14, 'description': 'Employee benefit programs'},
    'insurance': {'line': 15, 'description': 'Insurance (other than health)'},
    'interest_mortgage': {'line': 16, 'description': 'Interest: Mortgage'},
    'interest_other': {'line': 16, 'description': 'Interest: Other'},
    'legal_professional': {'line': 17, 'description': 'Legal and professional services'},
    'office_expense': {'line': 18, 'description': 'Office expense'},
    'pension_profit_sharing': {'line': 19, 'description': 'Pension and profit-sharing plans'},
    'rent_lease_vehicles': {'line': 20, 'description': 'Rent or lease: Vehicles, machinery, and equipment'},
    'rent_lease_property': {'line': 20, 'description': 'Rent or lease: Other business property'},
    'repairs_maintenance': {'line': 21, 'description': 'Repairs and maintenance'},
    'supplies': {'line': 22, 'description': 'Supplies'},
    'taxes_licenses': {'line': 23, 'description': 'Taxes and licenses'},
    'travel': {'line': 24, 'description': 'Travel and meals'},
    'meals': {'line': 24, 'description': 'Meals (50% deductible)'},
    'utilities': {'line': 25, 'description': 'Utilities'},
    'wages': {'line': 26, 'description': 'Wages'},
    'other': {'line': 27, 'description': 'Other expenses'}
}

# Complexity triggers
HIGH_COMPLEXITY_KEYWORDS = [
    'employee', 'employees', 'payroll', 'w-2', 'w2',
    'foreign', 'international', 'overseas', 'abroad',
    'inventory', 'stock', 'merchandise', 'goods for resale',
    'cryptocurrency', 'crypto', 'bitcoin', 'nft',
    'partnership', 'multi-member', 's-corp', 's corp',
    'rental property', 'real estate', 'depreciation schedule'
]

# Startup cost keywords
STARTUP_COST_KEYWORDS = [
    'startup', 'start-up', 'start up', 'initial', 'formation',
    'incorporation', 'llc filing', 'legal fees for formation',
    'organizational costs', 'pre-opening', 'launch'
]

# ========================================
# MULTI-STREAM GIG ECONOMY ENGINE
# ========================================

# Gig platform mappings with keywords, fees, and tax forms
GIG_PLATFORMS = {
    'uber': {
        'name': 'Uber',
        'keywords': ['uber', 'uber eats', 'ubereats'],
        'service_fee_rate': 0.25,  # 25% service fee
        'tax_form': '1099-K',
        'category': 'rideshare',
        'is_driver': True
    },
    'lyft': {
        'name': 'Lyft',
        'keywords': ['lyft'],
        'service_fee_rate': 0.25,
        'tax_form': '1099-K',
        'category': 'rideshare',
        'is_driver': True
    },
    'doordash': {
        'name': 'DoorDash',
        'keywords': ['doordash', 'door dash'],
        'service_fee_rate': 0.20,  # 20% service fee
        'tax_form': '1099-NEC',
        'category': 'delivery',
        'is_driver': True
    },
    'grubhub': {
        'name': 'GrubHub',
        'keywords': ['grubhub', 'grub hub'],
        'service_fee_rate': 0.20,
        'tax_form': '1099-NEC',
        'category': 'delivery',
        'is_driver': True
    },
    'instacart': {
        'name': 'Instacart',
        'keywords': ['instacart', 'insta cart'],
        'service_fee_rate': 0.15,
        'tax_form': '1099-NEC',
        'category': 'delivery',
        'is_driver': True
    },
    'postmates': {
        'name': 'Postmates',
        'keywords': ['postmates', 'post mates'],
        'service_fee_rate': 0.20,
        'tax_form': '1099-NEC',
        'category': 'delivery',
        'is_driver': True
    },
    'amazon_flex': {
        'name': 'Amazon Flex',
        'keywords': ['amazon flex', 'amazonflex'],
        'service_fee_rate': 0.10,
        'tax_form': '1099-NEC',
        'category': 'delivery',
        'is_driver': True
    },
    'upwork': {
        'name': 'Upwork',
        'keywords': ['upwork'],
        'service_fee_rate': 0.10,  # 10% service fee (sliding scale)
        'tax_form': '1099-NEC',
        'category': 'freelance',
        'is_driver': False
    },
    'fiverr': {
        'name': 'Fiverr',
        'keywords': ['fiverr'],
        'service_fee_rate': 0.20,
        'tax_form': '1099-K',
        'category': 'freelance',
        'is_driver': False
    },
    'etsy': {
        'name': 'Etsy',
        'keywords': ['etsy'],
        'service_fee_rate': 0.065,  # 6.5% transaction fee
        'tax_form': '1099-K',
        'category': 'ecommerce',
        'is_driver': False
    },
    'airbnb': {
        'name': 'Airbnb',
        'keywords': ['airbnb', 'air bnb'],
        'service_fee_rate': 0.03,  # 3% host service fee
        'tax_form': '1099-K',
        'category': 'rental',
        'is_driver': False
    },
    'taskrabbit': {
        'name': 'TaskRabbit',
        'keywords': ['taskrabbit', 'task rabbit'],
        'service_fee_rate': 0.15,
        'tax_form': '1099-NEC',
        'category': 'services',
        'is_driver': False
    },
    'rover': {
        'name': 'Rover',
        'keywords': ['rover'],
        'service_fee_rate': 0.20,
        'tax_form': '1099-K',
        'category': 'services',
        'is_driver': False
    }
}

# IRS standard mileage rates (updated annually)
MILEAGE_RATES = {
    2024: 0.67,  # $0.67 per mile
    2025: 0.70,  # $0.70 per mile (projected)
    2026: 0.70   # $0.70 per mile (projected)
}

# Income keywords for detecting revenue vs expenses
INCOME_KEYWORDS = [
    'made', 'earned', 'received', 'income', 'revenue', 'payment', 'paid me',
    'deposited', 'got paid', 'earnings', 'tips', 'collected'
]


class TaxContextParser:
    """AI-powered tax context parser using Anthropic Claude"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the parser with Anthropic API key"""
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        if self.api_key and HAS_ANTHROPIC:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.client = None

    def parse_expense(self, description: str, amount: Optional[float] = None) -> Dict:
        """
        Parse a natural language expense description into structured tax data

        Args:
            description: Natural language description (e.g., "I bought a $3k laptop")
            amount: Optional amount if not in description

        Returns:
            JSON-serializable dict with IRS category, Schedule C line, and metadata
        """
        # Extract amount from description if present
        extracted_amount = self._extract_amount(description) if not amount else amount

        # Use AI to classify if available, otherwise use fallback
        if self.client:
            classification = self._ai_classify(description)
        else:
            classification = self._fallback_classify(description)

        # Determine if this is a startup cost
        is_startup = self._is_startup_cost(description)

        # Get Schedule C line details
        schedule_c_info = SCHEDULE_C_LINES.get(
            classification['category'],
            SCHEDULE_C_LINES['other']
        )

        return {
            'success': True,
            'expense': {
                'description': description,
                'amount': float(extracted_amount) if extracted_amount else None,
                'irs_category': classification['irs_category'],
                'schedule_c_line': schedule_c_info['line'],
                'schedule_c_description': schedule_c_info['description'],
                'category_key': classification['category'],
                'deduction_percentage': classification.get('deduction_percentage', 100),
                'is_startup_cost': is_startup,
                'requires_documentation': classification.get('requires_documentation', True),
                'audit_risk': classification.get('audit_risk', 'low'),
                'irs_guidance': classification.get('irs_guidance', ''),
                'confidence': classification.get('confidence', 0.0)
            }
        }

    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract dollar amounts from text"""
        # Match patterns like $3k, $3,000, $3000, 3k, 3000
        patterns = [
            r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)\s*k',  # $3k or 3k
            r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)',        # $3,000 or $3000
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*dollars' # 3000 dollars
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                amount = float(amount_str)
                # Handle 'k' suffix
                if 'k' in text.lower():
                    amount *= 1000
                return amount

        return None

    def _ai_classify(self, description: str) -> Dict:
        """Use Claude AI to classify the expense"""
        prompt = f"""Analyze this business expense and provide tax classification:

Expense: "{description}"

Provide a JSON response with these fields:
- category: one of {list(SCHEDULE_C_LINES.keys())}
- irs_category: full IRS category name (e.g., "Section 179 Equipment Deduction")
- deduction_percentage: percentage deductible (usually 100, but 50 for meals)
- requires_documentation: true/false
- audit_risk: "low", "medium", or "high"
- irs_guidance: brief explanation of IRS rules
- confidence: 0.0 to 1.0 score

Consider:
- Laptops, computers, software = depreciation/section 179
- Meals = 50% deductible, travel line
- Office supplies = office expense
- Professional services = legal and professional
- Marketing, ads = advertising

Return ONLY valid JSON, no other text."""

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse the AI response
            response_text = message.content[0].text.strip()
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            result = json.loads(response_text)
            return result

        except Exception as e:
            print(f"AI classification error: {e}")
            return self._fallback_classify(description)

    def _fallback_classify(self, description: str) -> Dict:
        """Fallback classification using keyword matching"""
        desc_lower = description.lower()

        # Define keyword patterns
        patterns = {
            'depreciation': ['laptop', 'computer', 'equipment', 'machinery', 'furniture', 'vehicle'],
            'advertising': ['ad', 'marketing', 'promotion', 'google ads', 'facebook ads'],
            'office_expense': ['office supply', 'printer', 'paper', 'pen', 'desk'],
            'legal_professional': ['lawyer', 'attorney', 'accountant', 'cpa', 'consultant'],
            'utilities': ['electric', 'power', 'internet', 'phone', 'water', 'gas'],
            'travel': ['flight', 'hotel', 'airfare', 'lodging', 'conference'],
            'meals': ['meal', 'lunch', 'dinner', 'restaurant', 'food'],
            'supplies': ['supply', 'supplies', 'material'],
            'insurance': ['insurance', 'liability', 'coverage'],
            'rent_lease_property': ['rent', 'lease', 'office space']
        }

        for category, keywords in patterns.items():
            if any(kw in desc_lower for kw in keywords):
                irs_category = self._get_irs_category_name(category)
                return {
                    'category': category,
                    'irs_category': irs_category,
                    'deduction_percentage': 50 if category == 'meals' else 100,
                    'requires_documentation': True,
                    'audit_risk': 'medium' if category == 'meals' else 'low',
                    'irs_guidance': self._get_irs_guidance(category),
                    'confidence': 0.7
                }

        # Default to other expenses
        return {
            'category': 'other',
            'irs_category': 'Other Business Expenses',
            'deduction_percentage': 100,
            'requires_documentation': True,
            'audit_risk': 'low',
            'irs_guidance': 'General business expense - ensure ordinary and necessary',
            'confidence': 0.5
        }

    def _get_irs_category_name(self, category: str) -> str:
        """Get full IRS category name"""
        mapping = {
            'depreciation': 'Section 179 Equipment Deduction',
            'advertising': 'Advertising and Marketing',
            'office_expense': 'Office Expenses and Supplies',
            'legal_professional': 'Legal and Professional Services',
            'utilities': 'Business Utilities',
            'travel': 'Business Travel',
            'meals': 'Business Meals (50% Deductible)',
            'supplies': 'Business Supplies',
            'insurance': 'Business Insurance',
            'rent_lease_property': 'Rent and Lease Payments'
        }
        return mapping.get(category, 'Other Business Expenses')

    def _get_irs_guidance(self, category: str) -> str:
        """Get IRS guidance for category"""
        guidance = {
            'depreciation': 'Equipment over $2,500 may qualify for Section 179 immediate expensing up to $1,220,000 (2024)',
            'meals': 'Business meals are 50% deductible. Must be ordinary and necessary, not lavish or extravagant',
            'advertising': 'Fully deductible if ordinary and necessary for your business',
            'office_expense': 'Supplies and materials used in your business are fully deductible',
            'travel': 'Travel expenses must be ordinary, necessary, and away from your tax home',
            'legal_professional': 'Professional fees for business purposes are fully deductible'
        }
        return guidance.get(category, 'Expense must be ordinary and necessary for your business')

    def _is_startup_cost(self, description: str) -> bool:
        """Detect if this is a startup/organizational cost"""
        desc_lower = description.lower()
        return any(keyword in desc_lower for keyword in STARTUP_COST_KEYWORDS)


class ComplexityScaler:
    """Analyze business complexity based on expense descriptions and profile"""

    @staticmethod
    def assess_complexity(
        expense_descriptions: List[str],
        business_profile: Optional[Dict] = None
    ) -> Dict:
        """
        Assess business complexity based on expenses and profile

        Args:
            expense_descriptions: List of expense descriptions
            business_profile: Optional business profile data

        Returns:
            Complexity assessment with flags and recommendations
        """
        complexity_flags = []
        complexity_score = 0

        # Analyze expense descriptions
        all_text = ' '.join(expense_descriptions).lower()

        for keyword in HIGH_COMPLEXITY_KEYWORDS:
            if keyword in all_text:
                complexity_flags.append({
                    'trigger': keyword,
                    'category': ComplexityScaler._get_complexity_category(keyword),
                    'recommendation': ComplexityScaler._get_recommendation(keyword)
                })
                complexity_score += 10

        # Analyze business profile if provided
        if business_profile:
            if business_profile.get('has_employees'):
                complexity_flags.append({
                    'trigger': 'has_employees',
                    'category': 'Payroll & Employment',
                    'recommendation': 'Enable payroll tax modules and Form 941 preparation'
                })
                complexity_score += 15

            if business_profile.get('has_inventory'):
                complexity_flags.append({
                    'trigger': 'has_inventory',
                    'category': 'Inventory Accounting',
                    'recommendation': 'Enable COGS calculation and inventory valuation'
                })
                complexity_score += 10

            annual_revenue = business_profile.get('annual_revenue', 0)
            if annual_revenue > 250000:
                complexity_flags.append({
                    'trigger': 'high_revenue',
                    'category': 'High Revenue Business',
                    'recommendation': 'Consider quarterly estimated tax payments and S-Corp election'
                })
                complexity_score += 5

        # Determine complexity level
        if complexity_score >= 30:
            level = 'high'
        elif complexity_score >= 15:
            level = 'medium'
        else:
            level = 'low'

        return {
            'complexity_level': level,
            'complexity_score': complexity_score,
            'flags': complexity_flags,
            'requires_advanced_questionnaire': level in ['medium', 'high'],
            'recommended_tier': ComplexityScaler._recommend_tier(level),
            'estimated_forms': ComplexityScaler._estimate_forms(complexity_flags)
        }

    @staticmethod
    def _get_complexity_category(keyword: str) -> str:
        """Get complexity category for keyword"""
        if keyword in ['employee', 'employees', 'payroll', 'w-2', 'w2']:
            return 'Payroll & Employment'
        elif keyword in ['foreign', 'international', 'overseas', 'abroad']:
            return 'International Tax'
        elif keyword in ['inventory', 'stock', 'merchandise', 'goods for resale']:
            return 'Inventory Accounting'
        elif keyword in ['cryptocurrency', 'crypto', 'bitcoin', 'nft']:
            return 'Digital Assets'
        elif keyword in ['partnership', 'multi-member', 's-corp', 's corp']:
            return 'Complex Entity Structure'
        else:
            return 'Other Complexity'

    @staticmethod
    def _get_recommendation(keyword: str) -> str:
        """Get recommendation for complexity trigger"""
        recommendations = {
            'employee': 'Enable Form 941 (Quarterly Payroll Tax), W-2 generation, and unemployment tax tracking',
            'foreign': 'Enable FBAR reporting and Form 8938 for foreign financial assets',
            'inventory': 'Enable inventory tracking, COGS calculation, and method selection (FIFO/LIFO)',
            'cryptocurrency': 'Enable Form 8949 for crypto transactions and basis tracking',
            'partnership': 'Recommend upgrading to Premium tier for partnership/S-Corp support'
        }
        return recommendations.get(keyword, 'Consult with tax professional for complex situations')

    @staticmethod
    def _recommend_tier(complexity_level: str) -> str:
        """Recommend pricing tier based on complexity"""
        if complexity_level == 'high':
            return 'premium'
        elif complexity_level == 'medium':
            return 'guided'
        else:
            return 'self_service'

    @staticmethod
    def _estimate_forms(flags: List[Dict]) -> List[str]:
        """Estimate required tax forms based on complexity flags"""
        forms = ['Schedule C']  # Always need Schedule C for sole proprietors

        flag_triggers = [f['trigger'] for f in flags]

        if 'has_employees' in flag_triggers or any(t in flag_triggers for t in ['employee', 'payroll']):
            forms.extend(['Form 941', 'Form 940', 'W-2', 'W-3'])

        if any(t in flag_triggers for t in ['foreign', 'international']):
            forms.extend(['FBAR', 'Form 8938'])

        if 'cryptocurrency' in flag_triggers:
            forms.append('Form 8949')

        return forms


class StartupCostOptimizer:
    """Optimize deductions for startup businesses with $0 revenue"""

    @staticmethod
    def analyze_startup_costs(expenses: List[Dict], revenue: float = 0) -> Dict:
        """
        Analyze startup costs and provide optimization recommendations

        Args:
            expenses: List of expense dicts with 'amount' and 'is_startup_cost' fields
            revenue: Annual revenue (default 0)

        Returns:
            Startup cost analysis with deduction strategy
        """
        startup_expenses = [e for e in expenses if e.get('is_startup_cost', False)]
        total_startup_costs = sum(e.get('amount', 0) for e in startup_expenses)

        # IRS rules: Up to $5,000 startup costs deductible in year 1
        # Excess amortized over 180 months (15 years)
        immediate_deduction = min(total_startup_costs, 5000)
        amortizable_amount = max(total_startup_costs - 5000, 0)
        monthly_amortization = amortizable_amount / 180 if amortizable_amount > 0 else 0

        # Calculate first year deduction
        # Assume business started mid-year (6 months of amortization)
        first_year_amortization = monthly_amortization * 6
        total_first_year_deduction = immediate_deduction + first_year_amortization

        return {
            'total_startup_costs': float(total_startup_costs),
            'immediate_deduction': float(immediate_deduction),
            'amortizable_amount': float(amortizable_amount),
            'monthly_amortization': float(monthly_amortization),
            'first_year_total_deduction': float(total_first_year_deduction),
            'strategy': StartupCostOptimizer._get_strategy(revenue, total_startup_costs),
            'irs_form': 'Form 4562 (Depreciation and Amortization)',
            'recommendations': StartupCostOptimizer._get_recommendations(
                revenue, total_startup_costs, total_first_year_deduction
            )
        }

    @staticmethod
    def _get_strategy(revenue: float, startup_costs: float) -> str:
        """Get deduction strategy description"""
        if revenue == 0:
            return 'loss-leader'
        elif revenue < startup_costs:
            return 'partial-offset'
        else:
            return 'full-offset'

    @staticmethod
    def _get_recommendations(revenue: float, startup_costs: float, deduction: float) -> List[str]:
        """Get personalized recommendations"""
        recommendations = []

        if revenue == 0:
            recommendations.append(
                f"💡 Your startup costs of ${startup_costs:,.2f} will create a ${deduction:,.2f} "
                "business loss this year, which may offset other income on your tax return."
            )
            recommendations.append(
                "📋 File Schedule C even with $0 revenue to claim your startup deductions."
            )
            recommendations.append(
                "🎯 This loss can reduce your overall tax liability if you have other income (W-2, 1099, etc.)"
            )

        if startup_costs > 5000:
            recommendations.append(
                f"⏰ ${startup_costs - 5000:,.2f} will be amortized over 15 years. "
                "Track this in Form 4562 for future years."
            )

        recommendations.append(
            "📝 Keep detailed records of all startup expenses with dates and receipts for audit protection."
        )

        return recommendations


# Public API functions for easy integration
def parse_expense_string(description: str, amount: Optional[float] = None, api_key: Optional[str] = None) -> Dict:
    """
    Parse a natural language expense description

    Args:
        description: Natural language description
        amount: Optional amount
        api_key: Optional Anthropic API key

    Returns:
        JSON-serializable expense classification
    """
    parser = TaxContextParser(api_key=api_key)
    return parser.parse_expense(description, amount)


def assess_business_complexity(
    expense_descriptions: List[str],
    business_profile: Optional[Dict] = None
) -> Dict:
    """
    Assess business complexity and provide recommendations

    Args:
        expense_descriptions: List of expense descriptions
        business_profile: Optional business profile data

    Returns:
        Complexity assessment with recommendations
    """
    return ComplexityScaler.assess_complexity(expense_descriptions, business_profile)


def optimize_startup_costs(expenses: List[Dict], revenue: float = 0) -> Dict:
    """
    Optimize startup cost deductions for new businesses

    Args:
        expenses: List of expense dicts
        revenue: Annual revenue

    Returns:
        Startup cost optimization analysis
    """
    return StartupCostOptimizer.analyze_startup_costs(expenses, revenue)
