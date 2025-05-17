"""
Main application routes
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

# Create blueprint
main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    """Home page route"""
    return render_template("index.html")

@main_bp.route("/dashboard")
@login_required
def dashboard():
    """User dashboard route"""
    return render_template("dashboard.html")

@main_bp.route("/profile")
@login_required
def profile():
    """User profile route"""
    return render_template("profile.html")

@main_bp.route("/plans")
def plans():
    """Pricing plans route"""
    from app.pricing import TIERS, BUSINESS_TYPES, AUDIT_PROTECTION
    return render_template(
        "pricing.html",
        tiers=TIERS, 
        business_types=BUSINESS_TYPES,
        audit_protection=AUDIT_PROTECTION
    )