"""
Entity Recommendation Module

This module provides AI-powered entity structure recommendations based on
business profiles and questionnaire responses.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import login_required, current_user
from app.models import User, BusinessProfile, QuestionnaireResponse, BusinessType
from app.access_control import requires_access_level
from ai.openai_interface import get_openai_response
import json
import logging
from datetime import datetime

# Create blueprint
entity_bp = Blueprint("entity", __name__, url_prefix="/entity")

# Entity types and their characteristics
ENTITY_TYPES = {
    "sole_proprietor": {
        "name": "Sole Proprietorship",
        "description": "A business owned and operated by one individual with no legal distinction between the owner and the business.",
        "formation_complexity": "Low",
        "liability_protection": "None",
        "tax_treatment": "Pass-through (Schedule C)",
        "best_for": [
            "New businesses just starting out",
            "Low-risk businesses",
            "Businesses with minimal assets or liabilities",
            "Freelancers and consultants"
        ],
        "tax_forms": ["Schedule C", "Schedule SE"],
        "advantages": [
            "Simple and inexpensive to form",
            "Full control by one owner",
            "Minimal paperwork",
            "Easy to dissolve",
            "All profits pass directly to owner's personal tax return"
        ],
        "disadvantages": [
            "Unlimited personal liability for business debts and claims",
            "Limited ability to raise capital",
            "Self-employment taxes on all profits",
            "Business ends if owner dies or becomes incapacitated"
        ]
    },
    "llc": {
        "name": "Limited Liability Company (LLC)",
        "description": "A flexible business entity that combines liability protection with pass-through taxation.",
        "formation_complexity": "Moderate",
        "liability_protection": "Good",
        "tax_treatment": "Flexible (default: pass-through)",
        "best_for": [
            "Small to medium-sized businesses seeking liability protection",
            "Real estate investments",
            "Businesses with potential liability risks",
            "Multiple owners with different investment levels"
        ],
        "tax_forms": [
            "Form 1065 and Schedule K-1 (multi-member)",
            "Schedule C (single-member)",
            "Form 8832 (for tax election changes)"
        ],
        "advantages": [
            "Limited personal liability protection",
            "Pass-through taxation by default",
            "Flexible management structure",
            "Fewer formal requirements than corporations",
            "Can elect different tax treatment (S-Corp or C-Corp)"
        ],
        "disadvantages": [
            "More expensive to form than sole proprietorship",
            "Self-employment taxes on all profits (unless elect S-Corp status)",
            "May require annual state fees",
            "Less precedent in legal cases than corporations"
        ]
    },
    "s_corp": {
        "name": "S Corporation",
        "description": "A corporation that elects to pass corporate income, losses, deductions, and credits through to shareholders for federal tax purposes.",
        "formation_complexity": "High",
        "liability_protection": "Strong",
        "tax_treatment": "Pass-through with payroll optimization",
        "best_for": [
            "Profitable small businesses with significant net income",
            "Businesses where owners actively work in the business",
            "Businesses seeking to reduce self-employment taxes",
            "Established companies with consistent profits"
        ],
        "tax_forms": [
            "Form 1120S (corporate return)",
            "Schedule K-1 (shareholder portion)",
            "Form 2553 (S-Corp election)",
            "Employment tax forms"
        ],
        "advantages": [
            "Limited personal liability protection",
            "No corporate tax at federal level",
            "Potential self-employment tax savings",
            "Separate legal entity exists indefinitely",
            "Clear ownership structure with stock"
        ],
        "disadvantages": [
            "More complex and expensive to form and maintain",
            "Strict qualification requirements",
            "Payroll requirements (reasonable salary)",
            "Limited to 100 shareholders and one class of stock",
            "More IRS scrutiny on salary vs. distributions"
        ]
    },
    "c_corp": {
        "name": "C Corporation",
        "description": "A legal entity that is separate and distinct from its owners, with its own tax treatment and structure.",
        "formation_complexity": "Highest",
        "liability_protection": "Strongest",
        "tax_treatment": "Double taxation (corporate + dividends)",
        "best_for": [
            "Businesses planning to raise significant outside investment",
            "Businesses planning to go public",
            "High-growth startups seeking venture capital",
            "Businesses with significant reinvestment needs"
        ],
        "tax_forms": [
            "Form 1120 (corporate return)",
            "Form 1099-DIV (for dividend payments)",
            "Various employment and information returns"
        ],
        "advantages": [
            "Limited personal liability protection",
            "Unlimited number of shareholders",
            "Multiple classes of stock possible",
            "Attractive for outside investors",
            "Perpetual existence",
            "Corporate tax rate may be lower than personal rate"
        ],
        "disadvantages": [
            "Double taxation on corporate profits and dividends",
            "Most expensive to form and maintain",
            "Most complex regulatory requirements",
            "Extensive record-keeping requirements",
            "Less flexibility in allocating profits and losses"
        ]
    }
}

@entity_bp.route("/")
@login_required
def index():
    """Entity structure recommendation tool"""
    # Get business profile
    business_profile = BusinessProfile.query.filter_by(user_id=current_user.id).first()
    
    # Check if user has taken the entity questionnaire
    questionnaire = QuestionnaireResponse.query.filter_by(
        user_id=current_user.id,
        questionnaire_type="entity_structure"
    ).order_by(QuestionnaireResponse.created_at.desc()).first()
    
    if not questionnaire:
        # User needs to complete the questionnaire first
        return redirect(url_for("entity.questionnaire"))
    
    # Generate recommendations
    recommendations = generate_entity_recommendations(business_profile, questionnaire.responses)
    
    return render_template(
        "entity/recommendations.html",
        recommendations=recommendations,
        entity_types=ENTITY_TYPES,
        questionnaire=questionnaire
    )

@entity_bp.route("/questionnaire", methods=["GET", "POST"])
@login_required
def questionnaire():
    """Entity structure questionnaire"""
    if request.method == "POST":
        responses = {}
        
        # Process form data
        for key, value in request.form.items():
            if key.startswith("question_"):
                question_id = key.replace("question_", "")
                responses[question_id] = value
        
        # Create questionnaire response
        questionnaire = QuestionnaireResponse(
            user_id=current_user.id,
            questionnaire_type="entity_structure",
            responses=responses
        )
        
        # Save to database
        from app.app import db
        db.session.add(questionnaire)
        db.session.commit()
        
        # Redirect to recommendations
        flash("Thank you for completing the questionnaire. Here are your entity recommendations.", "success")
        return redirect(url_for("entity.index"))
    
    # Get current user profile to pre-populate some fields
    business_profile = BusinessProfile.query.filter_by(user_id=current_user.id).first()
    
    return render_template(
        "entity/questionnaire.html",
        questions=get_entity_questionnaire(),
        business_profile=business_profile
    )

@entity_bp.route("/compare/<string:entity_type_1>/<string:entity_type_2>")
@login_required
@requires_access_level("guided")
def compare_entities(entity_type_1, entity_type_2):
    """Compare two business entity types"""
    if entity_type_1 not in ENTITY_TYPES or entity_type_2 not in ENTITY_TYPES:
        flash("Invalid entity types selected for comparison.", "danger")
        return redirect(url_for("entity.index"))
    
    # Build comparison data
    comparison = {
        "entity_1": ENTITY_TYPES[entity_type_1],
        "entity_2": ENTITY_TYPES[entity_type_2],
        "categories": [
            {
                "name": "Formation",
                "metrics": [
                    {
                        "name": "Formation Complexity",
                        "entity_1": ENTITY_TYPES[entity_type_1]["formation_complexity"],
                        "entity_2": ENTITY_TYPES[entity_type_2]["formation_complexity"]
                    },
                    {
                        "name": "Filing Requirements",
                        "entity_1": "Low" if entity_type_1 == "sole_proprietor" else ("Moderate" if entity_type_1 == "llc" else "High"),
                        "entity_2": "Low" if entity_type_2 == "sole_proprietor" else ("Moderate" if entity_type_2 == "llc" else "High")
                    },
                    {
                        "name": "Formation Costs",
                        "entity_1": "Low" if entity_type_1 == "sole_proprietor" else ("Moderate" if entity_type_1 == "llc" else "High"),
                        "entity_2": "Low" if entity_type_2 == "sole_proprietor" else ("Moderate" if entity_type_2 == "llc" else "High")
                    }
                ]
            },
            {
                "name": "Liability & Protection",
                "metrics": [
                    {
                        "name": "Liability Protection",
                        "entity_1": ENTITY_TYPES[entity_type_1]["liability_protection"],
                        "entity_2": ENTITY_TYPES[entity_type_2]["liability_protection"]
                    },
                    {
                        "name": "Personal Asset Protection",
                        "entity_1": "None" if entity_type_1 == "sole_proprietor" else "Yes",
                        "entity_2": "None" if entity_type_2 == "sole_proprietor" else "Yes"
                    }
                ]
            },
            {
                "name": "Taxation",
                "metrics": [
                    {
                        "name": "Tax Treatment",
                        "entity_1": ENTITY_TYPES[entity_type_1]["tax_treatment"],
                        "entity_2": ENTITY_TYPES[entity_type_2]["tax_treatment"]
                    },
                    {
                        "name": "Self-Employment Tax",
                        "entity_1": "All profits" if entity_type_1 in ["sole_proprietor", "llc"] else "Salary only",
                        "entity_2": "All profits" if entity_type_2 in ["sole_proprietor", "llc"] else "Salary only"
                    },
                    {
                        "name": "Double Taxation",
                        "entity_1": "Yes" if entity_type_1 == "c_corp" else "No",
                        "entity_2": "Yes" if entity_type_2 == "c_corp" else "No"
                    }
                ]
            },
            {
                "name": "Ownership & Governance",
                "metrics": [
                    {
                        "name": "Ownership Restrictions",
                        "entity_1": "Single owner only" if entity_type_1 == "sole_proprietor" else ("100 shareholders max" if entity_type_1 == "s_corp" else "No restrictions"),
                        "entity_2": "Single owner only" if entity_type_2 == "sole_proprietor" else ("100 shareholders max" if entity_type_2 == "s_corp" else "No restrictions")
                    },
                    {
                        "name": "Management Flexibility",
                        "entity_1": "High" if entity_type_1 in ["sole_proprietor", "llc"] else "Limited",
                        "entity_2": "High" if entity_type_2 in ["sole_proprietor", "llc"] else "Limited"
                    },
                    {
                        "name": "Formality Requirements",
                        "entity_1": "Low" if entity_type_1 == "sole_proprietor" else ("Moderate" if entity_type_1 == "llc" else "High"),
                        "entity_2": "Low" if entity_type_2 == "sole_proprietor" else ("Moderate" if entity_type_2 == "llc" else "High")
                    }
                ]
            }
        ]
    }
    
    return render_template(
        "entity/compare.html",
        comparison=comparison,
        entity_1=ENTITY_TYPES[entity_type_1],
        entity_2=ENTITY_TYPES[entity_type_2]
    )

@entity_bp.route("/details/<string:entity_type>")
@login_required
def entity_details(entity_type):
    """Detailed information about a specific entity type"""
    if entity_type not in ENTITY_TYPES:
        flash("Invalid entity type selected.", "danger")
        return redirect(url_for("entity.index"))
    
    # Get user's business profile
    business_profile = BusinessProfile.query.filter_by(user_id=current_user.id).first()
    
    # Generate customized insights
    customized_insights = generate_entity_insights(entity_type, business_profile)
    
    # Check if the entity type requires a higher tier than user's current plan
    from app.pricing import is_business_type_eligible_for_tier
    eligible = is_business_type_eligible_for_tier(BusinessType(entity_type), current_user.plan)
    
    return render_template(
        "entity/details.html",
        entity=ENTITY_TYPES[entity_type],
        entity_type=entity_type,
        customized_insights=customized_insights,
        eligible_for_current_plan=eligible
    )

@entity_bp.route("/update-entity", methods=["POST"])
@login_required
def update_entity():
    """Update user's business entity type"""
    entity_type = request.form.get("entity_type")
    
    if not entity_type or entity_type not in ENTITY_TYPES:
        flash("Invalid entity type selected.", "danger")
        return redirect(url_for("entity.index"))
    
    # Check if the entity type requires a higher tier than user's current plan
    from app.pricing import is_business_type_eligible_for_tier
    if not is_business_type_eligible_for_tier(BusinessType(entity_type), current_user.plan):
        flash(f"Your current plan doesn't support {ENTITY_TYPES[entity_type]['name']}. Please upgrade to access this entity type.", "warning")
        return redirect(url_for("billing.pricing"))
    
    # Update business profile
    business_profile = BusinessProfile.query.filter_by(user_id=current_user.id).first()
    
    if business_profile:
        from app.app import db
        business_profile.business_type = BusinessType(entity_type)
        db.session.commit()
        
        flash(f"Your business entity type has been updated to {ENTITY_TYPES[entity_type]['name']}.", "success")
    else:
        flash("Please complete your business profile first.", "warning")
    
    return redirect(url_for("profile.business_profile"))

