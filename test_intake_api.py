"""
Test script for Intake API

Demonstrates the Dynamic Tax Engine capabilities without requiring API keys
"""

import json
from app.modules.intake import (
    parse_expense_string,
    assess_business_complexity,
    optimize_startup_costs
)


def test_expense_parsing():
    """Test natural language expense parsing"""
    print("\n" + "=" * 70)
    print("TEST 1: Natural Language Expense Parsing")
    print("=" * 70)

    test_cases = [
        "I bought a $3k laptop for my business",
        "Spent $1200 on office rent this month",
        "Hired an accountant for $500",
        "Business dinner with client $85",
        "LLC formation fees $800"
    ]

    for description in test_cases:
        print(f"\nInput: {description}")
        result = parse_expense_string(description)

        if result['success']:
            expense = result['expense']
            print(f"   ├─ Amount: ${expense['amount']}")
            print(f"   ├─ IRS Category: {expense['irs_category']}")
            print(f"   ├─ Schedule C Line: {expense['schedule_c_line']} - {expense['schedule_c_description']}")
            print(f"   ├─ Deductible: {expense['deduction_percentage']}%")
            print(f"   ├─ Startup Cost: {'Yes' if expense['is_startup_cost'] else 'No'}")
            print(f"   ├─ Audit Risk: {expense['audit_risk']}")
            print(f"   └─ Confidence: {expense['confidence'] * 100:.0f}%")
        else:
            print(f"   └─ Error: {result.get('error')}")


def test_complexity_assessment():
    """Test business complexity assessment"""
    print("\n" + "=" * 70)
    print("TEST 2: Business Complexity Assessment")
    print("=" * 70)

    # Simple business
    print("\n🏢 Scenario A: Simple Freelancer")
    simple_expenses = [
        "Bought a laptop",
        "Paid for internet service",
        "Office supplies"
    ]
    simple_result = assess_business_complexity(simple_expenses)
    print(f"   ├─ Complexity Level: {simple_result['complexity_level']}")
    print(f"   ├─ Complexity Score: {simple_result['complexity_score']}")
    print(f"   ├─ Recommended Tier: {simple_result['recommended_tier']}")
    print(f"   └─ Advanced Questionnaire Needed: {simple_result['requires_advanced_questionnaire']}")

    # Complex business
    print("\n🏢 Scenario B: Growing Business with Employees")
    complex_expenses = [
        "Hired 3 employees this year",
        "Bought inventory from overseas supplier",
        "Paid payroll taxes",
        "International shipping costs"
    ]
    complex_profile = {
        'has_employees': True,
        'has_inventory': True,
        'annual_revenue': 350000
    }
    complex_result = assess_business_complexity(complex_expenses, complex_profile)
    print(f"   ├─ Complexity Level: {complex_result['complexity_level']}")
    print(f"   ├─ Complexity Score: {complex_result['complexity_score']}")
    print(f"   ├─ Recommended Tier: {complex_result['recommended_tier']}")
    print(f"   ├─ Advanced Questionnaire Needed: {complex_result['requires_advanced_questionnaire']}")
    print(f"   ├─ Estimated Forms: {', '.join(complex_result['estimated_forms'])}")
    print(f"   └─ Complexity Flags:")
    for flag in complex_result['flags']:
        print(f"       • {flag['category']}: {flag['recommendation'][:60]}...")


def test_startup_optimization():
    """Test startup cost optimization"""
    print("\n" + "=" * 70)
    print("TEST 3: Startup Cost Optimization (Loss-Leader Strategy)")
    print("=" * 70)

    # Scenario: New business with $0 revenue
    startup_expenses = [
        {
            'description': 'LLC formation fees',
            'amount': 800,
            'is_startup_cost': True
        },
        {
            'description': 'Initial website development',
            'amount': 2500,
            'is_startup_cost': True
        },
        {
            'description': 'Business insurance - first year',
            'amount': 1200,
            'is_startup_cost': True
        },
        {
            'description': 'Marketing campaign',
            'amount': 1500,
            'is_startup_cost': True
        }
    ]

    result = optimize_startup_costs(startup_expenses, revenue=0)

    print(f"\n💰 Startup Cost Analysis:")
    print(f"   ├─ Total Startup Costs: ${result['total_startup_costs']:,.2f}")
    print(f"   ├─ Immediate Deduction (Year 1): ${result['immediate_deduction']:,.2f}")
    print(f"   ├─ Amount to Amortize: ${result['amortizable_amount']:,.2f}")
    print(f"   ├─ Monthly Amortization: ${result['monthly_amortization']:,.2f}")
    print(f"   ├─ First Year Total Deduction: ${result['first_year_total_deduction']:,.2f}")
    print(f"   ├─ Strategy: {result['strategy']}")
    print(f"   └─ IRS Form Required: {result['irs_form']}")

    print(f"\n💡 Recommendations:")
    for i, rec in enumerate(result['recommendations'], 1):
        print(f"   {i}. {rec}")


def test_json_output():
    """Test JSON output format"""
    print("\n" + "=" * 70)
    print("TEST 4: JSON Output Format (for Glass Card Updates)")
    print("=" * 70)

    description = "I spent $2800 on a new computer"
    result = parse_expense_string(description)

    print(f"\n📦 Raw JSON Output:")
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("🚀 DYNAMIC TAX ENGINE - INTAKE API TESTS")
    print("=" * 70)

    test_expense_parsing()
    test_complexity_assessment()
    test_startup_optimization()
    test_json_output()

    print("\n" + "=" * 70)
    print("✅ All tests completed!")
    print("=" * 70)
    print("\n💡 These functions are available via REST API at:")
    print("   • POST /api/intake/parse-expense")
    print("   • POST /api/intake/assess-complexity")
    print("   • POST /api/intake/optimize-startup")
    print("   • POST /api/intake/batch-parse (authenticated)")
    print("\n")
