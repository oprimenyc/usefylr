from functools import wraps
from flask import redirect, url_for, flash, request, abort
from flask_login import current_user

def requires_access_level(access_level):
    """
    Decorator for views that checks if the user has the required access level
    
    Access levels:
    - full_access: Business Builder plan users
    - discounted: Subscription members
    - standard: Regular users
    
    Features can also be passed directly:
    - basic_diy
    - guided_filing
    - strategy_unlock
    - irs_letter_pack
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # If user is not logged in, redirect to login page
            if not current_user.is_authenticated:
                flash('Please log in to access this feature.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            # Check access level
            if access_level == 'full_access':
                # Only business builder plan users have full access
                if current_user.get_access_level() != 'full_access':
                    flash('This feature requires a Business Builder plan.', 'danger')
                    return redirect(url_for('main.pricing'))
            elif access_level == 'discounted':
                # Only subscription members or business builder plan users
                if current_user.get_access_level() not in ['discounted', 'full_access']:
                    flash('This feature requires a subscription.', 'danger')
                    return redirect(url_for('main.pricing'))
            elif access_level in ['basic_diy', 'guided_filing', 'strategy_unlock', 'irs_letter_pack']:
                # Check if user has paid for the specific feature
                if not unlock_tool(current_user, access_level):
                    flash(f'You need to purchase {access_level.replace("_", " ").title()} to access this feature.', 'danger')
                    return redirect(url_for('main.pricing'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def unlock_tool(user, tool_name):
    """Check if a user has access to a specific tool"""
    # Business Builder plan users have access to all tools
    if user.get_access_level() == 'full_access':
        return True
    
    # Subscription members get 50% off
    if user.get_access_level() == 'discounted':
        return user.has_paid(tool_name, discounted=True)
    
    # Standard users pay full price
    return user.has_paid(tool_name)