def get_entity_questionnaire():
    """Get entity structure questionnaire questions"""
    return [
        {
            "id": "business_purpose",
            "question": "What is the primary purpose of your business?",
            "type": "select",
            "options": [
                {"value": "service", "label": "Providing services"},
                {"value": "product", "label": "Selling products"},
                {"value": "investment", "label": "Managing investments"},
                {"value": "real_estate", "label": "Real estate"},
                {"value": "tech", "label": "Technology/software"},
                {"value": "mixed", "label": "Mixed"}
            ]
        },
        {
            "id": "liability_concerns",
            "question": "How concerned are you about personal liability?",
            "type": "select",
            "options": [
                {"value": "not_concerned", "label": "Not concerned"},
                {"value": "somewhat_concerned", "label": "Somewhat concerned"},
                {"value": "very_concerned", "label": "Very concerned"},
                {"value": "extremely_concerned", "label": "Extremely concerned"}
            ]
        },
        {
            "id": "ownership",
            "question": "How many owners will the business have?",
            "type": "select",
            "options": [
                {"value": "one", "label": "Just me (1 owner)"},
                {"value": "two_to_five", "label": "2-5 owners"},
                {"value": "six_to_ten", "label": "6-10 owners"},
                {"value": "more_than_ten", "label": "More than 10 owners"},
                {"value": "many", "label": "Many (planning to raise capital from numerous investors)"}
            ]
        },
        {
            "id": "growth_plans",
            "question": "What are your plans for business growth?",
            "type": "select",
            "options": [
                {"value": "lifestyle", "label": "Lifestyle business (steady, manageable growth)"},
                {"value": "moderate", "label": "Moderate growth with internal funding"},
                {"value": "rapid", "label": "Rapid growth with potential outside investors"},
                {"value": "acquisition", "label": "Growth through acquisition of other businesses"},
                {"value": "exit", "label": "Build for quick exit/sale"}
            ]
        },
        {
            "id": "reinvestment",
            "question": "How much of the profits do you plan to reinvest in the business?",
            "type": "select",
            "options": [
                {"value": "minimal", "label": "Minimal (taking most profits as personal income)"},
                {"value": "quarter", "label": "About 25%"},
                {"value": "half", "label": "About 50%"},
                {"value": "most", "label": "Most profits (75% or more)"},
                {"value": "all", "label": "All profits initially"}
            ]
        },
        {
            "id": "tax_priorities",
            "question": "What are your tax priorities?",
            "type": "select",
            "options": [
                {"value": "simplicity", "label": "Simplicity in filing"},
                {"value": "minimize_self_employment", "label": "Minimizing self-employment taxes"},
                {"value": "maximize_deductions", "label": "Maximizing deductions"},
                {"value": "retirement", "label": "Retirement planning/benefits"},
                {"value": "overall_minimization", "label": "Overall tax minimization strategy"}
            ]
        },
        {
            "id": "expected_annual_profit",
            "question": "What is your expected annual net profit?",
            "type": "select",
            "options": [
                {"value": "loss", "label": "Operating at a loss initially"},
                {"value": "under_50k", "label": "Under $50,000"},
                {"value": "50k_100k", "label": "$50,000 - $100,000"},
                {"value": "100k_250k", "label": "$100,000 - $250,000"},
                {"value": "250k_500k", "label": "$250,000 - $500,000"},
                {"value": "over_500k", "label": "Over $500,000"}
            ]
        },
        {
            "id": "business_risk",
            "question": "How would you characterize your business risk level?",
            "type": "select",
            "options": [
                {"value": "very_low", "label": "Very low (e.g., consulting, writing)"},
                {"value": "low", "label": "Low (e.g., online services, software)"},
                {"value": "moderate", "label": "Moderate (e.g., retail, food service)"},
                {"value": "high", "label": "High (e.g., construction, manufacturing)"},
                {"value": "very_high", "label": "Very high (e.g., medical, financial services)"}
            ]
        },
        {
            "id": "external_funding",
            "question": "Do you plan to seek external funding/investments?",
            "type": "select",
            "options": [
                {"value": "no", "label": "No external funding needed"},
                {"value": "loans", "label": "Business loans only"},
                {"value": "friends_family", "label": "Friends and family investments"},
                {"value": "angel", "label": "Angel investors"},
                {"value": "venture", "label": "Venture capital"},
                {"value": "public", "label": "Eventually go public"}
            ]
        },
        {
            "id": "complexity_tolerance",
            "question": "What level of administrative complexity can you manage?",
            "type": "select",
            "options": [
                {"value": "minimal", "label": "Minimal (prefer simplicity over optimization)"},
                {"value": "moderate", "label": "Moderate (willing to handle some requirements)"},
                {"value": "significant", "label": "Significant (will hire help for complex requirements)"},
                {"value": "whatever_needed", "label": "Whatever is needed for optimal structure"}
            ]
        }
    ]

