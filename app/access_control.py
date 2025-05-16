from functools import wraps
from flask import redirect, url_for, flash, current_app
from flask_login import current_user


def requires_legal_acknowledgment(f):
    """
    Decorator that checks if the user has acknowledged the legal disclaimer.
    If not, redirects them to the disclaimer page.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user has acknowledged legal disclaimer
        if not current_user.has_acknowledged_disclaimer:
            flash('You must acknowledge the legal disclaimer before accessing this feature.', 'warning')
            return redirect(url_for('main.legal_disclaimer'))
        return f(*args, **kwargs)
    return decorated_function


def requires_access_level(access_level):
    """
    Decorator for views that checks if the user has the required access level
    
    Access levels:
    - pro: .fylr Pro plan users
    - plus: .fylr+ plan users
    - basic: Basic plan users
    
    Features can also be passed directly:
    - guided_input
    - auto_fill
    - save_progress
    - smart_form_logic
    - enhanced_ai_support
    - ai_deduction_detection
    - audit_protection
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # If user doesn't have required access, redirect to pricing page
            if not current_user.has_paid(access_level):
                flash(f'You need to upgrade your plan to access this feature.', 'warning')
                return redirect(url_for('main.pricing'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def unlock_tool(user, tool_name):
    """Check if a user has access to a specific tool"""
    return user.has_paid(tool_name)