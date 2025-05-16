"""
Pricing Module

This module defines the pricing tiers, features, and business type eligibility
for the .fylr tax platform.
"""

# Pricing tier definitions
TIERS = {
    "self_service": {
        "name": "Self-Service",
        "price": 97,
        "description": "Automated tax form preparation with AI assistance",
        "features": [
            "Auto-fill IRS and State tax forms",
            "Smart document upload (OCR enabled)",
            "AI assistance and suggestions",
            "Download-ready tax PDF package",
            "Basic error check"
        ],
        "upsell_triggers": [
            "High risk of audit",
            "Inconsistent documentation",
            "Complex entity structure"
        ]
    },
    "guided": {
        "name": "Guided",
        "price": 197,
        "description": "Enhanced tax assistance with AI recommendations",
        "features": [
            "Everything in Self-Service",
            "AI-powered tax strategy recommendations",
            "Smart alerts for deductions and credits",
            "Review checklist with compliance warnings",
            "Optional year-end closing walkthrough"
        ],
        "upsell_triggers": [
            "Desire for optimization",
            "Business with employees or contractors",
            "Capital gains or losses"
        ]
    },
    "concierge": {
        "name": "Concierge",
        "price": 497,
        "description": "Premium tax service with audit protection",
        "features": [
            "Everything in Guided",
            "Automated document collection and compilation",
            "AI-reviewed tax package filing",
            "Lifetime digital backup",
            "Priority support",
            "Audit protection plan"
        ]
    }
}

# Business type eligibility
BUSINESS_TYPES = {
    "sole_proprietor": {
        "name": "Sole Proprietorship",
        "description": "A business owned and operated by one individual",
        "eligible_tiers": ["self_service", "guided", "concierge"],
        "required_docs": ["ID", "SSN", "Business Income Proof", "Expense Records"]
    },
    "llc": {
        "name": "Limited Liability Company (LLC)",
        "description": "A business structure that provides personal liability protection",
        "eligible_tiers": ["self_service", "guided", "concierge"],
        "required_docs": ["EIN", "Articles of Organization", "Operating Agreement", "Income & Expense Records"]
    },
    "s_corp": {
        "name": "S Corporation",
        "description": "A corporation that passes corporate income, losses, deductions, and credits to shareholders",
        "eligible_tiers": ["guided", "concierge"],
        "required_docs": ["EIN", "Form 2553", "Bylaws", "Income Statement", "Payroll Summary"]
    },
    "c_corp": {
        "name": "C Corporation",
        "description": "A legal structure for a business where owners are taxed separately from the entity",
        "eligible_tiers": ["guided", "concierge"],
        "required_docs": ["EIN", "Articles of Incorporation", "Income Statement", "Balance Sheet", "Payroll Summary"]
    }
}

# Audit protection add-on
AUDIT_PROTECTION = {
    "name": "Audit Protection Plan",
    "description": "Protection and support in case of an IRS audit",
    "included_tiers": ["concierge"],
    "optional_add_on_price": 99,
    "coverage_details": "Includes up to 2 IRS responses per year and 1 state filing support. AI-based document match verification included."
}

def get_tier_info(tier):
    """Get information about a specific pricing tier"""
    return TIERS.get(tier, None)

def get_business_type_info(business_type):
    """Get information about a specific business type"""
    return BUSINESS_TYPES.get(business_type, None)

def is_business_type_eligible_for_tier(business_type, tier):
    """Check if a business type is eligible for a specific tier"""
    business_info = get_business_type_info(business_type)
    if not business_info:
        return False
    
    return tier in business_info.get('eligible_tiers', [])

def get_eligible_tiers_for_business(business_type):
    """Get all eligible tiers for a specific business type"""
    business_info = get_business_type_info(business_type)
    if not business_info:
        return []
    
    return business_info.get('eligible_tiers', [])

def get_required_docs_for_business(business_type):
    """Get required documents for a specific business type"""
    business_info = get_business_type_info(business_type)
    if not business_info:
        return []
    
    return business_info.get('required_docs', [])

def is_audit_protection_included(tier):
    """Check if audit protection is included in a specific tier"""
    return tier in AUDIT_PROTECTION.get('included_tiers', [])

def get_audit_protection_price(tier):
    """Get the price of audit protection for a specific tier"""
    if is_audit_protection_included(tier):
        return 0
    
    return AUDIT_PROTECTION.get('optional_add_on_price', 99)