def generate_entity_recommendations(business_profile, questionnaire_responses):
    """
    Generate entity structure recommendations based on business profile and questionnaire
    
    Args:
        business_profile: BusinessProfile object
        questionnaire_responses: Dictionary of questionnaire responses
        
    Returns:
        Dictionary with recommendations
    """
    # Points-based recommendation system
    points = {
        "sole_proprietor": 0,
        "llc": 0,
        "s_corp": 0,
        "c_corp": 0
    }
    
    # Factor 1: Business risk/liability
    liability_concern = questionnaire_responses.get("liability_concerns", "not_concerned")
    business_risk = questionnaire_responses.get("business_risk", "very_low")
    
    # Lower points for sole proprietorship with higher risk or liability concerns
    if liability_concern in ["very_concerned", "extremely_concerned"]:
        points["sole_proprietor"] -= 20
        points["llc"] += 10
        points["s_corp"] += 8
        points["c_corp"] += 8
    elif liability_concern == "somewhat_concerned":
        points["sole_proprietor"] -= 10
        points["llc"] += 5
        points["s_corp"] += 3
        points["c_corp"] += 3
    else:  # not concerned
        points["sole_proprietor"] += 5
    
    if business_risk in ["high", "very_high"]:
        points["sole_proprietor"] -= 15
        points["llc"] += 8
        points["s_corp"] += 5
        points["c_corp"] += 5
    elif business_risk == "moderate":
        points["sole_proprietor"] -= 5
        points["llc"] += 3
    
    # Factor 2: Number of owners
    ownership = questionnaire_responses.get("ownership", "one")
    
    if ownership == "one":
        points["sole_proprietor"] += 10
        points["llc"] += 5
    elif ownership == "two_to_five":
        points["sole_proprietor"] -= 50  # Not possible
        points["llc"] += 10
        points["s_corp"] += 8
    elif ownership == "six_to_ten":
        points["sole_proprietor"] -= 50  # Not possible
        points["llc"] += 8
        points["s_corp"] += 10
    elif ownership == "more_than_ten":
        points["sole_proprietor"] -= 50  # Not possible
        points["llc"] += 5
        points["s_corp"] += 5  # Limited to 100 shareholders
        points["c_corp"] += 15
    elif ownership == "many":
        points["sole_proprietor"] -= 50  # Not possible
        points["llc"] -= 5
        points["s_corp"] -= 20  # Not suitable for many owners
        points["c_corp"] += 25
    
    # Factor 3: Expected profit
    expected_profit = questionnaire_responses.get("expected_annual_profit", "under_50k")
    
    if expected_profit in ["loss", "under_50k"]:
        points["sole_proprietor"] += 8
        points["llc"] += 5
        points["s_corp"] -= 5
        points["c_corp"] -= 10
    elif expected_profit == "50k_100k":
        points["sole_proprietor"] += 3
        points["llc"] += 8
        points["s_corp"] += 0
        points["c_corp"] -= 5
    elif expected_profit == "100k_250k":
        points["sole_proprietor"] -= 2
        points["llc"] += 3
        points["s_corp"] += 10
        points["c_corp"] -= 2
    elif expected_profit in ["250k_500k", "over_500k"]:
        points["sole_proprietor"] -= 10
        points["llc"] += 0
        points["s_corp"] += 15
        points["c_corp"] += 5
    
    # Factor 4: Growth plans and external funding
    growth_plans = questionnaire_responses.get("growth_plans", "lifestyle")
    external_funding = questionnaire_responses.get("external_funding", "no")
    
    if growth_plans in ["lifestyle", "moderate"]:
        points["sole_proprietor"] += 5
        points["llc"] += 8
        points["s_corp"] += 5
        points["c_corp"] -= 5
    elif growth_plans in ["rapid", "acquisition", "exit"]:
        points["sole_proprietor"] -= 10
        points["llc"] += 0
        points["s_corp"] += 5
        points["c_corp"] += 15
    
    if external_funding in ["no", "loans"]:
        points["sole_proprietor"] += 3
        points["llc"] += 5
    elif external_funding in ["friends_family", "angel"]:
        points["sole_proprietor"] -= 5
        points["llc"] += 8
        points["s_corp"] += 5
        points["c_corp"] += 2
    elif external_funding in ["venture", "public"]:
        points["sole_proprietor"] -= 15
        points["llc"] -= 5
        points["s_corp"] -= 10
        points["c_corp"] += 25
    
    # Factor 5: Tax priorities
    tax_priorities = questionnaire_responses.get("tax_priorities", "simplicity")
    
    if tax_priorities == "simplicity":
        points["sole_proprietor"] += 10
        points["llc"] += 5
        points["s_corp"] -= 5
        points["c_corp"] -= 10
    elif tax_priorities == "minimize_self_employment":
        points["sole_proprietor"] -= 15
        points["llc"] -= 5
        points["s_corp"] += 20
        points["c_corp"] += 10
    elif tax_priorities == "maximize_deductions":
        points["sole_proprietor"] += 0
        points["llc"] += 5
        points["s_corp"] += 10
        points["c_corp"] += 5
    elif tax_priorities in ["retirement", "overall_minimization"]:
        points["sole_proprietor"] -= 5
        points["llc"] += 0
        points["s_corp"] += 15
        points["c_corp"] += 10
    
    # Factor 6: Complexity tolerance
    complexity_tolerance = questionnaire_responses.get("complexity_tolerance", "minimal")
    
    if complexity_tolerance == "minimal":
        points["sole_proprietor"] += 15
        points["llc"] += 5
        points["s_corp"] -= 10
        points["c_corp"] -= 15
    elif complexity_tolerance == "moderate":
        points["sole_proprietor"] += 5
        points["llc"] += 10
        points["s_corp"] += 0
        points["c_corp"] -= 5
    elif complexity_tolerance in ["significant", "whatever_needed"]:
        points["sole_proprietor"] += 0
        points["llc"] += 5
        points["s_corp"] += 10
        points["c_corp"] += 5
    
    # Adjust for special business types or industries
    if business_profile:
        # Real estate holdings often benefit from LLC
        if questionnaire_responses.get("business_purpose") == "real_estate":
            points["llc"] += 10
        
        # Professional services sometimes have specific entity requirements
        if business_profile.industry in ["legal", "medical", "accounting"]:
            points["sole_proprietor"] -= 5
            points["s_corp"] += 5
            points["llc"] += 5  # Professional LLC
        
        # Retail or physical product businesses with higher liability
        if business_profile.industry in ["retail", "manufacturing"]:
            points["sole_proprietor"] -= 5
            points["llc"] += 3
    
    # Sort entities by points
    sorted_entities = sorted(points.items(), key=lambda x: x[1], reverse=True)
    
    # Get the top recommendation and alternatives
    primary = sorted_entities[0][0]
    alternatives = [entity for entity, _ in sorted_entities[1:]]
    
    # Provide additional insights for the primary recommendation
    primary_insights = get_entity_insights(primary, questionnaire_responses)
    
    # Consider using OpenAI for enhanced recommendations if needed
    ai_recommendations = False
    if current_user.plan.value in ["guided", "concierge"]:
        ai_recommendations = True
        try:
            enhanced_insights = generate_ai_entity_recommendation(business_profile, questionnaire_responses)
        except:
            enhanced_insights = None
    else:
        enhanced_insights = None
    
    return {
        "primary": {
            "entity_type": primary,
            "entity_info": ENTITY_TYPES[primary],
            "score": points[primary],
            "insights": primary_insights
        },
        "alternatives": [
            {
                "entity_type": alt,
                "entity_info": ENTITY_TYPES[alt],
                "score": points[alt]
            } for alt in alternatives
        ],
        "enhanced_insights": enhanced_insights,
        "has_ai_recommendations": ai_recommendations,
        "questionnaire_responses": questionnaire_responses
    }

