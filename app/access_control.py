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
    - guided_input: Basic tier - AI-guided data input
    - auto_fill: Basic tier - Auto-populate IRS form fields
    - form_generation: Basic tier - Generate IRS documents
    - pdf_export: Basic tier - Export PDF files
    - educational_guidance: Basic tier - Optional tooltips
    
    - save_progress: Plus tier - Save and resume work
    - smart_form_logic: Plus tier - Smart form field guidance
    - enhanced_ai_support: Plus tier - Advanced AI explanations
    - dynamic_checklist: Plus tier - AI-generated task lists
    - export_forms: Plus tier - Export clean, ready-to-file forms
    
    - ai_deduction_detection: Pro tier - AI-enhanced deduction finder
    - ai_sorted_uploads: Pro tier - AI organization of document uploads
    - filing_export_support: Pro tier - Enhanced export features
    - audit_protection: Pro tier - Basic audit risk reduction
    - enhanced_audit_protection: Pro tier - Advanced audit protection
    - priority_support: Pro tier - Priority support access
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # If user doesn't have required access, show appropriate message
            if not current_user.has_feature(access_level):
                # Determine required tier
                required_tier = "Basic"
                upgrade_price = "$0"
                
                if access_level in ['save_progress', 'smart_form_logic', 'enhanced_ai_support',
                                  'dynamic_checklist', 'export_forms', 'plus', 'fylr_plus']:
                    required_tier = ".fylr+"
                    upgrade_price = "$197"
                elif access_level in ['ai_deduction_detection', 'ai_sorted_uploads', 
                                    'filing_export_support', 'audit_protection', 
                                    'enhanced_audit_protection', 'priority_support', 
                                    'pro', 'fylr_pro']:
                    required_tier = ".fylr Pro"
                    upgrade_price = "$97-$197"
                
                # Custom message for different feature types
                feature_name = access_level.replace('_', ' ').title()
                
                flash(f'The {feature_name} feature requires a {required_tier} plan '
                      f'(starting at {upgrade_price}). Please upgrade to access this feature.', 'warning')
                      
                return redirect(url_for('main.pricing'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def unlock_tool(user, tool_name):
    """
    Check if a user has access to a specific tool and return info about access
    
    Args:
        user: The User object to check
        tool_name: The feature or tool to check access for
        
    Returns:
        dict: {
            'has_access': bool - Whether user has access,
            'required_tier': str - Required tier name for access,
            'upgrade_price': str - Starting price for the required tier,
            'feature_description': str - Description of the feature
        }
    """
    # Check if user has access first
    has_access = user.has_feature(tool_name)
    
    # Default values
    required_tier = "Basic"
    upgrade_price = "$0"
    feature_description = "Standard functionality"
    
    # Feature descriptions
    feature_descriptions = {
        # Basic tier features
        'guided_input': "AI-guided data input assistance",
        'auto_fill': "Automatic field population based on provided information",
        'form_generation': "Generate IRS-compatible documents",
        'pdf_export': "Export documents as PDF files",
        'educational_guidance': "Educational tooltips and guidance",
        
        # Plus tier features
        'save_progress': "Save your work and continue later",
        'resume_progress': "Resume previously saved work",
        'smart_form_logic': "Intelligent form field guidance and suggestions",
        'enhanced_ai_support': "Advanced AI explanations for tax concepts",
        'dynamic_checklist': "AI-generated task lists based on your business",
        'export_forms': "Export clean, ready-to-file forms",
        
        # Pro tier features
        'ai_deduction_detection': "AI-enhanced detection of potential deductions",
        'ai_sorted_uploads': "AI categorization and organization of document uploads",
        'filing_export_support': "Enhanced export features with filing assistance",
        'audit_protection': "Basic audit risk reduction features",
        'enhanced_audit_protection': "Advanced audit protection and preparation",
        'priority_support': "Priority support access"
    }
    
    # Determine required tier for the feature
    plus_features = ['save_progress', 'resume_progress', 'smart_form_logic', 
                    'enhanced_ai_support', 'dynamic_checklist', 'export_forms',
                    'plus', 'fylr_plus']
                    
    pro_features = ['ai_deduction_detection', 'ai_sorted_uploads', 
                   'filing_export_support', 'audit_protection', 
                   'enhanced_audit_protection', 'priority_support',
                   'pro', 'fylr_pro']
    
    if tool_name in plus_features:
        required_tier = ".fylr+"
        upgrade_price = "$197"
    elif tool_name in pro_features:
        required_tier = ".fylr Pro"
        upgrade_price = "$97-$197"
    
    # Get feature description
    if tool_name in feature_descriptions:
        feature_description = feature_descriptions[tool_name]
    else:
        # Generate a description for tier levels
        if tool_name in ['basic', 'basic_tier']:
            feature_description = "Basic tier access with essential features"
        elif tool_name in ['plus', 'fylr_plus', 'plus_tier']:
            feature_description = ".fylr+ tier with advanced features and time-saving tools"
        elif tool_name in ['pro', 'fylr_pro', 'pro_tier']:
            feature_description = ".fylr Pro tier with premium features and maximum automation"
    
    return {
        'has_access': has_access,
        'required_tier': required_tier,
        'upgrade_price': upgrade_price,
        'feature_description': feature_description
    }