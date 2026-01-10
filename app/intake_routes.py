"""
Intake API Routes - Dynamic Tax Engine Endpoints

Provides REST API endpoints for the tax context parser and complexity analyzer.
"""

from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from app.modules.intake import (
    parse_expense_string,
    assess_business_complexity,
    optimize_startup_costs
)

# Create blueprint
intake_bp = Blueprint('intake', __name__, url_prefix='/api/intake')


@intake_bp.route('/parse-expense', methods=['POST'])
def parse_expense():
    """
    Parse a natural language expense description into structured tax data

    Request JSON:
        {
            "description": "I bought a $3k laptop for my business",
            "amount": 3000  // optional if in description
        }

    Response JSON:
        {
            "success": true,
            "expense": {
                "description": "I bought a $3k laptop for my business",
                "amount": 3000.0,
                "irs_category": "Section 179 Equipment Deduction",
                "schedule_c_line": 13,
                "schedule_c_description": "Depreciation and section 179 expense deduction",
                "category_key": "depreciation",
                "deduction_percentage": 100,
                "is_startup_cost": false,
                "requires_documentation": true,
                "audit_risk": "low",
                "irs_guidance": "Equipment over $2,500 may qualify...",
                "confidence": 0.95
            }
        }
    """
    try:
        data = request.get_json()

        if not data or 'description' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: description'
            }), 400

        description = data.get('description')
        amount = data.get('amount')

        # Parse the expense
        result = parse_expense_string(description, amount)

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@intake_bp.route('/assess-complexity', methods=['POST'])
def assess_complexity():
    """
    Assess business complexity based on expenses and profile

    Request JSON:
        {
            "expense_descriptions": [
                "Hired 3 employees this year",
                "Bought inventory from China",
                "Paid for office rent"
            ],
            "business_profile": {
                "has_employees": true,
                "has_inventory": true,
                "annual_revenue": 250000
            }
        }

    Response JSON:
        {
            "complexity_level": "high",
            "complexity_score": 35,
            "flags": [
                {
                    "trigger": "employee",
                    "category": "Payroll & Employment",
                    "recommendation": "Enable Form 941..."
                }
            ],
            "requires_advanced_questionnaire": true,
            "recommended_tier": "premium",
            "estimated_forms": ["Schedule C", "Form 941", "Form 940", "W-2"]
        }
    """
    try:
        data = request.get_json()

        expense_descriptions = data.get('expense_descriptions', [])
        business_profile = data.get('business_profile')

        # Assess complexity
        result = assess_business_complexity(expense_descriptions, business_profile)

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@intake_bp.route('/optimize-startup', methods=['POST'])
def optimize_startup():
    """
    Optimize startup cost deductions for businesses with $0 revenue

    Request JSON:
        {
            "expenses": [
                {
                    "description": "LLC formation fees",
                    "amount": 800,
                    "is_startup_cost": true
                },
                {
                    "description": "Initial marketing campaign",
                    "amount": 3500,
                    "is_startup_cost": true
                }
            ],
            "revenue": 0
        }

    Response JSON:
        {
            "total_startup_costs": 4300.0,
            "immediate_deduction": 4300.0,
            "amortizable_amount": 0.0,
            "monthly_amortization": 0.0,
            "first_year_total_deduction": 4300.0,
            "strategy": "loss-leader",
            "irs_form": "Form 4562 (Depreciation and Amortization)",
            "recommendations": [
                "💡 Your startup costs of $4,300 will create...",
                "📋 File Schedule C even with $0 revenue..."
            ]
        }
    """
    try:
        data = request.get_json()

        expenses = data.get('expenses', [])
        revenue = data.get('revenue', 0)

        # Optimize startup costs
        result = optimize_startup_costs(expenses, revenue)

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@intake_bp.route('/batch-parse', methods=['POST'])
@login_required
def batch_parse():
    """
    Parse multiple expenses at once (authenticated users only)

    Request JSON:
        {
            "expenses": [
                {"description": "Bought laptop $2500"},
                {"description": "Office rent $1200/month"},
                {"description": "Hired accountant $500"}
            ]
        }

    Response JSON:
        {
            "success": true,
            "parsed_expenses": [...],
            "summary": {
                "total_count": 3,
                "total_amount": 4200.0,
                "by_category": {...}
            }
        }
    """
    try:
        data = request.get_json()
        expenses = data.get('expenses', [])

        if not expenses:
            return jsonify({
                'success': False,
                'error': 'No expenses provided'
            }), 400

        # Parse all expenses
        parsed = []
        total_amount = 0
        by_category = {}

        for exp in expenses:
            result = parse_expense_string(exp.get('description'))
            if result.get('success'):
                expense_data = result['expense']
                parsed.append(expense_data)

                # Update totals
                amount = expense_data.get('amount', 0) or 0
                total_amount += amount

                category = expense_data.get('category_key', 'other')
                if category not in by_category:
                    by_category[category] = {'count': 0, 'total': 0}
                by_category[category]['count'] += 1
                by_category[category]['total'] += amount

        return jsonify({
            'success': True,
            'parsed_expenses': parsed,
            'summary': {
                'total_count': len(parsed),
                'total_amount': total_amount,
                'by_category': by_category
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@intake_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'intake-api',
        'version': '1.0.0'
    }), 200