def get_entity_insights(entity_type, questionnaire_responses):
    """
    Get specific insights for an entity type based on questionnaire responses
    
    Args:
        entity_type: Entity type key
        questionnaire_responses: Dictionary of questionnaire responses
        
    Returns:
        List of insight dictionaries
    """
    insights = []
    
    # Common insights for Sole Proprietorship
    if entity_type == "sole_proprietor":
        insights.append({
            "type": "advantage",
            "title": "Simplicity",
            "description": "A sole proprietorship requires minimal paperwork and is the simplest to set up and maintain."
        })
        
        if questionnaire_responses.get("expected_annual_profit") in ["under_50k", "50k_100k"]:
            insights.append({
                "type": "advantage",
                "title": "Cost-Effective for Lower Profits",
                "description": "With your expected profit level, a sole proprietorship avoids unnecessary administrative costs."
            })
        else:
            insights.append({
                "type": "caution",
                "title": "Self-Employment Tax Consideration",
                "description": "With higher profits, you'll pay self-employment tax on the entire amount, which might not be optimal."
            })
        
        if questionnaire_responses.get("liability_concerns") in ["very_concerned", "extremely_concerned"]:
            insights.append({
                "type": "warning",
                "title": "Liability Risk",
                "description": "Given your liability concerns, a sole proprietorship offers no separation between personal and business assets."
            })
    
    # Common insights for LLC
    elif entity_type == "llc":
        insights.append({
            "type": "advantage",
            "title": "Liability Protection",
            "description": "An LLC provides personal asset protection while maintaining relatively simple administration."
        })
        
        if questionnaire_responses.get("ownership") != "one":
            insights.append({
                "type": "advantage",
                "title": "Multi-Member Flexibility",
                "description": "LLCs easily accommodate multiple owners with flexible profit distribution options."
            })
        
        if questionnaire_responses.get("expected_annual_profit") in ["250k_500k", "over_500k"]:
            insights.append({
                "type": "consideration",
                "title": "Consider S-Corp Election",
                "description": "With your profit level, you might benefit from electing S-Corporation tax treatment to reduce self-employment taxes."
            })
    
    # Common insights for S-Corp
    elif entity_type == "s_corp":
        insights.append({
            "type": "advantage",
            "title": "Self-Employment Tax Savings",
            "description": "S-Corporations can save on self-employment taxes by paying a reasonable salary plus distributions."
        })
        
        if questionnaire_responses.get("expected_annual_profit") in ["under_50k", "loss"]:
            insights.append({
                "type": "caution",
                "title": "Cost vs. Benefit",
                "description": "With lower profits, the administrative costs of an S-Corporation might outweigh the tax benefits."
            })
        
        if questionnaire_responses.get("complexity_tolerance") == "minimal":
            insights.append({
                "type": "warning",
                "title": "Administrative Requirements",
                "description": "S-Corporations require more paperwork, including payroll, annual meetings, and separate tax filings."
            })
    
    # Common insights for C-Corp
    elif entity_type == "c_corp":
        insights.append({
            "type": "advantage",
            "title": "Investment-Ready Structure",
            "description": "C-Corporations are the preferred entity type for most outside investors and venture capital."
        })
        
        if questionnaire_responses.get("external_funding") in ["no", "loans", "friends_family"]:
            insights.append({
                "type": "caution",
                "title": "Potentially Unnecessary Complexity",
                "description": "Without plans for significant external investment, a C-Corporation may introduce unnecessary complexity and costs."
            })
        
        if questionnaire_responses.get("expected_annual_profit") in ["loss", "under_50k", "50k_100k"]:
            insights.append({
                "type": "warning",
                "title": "Double Taxation Concern",
                "description": "C-Corporations face double taxation on profits, which can be inefficient for smaller businesses."
            })
    
    return insights

