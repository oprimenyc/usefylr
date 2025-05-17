"""
Audit Protection Module

This module provides audit protection features for Pro tier users, including risk assessment,
document organization, compliance checks, and audit response assistance.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import login_required, current_user
from app.models import User, TaxForm, BusinessProfile
from app.access_control import requires_access_level
from datetime import datetime
import logging
import json
import os
from ai.openai_interface import get_openai_response

# Create blueprint
audit_bp = Blueprint("audit", __name__, url_prefix="/audit")

# Risk factors and their weights
AUDIT_RISK_FACTORS = {
    "schedule_c_losses": {
        "description": "Multiple years of Schedule C losses",
        "weight": 10,
        "threshold": 3  # Years
    },
    "home_office": {
        "description": "Home office deduction claimed",
        "weight": 5
    },
    "vehicle_deduction": {
        "description": "Vehicle deduction above typical range",
        "weight": 8,
        "threshold": 5000  # Dollar amount
    },
    "unreported_income": {
        "description": "Potential unreported income based on expense ratio",
        "weight": 15,
        "threshold": 0.8  # Expense/Income ratio
    },
    "cash_business": {
        "description": "Cash-intensive business",
        "weight": 12
    },
    "large_charitable_contributions": {
        "description": "Large charitable contributions relative to income",
        "weight": 7
    },
    "missing_documentation": {
        "description": "Incomplete or missing documentation",
        "weight": 20
    }
}

@audit_bp.route("/risk-assessment")
@login_required
@requires_access_level("audit_protection")
def risk_assessment():
    """Show audit risk assessment"""
    # Get business profile
    business_profile = BusinessProfile.query.filter_by(user_id=current_user.id).first()
    
    if not business_profile:
        flash("Please complete your business profile first.", "warning")
        return redirect(url_for("profile.business_profile"))
    
    # Calculate risk score
    risk_factors, total_score = calculate_risk_score(business_profile)
    
    # Get risk level and recommendations
    risk_level = get_risk_level(total_score)
    recommendations = get_risk_recommendations(risk_factors, business_profile)
    
    return render_template(
        "audit/risk_assessment.html",
        risk_factors=risk_factors,
        total_score=total_score,
        risk_level=risk_level,
        recommendations=recommendations
    )

@audit_bp.route("/document-organizer")
@login_required
@requires_access_level("audit_protection")
def document_organizer():
    """Document organization system for audit readiness"""
    # Get business profile
    business_profile = BusinessProfile.query.filter_by(user_id=current_user.id).first()
    
    if not business_profile:
        flash("Please complete your business profile first.", "warning")
        return redirect(url_for("profile.business_profile"))
    
    # Get document categories based on business type
    document_categories = get_document_categories(business_profile.business_type)
    
    # Get uploaded documents status
    document_status = get_document_status(current_user.id)
    
    return render_template(
        "audit/document_organizer.html",
        document_categories=document_categories,
        document_status=document_status
    )

@audit_bp.route("/compliance-check")
@login_required
@requires_access_level("audit_protection")
def compliance_check():
    """Run compliance checks on tax forms"""
    # Get all user tax forms
    tax_forms = TaxForm.query.filter_by(user_id=current_user.id).all()
    
    # Run compliance checks
    compliance_results = []
    for form in tax_forms:
        result = run_compliance_check(form)
        compliance_results.append({
            "form_id": form.id,
            "form_type": form.form_type.value,
            "tax_year": form.tax_year,
            "issues_found": len(result["issues"]),
            "compliance_score": result["compliance_score"],
            "issues": result["issues"]
        })
    
    return render_template(
        "audit/compliance_check.html",
        compliance_results=compliance_results
    )

@audit_bp.route("/audit-response/<int:form_id>")
@login_required
@requires_access_level("enhanced_audit_protection")
def audit_response(form_id):
    """Generate audit response assistance for a specific form"""
    tax_form = TaxForm.query.filter_by(id=form_id, user_id=current_user.id).first_or_404()
    
    # Generate audit response guidance
    response_guidance = generate_audit_response_guidance(tax_form)
    
    return render_template(
        "audit/response_guidance.html",
        tax_form=tax_form,
        response_guidance=response_guidance
    )

def calculate_risk_score(business_profile):
    """
    Calculate audit risk score based on business profile data
    
    Args:
        business_profile: BusinessProfile object
        
    Returns:
        Tuple of (triggered_risk_factors, total_risk_score)
    """
    triggered_factors = {}
    total_score = 0
    
    # Check for multiple years of reported losses
    if business_profile.reported_losses >= AUDIT_RISK_FACTORS["schedule_c_losses"]["threshold"]:
        triggered_factors["schedule_c_losses"] = {
            "description": AUDIT_RISK_FACTORS["schedule_c_losses"]["description"],
            "weight": AUDIT_RISK_FACTORS["schedule_c_losses"]["weight"],
            "value": f"{business_profile.reported_losses} years of losses"
        }
        total_score += AUDIT_RISK_FACTORS["schedule_c_losses"]["weight"]
    
    # Check for home office deduction
    if business_profile.has_home_office:
        triggered_factors["home_office"] = {
            "description": AUDIT_RISK_FACTORS["home_office"]["description"],
            "weight": AUDIT_RISK_FACTORS["home_office"]["weight"],
            "value": "Home office deduction claimed"
        }
        total_score += AUDIT_RISK_FACTORS["home_office"]["weight"]
    
    # Check for high vehicle deduction
    if business_profile.vehicle_deduction > AUDIT_RISK_FACTORS["vehicle_deduction"]["threshold"]:
        triggered_factors["vehicle_deduction"] = {
            "description": AUDIT_RISK_FACTORS["vehicle_deduction"]["description"],
            "weight": AUDIT_RISK_FACTORS["vehicle_deduction"]["weight"],
            "value": f"${business_profile.vehicle_deduction:,.2f} vehicle deduction"
        }
        total_score += AUDIT_RISK_FACTORS["vehicle_deduction"]["weight"]
    
    # Check for high expense ratio
    if business_profile.expense_ratio and business_profile.expense_ratio > AUDIT_RISK_FACTORS["unreported_income"]["threshold"]:
        triggered_factors["unreported_income"] = {
            "description": AUDIT_RISK_FACTORS["unreported_income"]["description"],
            "weight": AUDIT_RISK_FACTORS["unreported_income"]["weight"],
            "value": f"{business_profile.expense_ratio:.2%} expense ratio"
        }
        total_score += AUDIT_RISK_FACTORS["unreported_income"]["weight"]
    
    # Check for cash-intensive business
    if business_profile.high_cash_transactions:
        triggered_factors["cash_business"] = {
            "description": AUDIT_RISK_FACTORS["cash_business"]["description"],
            "weight": AUDIT_RISK_FACTORS["cash_business"]["weight"],
            "value": "Cash-intensive business reported"
        }
        total_score += AUDIT_RISK_FACTORS["cash_business"]["weight"]
    
    # Check for large charitable contributions
    if business_profile.large_charitable_contributions:
        triggered_factors["large_charitable_contributions"] = {
            "description": AUDIT_RISK_FACTORS["large_charitable_contributions"]["description"],
            "weight": AUDIT_RISK_FACTORS["large_charitable_contributions"]["weight"],
            "value": "Large charitable contributions reported"
        }
        total_score += AUDIT_RISK_FACTORS["large_charitable_contributions"]["weight"]
    
    # Check for missing documentation
    if business_profile.missing_receipts or business_profile.incomplete_records:
        triggered_factors["missing_documentation"] = {
            "description": AUDIT_RISK_FACTORS["missing_documentation"]["description"],
            "weight": AUDIT_RISK_FACTORS["missing_documentation"]["weight"],
            "value": "Missing receipts or incomplete records reported"
        }
        total_score += AUDIT_RISK_FACTORS["missing_documentation"]["weight"]
    
    return triggered_factors, total_score

def get_risk_level(risk_score):
    """
    Determine risk level based on risk score
    
    Args:
        risk_score: Numerical risk score
        
    Returns:
        Dictionary with risk level information
    """
    if risk_score <= 10:
        return {
            "level": "low",
            "description": "Low Risk",
            "color": "success",
            "message": "Your audit risk appears to be relatively low based on the information provided."
        }
    elif risk_score <= 30:
        return {
            "level": "moderate",
            "description": "Moderate Risk",
            "color": "warning",
            "message": "Your audit risk is moderate. Consider implementing the recommended safeguards."
        }
    else:
        return {
            "level": "high",
            "description": "High Risk",
            "color": "danger",
            "message": "Your audit risk is elevated. Immediate action is recommended to implement safeguards."
        }

def get_risk_recommendations(risk_factors, business_profile):
    """
    Generate risk mitigation recommendations based on triggered risk factors
    
    Args:
        risk_factors: Dictionary of triggered risk factors
        business_profile: BusinessProfile object
        
    Returns:
        List of recommendation dictionaries
    """
    recommendations = []
    
    # Schedule C losses recommendations
    if "schedule_c_losses" in risk_factors:
        recommendations.append({
            "title": "Document Business Purpose & Profit Motive",
            "description": "Multiple years of losses increase audit risk. Document your legitimate business purpose and profit motive with a formal business plan, marketing materials, and evidence of efforts to increase profitability.",
            "priority": "high"
        })
    
    # Home office recommendations
    if "home_office" in risk_factors:
        recommendations.append({
            "title": "Strengthen Home Office Documentation",
            "description": "Take photographs of your home office space, create a floor plan with measurements, and maintain a log of business activities conducted in the space.",
            "priority": "medium"
        })
    
    # Vehicle deduction recommendations
    if "vehicle_deduction" in risk_factors:
        recommendations.append({
            "title": "Improve Vehicle Usage Records",
            "description": "Maintain a detailed mileage log with dates, destinations, business purpose, and odometer readings. Consider using a mileage tracking app for real-time documentation.",
            "priority": "high"
        })
    
    # Expense ratio recommendations
    if "unreported_income" in risk_factors:
        recommendations.append({
            "title": "Reconcile Income vs. Expenses",
            "description": "Your expense-to-income ratio is unusually high. Ensure all income is properly reported and review expense categorization for accuracy.",
            "priority": "high"
        })
    
    # Cash business recommendations
    if "cash_business" in risk_factors:
        recommendations.append({
            "title": "Enhance Cash Transaction Documentation",
            "description": "Implement a point-of-sale system to track all transactions, make regular bank deposits, and maintain daily cash logs that reconcile with deposits.",
            "priority": "high"
        })
    
    # Missing documentation recommendations
    if "missing_documentation" in risk_factors:
        recommendations.append({
            "title": "Implement Document Management System",
            "description": "Set up a digital receipt management system, create a standard process for documenting all business transactions, and conduct quarterly reviews of documentation completeness.",
            "priority": "high"
        })
    
    return recommendations

def get_document_categories(business_type):
    """
    Get recommended document categories for audit preparedness based on business type
    
    Args:
        business_type: Business entity type
        
    Returns:
        Dictionary of document categories and their descriptions
    """
    # Base categories for all business types
    categories = {
        "income": {
            "name": "Income Documentation",
            "description": "Records that substantiate all reported income",
            "documents": [
                "Bank statements",
                "Payment processor records (PayPal, Stripe, etc.)",
                "Sales receipts and invoices",
                "1099 forms received"
            ]
        },
        "expenses": {
            "name": "Expense Documentation",
            "description": "Records that substantiate all claimed deductions",
            "documents": [
                "Receipts for business purchases",
                "Credit card statements",
                "Recurring expense documentation",
                "Asset purchase and depreciation records"
            ]
        },
        "tax_returns": {
            "name": "Tax Returns & Filings",
            "description": "Copies of all tax returns and related filings",
            "documents": [
                "Filed tax returns (3-7 years)",
                "Estimated tax payment records",
                "Extension requests",
                "Tax preparation documentation"
            ]
        },
        "banking": {
            "name": "Banking & Financial Records",
            "description": "Financial institution records related to the business",
            "documents": [
                "Business bank statements",
                "Loan documents",
                "Investment records",
                "Reconciliation reports"
            ]
        }
    }
    
    # Add business-type specific categories
    if business_type.value in ["s_corp", "c_corp"]:
        categories["corporate"] = {
            "name": "Corporate Records",
            "description": "Corporate governance and structure documentation",
            "documents": [
                "Articles of incorporation",
                "Bylaws",
                "Board meeting minutes",
                "Stock certificates and ledger"
            ]
        }
        
        categories["payroll"] = {
            "name": "Payroll Records",
            "description": "Documentation of employee compensation",
            "documents": [
                "Payroll reports",
                "W-2 and W-3 forms",
                "941 quarterly filings",
                "State employment filings"
            ]
        }
    
    if business_type.value == "llc":
        categories["entity"] = {
            "name": "LLC Records",
            "description": "LLC formation and governance documentation",
            "documents": [
                "Articles of organization",
                "Operating agreement",
                "Member meeting minutes",
                "State filings"
            ]
        }
    
    return categories

def get_document_status(user_id):
    """
    Get document upload status for a user
    
    Args:
        user_id: User ID
        
    Returns:
        Dictionary of document status by category
    """
    # This would typically query a document storage system
    # For now, we'll return a sample status
    return {
        "income": {
            "total": 4,
            "uploaded": 2,
            "status": "in_progress"
        },
        "expenses": {
            "total": 4, 
            "uploaded": 4,
            "status": "complete"
        },
        "tax_returns": {
            "total": 4,
            "uploaded": 3,
            "status": "in_progress"
        },
        "banking": {
            "total": 4,
            "uploaded": 0,
            "status": "not_started"
        }
    }

def run_compliance_check(tax_form):
    """
    Run automated compliance checks on a tax form
    
    Args:
        tax_form: TaxForm object
        
    Returns:
        Dictionary with compliance check results
    """
    issues = []
    
    # This would contain actual logic to validate form data against IRS rules
    # For now, we'll return sample issues based on the form type
    
    if tax_form.form_type.value == "schedule_c":
        # Check for Schedule C specific issues
        form_data = tax_form.data
        
        # Example check: Missing business code
        if not form_data.get("business_code"):
            issues.append({
                "field": "business_code",
                "severity": "high",
                "description": "Missing principal business code",
                "recommendation": "Enter the 6-digit code that best describes your business from the IRS list"
            })
        
        # Example check: Home office without exclusive use
        if form_data.get("home_office_deduction") and not form_data.get("exclusive_use"):
            issues.append({
                "field": "exclusive_use",
                "severity": "high",
                "description": "Home office deduction claimed without exclusive use",
                "recommendation": "Home office must be used exclusively for business purposes to qualify"
            })
    
    elif tax_form.form_type.value == "schedule_se":
        # Check for Schedule SE specific issues
        form_data = tax_form.data
        
        # Example check: SE tax calculation error
        if form_data.get("self_employment_income", 0) > 400 and not form_data.get("self_employment_tax"):
            issues.append({
                "field": "self_employment_tax",
                "severity": "high",
                "description": "Self-employment tax not calculated for income over $400",
                "recommendation": "Calculate and report self-employment tax for all SE income over $400"
            })
    
    # Calculate compliance score based on issues found
    compliance_score = 100 - (len(issues) * 10)
    compliance_score = max(0, min(100, compliance_score))
    
    return {
        "issues": issues,
        "compliance_score": compliance_score
    }

def generate_audit_response_guidance(tax_form):
    """
    Generate AI-assisted audit response guidance for a specific form
    
    Args:
        tax_form: TaxForm object
        
    Returns:
        Dictionary with response guidance
    """
    # This would use OpenAI to generate tailored audit response guidance
    # For now, we'll return sample guidance based on the form type
    
    form_type_name = tax_form.form_type.value.replace("_", " ").title()
    
    system_message = f"""
    You are an AI tax assistant helping a business owner prepare for a potential IRS audit.
    Provide clear, concise guidance on how to respond to an audit notice regarding their {form_type_name} for tax year {tax_form.tax_year}.
    Focus on documentation requirements, common audit triggers, and best practices for communication with the IRS.
    Format your response with clear sections and bullet points when appropriate.
    """
    
    user_message = f"""
    Generate audit response guidance for a {form_type_name} that includes:
    1. Initial steps upon receiving an audit notice
    2. Required documentation to gather
    3. How to organize the documentation
    4. Communication strategies when dealing with an auditor
    5. Common pitfalls to avoid
    
    Form details:
    - Tax year: {tax_form.tax_year}
    - Status: {tax_form.status}
    """
    
    try:
        response_text = get_openai_response(system_message, user_message)
        
        # Parse response sections (in a safer way to avoid index errors)
        sections = []
        
        # Helper function to safely extract sections
        def extract_section(text, start_phrase, end_phrase=None):
            if start_phrase not in text:
                return "Information not available"
            
            parts = text.split(start_phrase, 1)
            if len(parts) < 2:
                return "Information not available"
                
            content = parts[1]
            
            if end_phrase and end_phrase in content:
                content = content.split(end_phrase, 1)[0]
                
            return content.strip()
        
        # Extract each section
        sections = [
            {
                "title": "Initial Steps Upon Receiving an Audit Notice",
                "content": extract_section(response_text, "Initial Steps", "Required Documentation")
            },
            {
                "title": "Required Documentation",
                "content": extract_section(response_text, "Required Documentation", "Organizing Your Documentation")
            },
            {
                "title": "Organizing Your Documentation",
                "content": extract_section(response_text, "Organizing Your Documentation", "Communication Strategies")
            },
            {
                "title": "Communication Strategies",
                "content": extract_section(response_text, "Communication Strategies", "Common Pitfalls")
            },
            {
                "title": "Common Pitfalls to Avoid",
                "content": extract_section(response_text, "Common Pitfalls")
            }
        ]
    except:
        # Fallback if OpenAI call or parsing fails
        sections = [
            {
                "title": "Initial Steps Upon Receiving an Audit Notice",
                "content": "Review the audit notice carefully to understand the scope and timeline. Contact .fylr support for guidance with your Pro tier protection."
            },
            {
                "title": "Required Documentation",
                "content": "Gather all relevant income and expense documentation, bank statements, and prior year returns."
            },
            {
                "title": "Organizing Your Documentation",
                "content": "Use our document organizer system to categorize all documents by type and ensure completeness."
            },
            {
                "title": "Communication Strategies",
                "content": "Respond promptly, be professional, and only answer the specific questions asked. Consider representation."
            },
            {
                "title": "Common Pitfalls to Avoid",
                "content": "Don't provide more information than requested. Don't recreate or fabricate missing documentation."
            }
        ]
    
    return {
        "form_type": form_type_name,
        "tax_year": tax_form.tax_year,
        "sections": sections,
        "disclaimer": "This guidance is provided for informational purposes only and does not constitute legal or tax advice. We recommend consulting with a qualified tax professional for specific audit situations."
    }