def generate_ai_entity_recommendation(business_profile, questionnaire_responses):
    """
    Generate enhanced entity recommendations using OpenAI
    
    Args:
        business_profile: BusinessProfile object
        questionnaire_responses: Dictionary of questionnaire responses
        
    Returns:
        Dictionary with AI-generated recommendations
    """
    try:
        # Format the business data for the prompt
        business_data = {
            "business_name": business_profile.business_name if business_profile else "Your Business",
            "industry": business_profile.industry if business_profile else "Unknown",
            "annual_revenue": business_profile.annual_revenue if business_profile else 0,
            "employee_count": business_profile.employee_count if business_profile else 0,
            "contractor_count": business_profile.contractor_count if business_profile else 0,
            "states": business_profile.operating_states if business_profile else ["Unknown"],
            "has_home_office": business_profile.has_home_office if business_profile else False,
            "current_entity_type": business_profile.business_type.value if business_profile and business_profile.business_type else "unknown"
        }
        
        # Create the prompt for OpenAI
        system_message = """
        You are an expert business entity advisor with extensive knowledge in tax law and business structures.
        Analyze the provided business profile and questionnaire responses to recommend the optimal business 
        entity structure. Focus on tax implications, liability protection, and administrative requirements.
        
        Provide a detailed, personalized recommendation with 3-5 specific strategic insights.
        Include pros and cons of the recommended structure in the context of the specific business.
        """
        
        user_message = f"""
        Please analyze this business profile and questionnaire responses to recommend the optimal business entity structure:
        
        BUSINESS PROFILE:
        - Business Name: {business_data["business_name"]}
        - Industry: {business_data["industry"]}
        - Annual Revenue: ${business_data["annual_revenue"]:,.2f}
        - Employees: {business_data["employee_count"]}
        - Contractors: {business_data["contractor_count"]}
        - Operating States: {", ".join(business_data["states"]) if isinstance(business_data["states"], list) else business_data["states"]}
        - Home Office: {"Yes" if business_data["has_home_office"] else "No"}
        - Current Entity Type: {business_data["current_entity_type"]}
        
        QUESTIONNAIRE RESPONSES:
        - Business Purpose: {questionnaire_responses.get("business_purpose", "Unknown")}
        - Liability Concerns: {questionnaire_responses.get("liability_concerns", "Unknown")}
        - Ownership Structure: {questionnaire_responses.get("ownership", "Unknown")}
        - Growth Plans: {questionnaire_responses.get("growth_plans", "Unknown")}
        - Profit Reinvestment: {questionnaire_responses.get("reinvestment", "Unknown")}
        - Tax Priorities: {questionnaire_responses.get("tax_priorities", "Unknown")}
        - Expected Annual Profit: {questionnaire_responses.get("expected_annual_profit", "Unknown")}
        - Business Risk Level: {questionnaire_responses.get("business_risk", "Unknown")}
        - External Funding Plans: {questionnaire_responses.get("external_funding", "Unknown")}
        - Complexity Tolerance: {questionnaire_responses.get("complexity_tolerance", "Unknown")}
        
        Please provide:
        1. The recommended entity structure with a brief justification
        2. 3-5 specific strategic insights based on the business profile
        3. Key tax considerations for this business
        4. Potential pitfalls or special considerations
        """
        
        # Get response from OpenAI
        response = get_openai_response(system_message, user_message)
        
        # Parse the response to extract key sections
        sections = {
            "recommendation": extract_section(response, "recommended entity structure", "specific strategic insights"),
            "strategic_insights": extract_section(response, "specific strategic insights", "key tax considerations"),
            "tax_considerations": extract_section(response, "key tax considerations", "potential pitfalls"),
            "pitfalls": extract_section(response, "potential pitfalls")
        }
        
        return sections
    
    except Exception as e:
        logging.error(f"Error generating AI entity recommendations: {e}")
        return None

def generate_entity_insights(entity_type, business_profile):
    """
    Generate customized insights for an entity type based on a specific business profile
    
    Args:
        entity_type: Entity type key
        business_profile: BusinessProfile object
        
    Returns:
        Dictionary with customized insights
    """
    insights = {
        "tax_insights": [],
        "legal_insights": [],
        "operational_insights": []
    }
    
    # Generate insights based on entity type and business profile
    if entity_type == "sole_proprietor":
        # Tax insights
        if business_profile and business_profile.annual_revenue > 0:
            if business_profile.annual_revenue > 50000:
                insights["tax_insights"].append(
                    "Consider quarterly estimated tax payments as a sole proprietor, especially with your revenue level."
                )
            
            if business_profile.has_home_office:
                insights["tax_insights"].append(
                    "Your home office may qualify for a deduction, which can reduce your Schedule C income."
                )
        
        # Legal insights
        insights["legal_insights"].append(
            "As a sole proprietor, consider business liability insurance to protect personal assets."
        )
        
        # Operational insights
        insights["operational_insights"].append(
            "Keep meticulous records of business expenses separate from personal expenses to simplify tax filing."
        )
    
    elif entity_type == "llc":
        # Tax insights
        if business_profile and business_profile.annual_revenue > 0:
            if business_profile.annual_revenue > 100000:
                insights["tax_insights"].append(
                    "With your revenue level, consider the potential tax benefits of electing S-Corporation taxation for your LLC."
                )
            
            if business_profile.operating_states and len(business_profile.operating_states) > 1:
                insights["tax_insights"].append(
                    "Your LLC may need to register as a foreign LLC in all states where you conduct business."
                )
        
        # Legal insights
        insights["legal_insights"].append(
            "Create a comprehensive operating agreement to define member rights and responsibilities."
        )
        
        # Operational insights
        insights["operational_insights"].append(
            "Maintain clear separation between business and personal finances to preserve LLC liability protection."
        )
    
    elif entity_type == "s_corp":
        # Tax insights
        if business_profile:
            insights["tax_insights"].append(
                "Pay yourself a reasonable salary subject to employment taxes, with additional profits as distributions."
            )
            
            if business_profile.employee_count > 0 or business_profile.contractor_count > 0:
                insights["tax_insights"].append(
                    "Your S-Corporation must handle payroll tax filings for all employees, including owner-employees."
                )
        
        # Legal insights
        insights["legal_insights"].append(
            "Hold annual meetings and maintain corporate minutes to preserve S-Corporation status."
        )
        
        # Operational insights
        insights["operational_insights"].append(
            "Set up proper payroll systems to ensure your salary is reasonable relative to distributions."
        )
    
    elif entity_type == "c_corp":
        # Tax insights
        if business_profile:
            insights["tax_insights"].append(
                "Consider strategic timing of dividends and employee benefits to manage overall tax burden."
            )
            
            if business_profile.annual_revenue < 250000:
                insights["tax_insights"].append(
                    "At your current revenue level, the double taxation of C-Corporations may outweigh the benefits."
                )
        
        # Legal insights
        insights["legal_insights"].append(
            "Maintain strict corporate formalities including board meetings, minutes, and corporate bylaws."
        )
        
        # Operational insights
        insights["operational_insights"].append(
            "Consider establishing a fiscal year different from the calendar year for potential tax planning advantages."
        )
    
    return insights

def extract_section(text, start_marker, end_marker=None):
    """
    Extract a section from text between start and end markers
    
    Args:
        text: Text to search
        start_marker: Text marking the start of the section
        end_marker: Optional text marking the end of the section
        
    Returns:
        Extracted text section
    """
    if not text:
        return ""
    
    text_lower = text.lower()
    start_marker_lower = start_marker.lower()
    
    # Find the start position
    start_pos = text_lower.find(start_marker_lower)
    if start_pos == -1:
        return ""
    
    # Adjust start position to include the header
    start_pos = text.find("\n", start_pos)
    if start_pos == -1:
        start_pos = len(start_marker)
    else:
        start_pos += 1
    
    # Find the end position if end marker is provided
    if end_marker:
        end_marker_lower = end_marker.lower()
        end_pos = text_lower.find(end_marker_lower, start_pos)
        if end_pos != -1:
            return text[start_pos:end_pos].strip()
    
    # If no end marker or end marker not found, return to the end
    return text[start_pos:].strip()