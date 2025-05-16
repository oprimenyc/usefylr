"""
Accounting Software Integration Module

This module provides integration with popular accounting software platforms
to import financial data for tax preparation.
"""

from flask import Blueprint, render_template, flash, redirect, url_for, request, abort, jsonify, session
from flask_login import login_required, current_user
from app.app import db
from app.models import User, TaxForm, AuditLog
from app.access_control import requires_access_level
import json
import os
import requests
from datetime import datetime, timedelta
import base64
import hmac
import hashlib
import time
import urllib.parse

# Create blueprint
accounting_bp = Blueprint('accounting', __name__, url_prefix='/accounting')

# Supported accounting platforms
SUPPORTED_PLATFORMS = {
    'quickbooks': {
        'name': 'QuickBooks Online',
        'logo': 'quickbooks_logo.png',
        'description': 'Import data from QuickBooks Online',
        'auth_type': 'oauth2',
        'features': ['chart_of_accounts', 'income_statement', 'balance_sheet', 'general_ledger', 'tax_documents']
    },
    'xero': {
        'name': 'Xero',
        'logo': 'xero_logo.png',
        'description': 'Import data from Xero',
        'auth_type': 'oauth2',
        'features': ['chart_of_accounts', 'income_statement', 'balance_sheet', 'general_ledger']
    },
    'wave': {
        'name': 'Wave Accounting',
        'logo': 'wave_logo.png',
        'description': 'Import data from Wave Accounting',
        'auth_type': 'api_key',
        'features': ['income_statement', 'balance_sheet', 'tax_documents']
    },
    'freshbooks': {
        'name': 'FreshBooks',
        'logo': 'freshbooks_logo.png',
        'description': 'Import data from FreshBooks',
        'auth_type': 'oauth2',
        'features': ['income_statement', 'balance_sheet', 'tax_documents']
    }
}

@accounting_bp.route('/')
@login_required
@requires_access_level('fylr_plus')
def index():
    """Display the accounting integration home page"""
    # Get user's connected accounting platforms
    connected_platforms = get_connected_platforms(current_user.id)
    
    return render_template('accounting/index.html',
                          platforms=SUPPORTED_PLATFORMS,
                          connected_platforms=connected_platforms)

@accounting_bp.route('/connect/<platform>')
@login_required
@requires_access_level('fylr_plus')
def connect_platform(platform):
    """Start the connection process for an accounting platform"""
    if platform not in SUPPORTED_PLATFORMS:
        flash(f"Unsupported accounting platform: {platform}", 'danger')
        return redirect(url_for('accounting.index'))
    
    platform_info = SUPPORTED_PLATFORMS[platform]
    
    # Store platform in session for callback
    session['connecting_platform'] = platform
    
    if platform_info['auth_type'] == 'oauth2':
        # Generate authorization URL based on the platform
        if platform == 'quickbooks':
            auth_url = generate_quickbooks_auth_url()
        elif platform == 'xero':
            auth_url = generate_xero_auth_url()
        elif platform == 'freshbooks':
            auth_url = generate_freshbooks_auth_url()
        else:
            flash(f"OAuth2 not configured for {platform_info['name']}", 'danger')
            return redirect(url_for('accounting.index'))
        
        return redirect(auth_url)
    elif platform_info['auth_type'] == 'api_key':
        # Redirect to API key entry page
        return render_template('accounting/api_key_entry.html',
                              platform=platform,
                              platform_info=platform_info)
    else:
        flash(f"Unsupported authentication type for {platform_info['name']}", 'danger')
        return redirect(url_for('accounting.index'))

@accounting_bp.route('/callback')
@login_required
@requires_access_level('fylr_plus')
def oauth_callback():
    """Handle OAuth callback from accounting platforms"""
    platform = session.get('connecting_platform')
    if not platform:
        flash("Invalid callback request", 'danger')
        return redirect(url_for('accounting.index'))
    
    # Clear the session variable
    session.pop('connecting_platform', None)
    
    # Get authorization code
    code = request.args.get('code')
    if not code:
        flash("Authorization failed", 'danger')
        return redirect(url_for('accounting.index'))
    
    # Exchange code for access token based on the platform
    if platform == 'quickbooks':
        success = exchange_quickbooks_code(code, current_user.id)
    elif platform == 'xero':
        success = exchange_xero_code(code, current_user.id)
    elif platform == 'freshbooks':
        success = exchange_freshbooks_code(code, current_user.id)
    else:
        flash(f"OAuth2 exchange not configured for {platform}", 'danger')
        return redirect(url_for('accounting.index'))
    
    if success:
        flash(f"Successfully connected to {SUPPORTED_PLATFORMS[platform]['name']}", 'success')
    else:
        flash(f"Failed to connect to {SUPPORTED_PLATFORMS[platform]['name']}", 'danger')
    
    return redirect(url_for('accounting.index'))

@accounting_bp.route('/disconnect/<platform>')
@login_required
@requires_access_level('fylr_plus')
def disconnect_platform(platform):
    """Disconnect an accounting platform"""
    if platform not in SUPPORTED_PLATFORMS:
        flash(f"Unsupported accounting platform: {platform}", 'danger')
        return redirect(url_for('accounting.index'))
    
    # Remove connection from database
    success = remove_platform_connection(platform, current_user.id)
    
    if success:
        flash(f"Successfully disconnected from {SUPPORTED_PLATFORMS[platform]['name']}", 'success')
    else:
        flash(f"Failed to disconnect from {SUPPORTED_PLATFORMS[platform]['name']}", 'danger')
    
    return redirect(url_for('accounting.index'))

@accounting_bp.route('/api-key/<platform>', methods=['POST'])
@login_required
@requires_access_level('fylr_plus')
def save_api_key(platform):
    """Save API key for platforms that use API key authentication"""
    if platform not in SUPPORTED_PLATFORMS:
        flash(f"Unsupported accounting platform: {platform}", 'danger')
        return redirect(url_for('accounting.index'))
    
    platform_info = SUPPORTED_PLATFORMS[platform]
    if platform_info['auth_type'] != 'api_key':
        flash(f"{platform_info['name']} does not use API key authentication", 'danger')
        return redirect(url_for('accounting.index'))
    
    # Get API key from form
    api_key = request.form.get('api_key')
    if not api_key:
        flash("API key is required", 'danger')
        return redirect(url_for('accounting.connect_platform', platform=platform))
    
    # Save API key to database
    success = save_platform_api_key(platform, api_key, current_user.id)
    
    if success:
        flash(f"Successfully connected to {platform_info['name']}", 'success')
    else:
        flash(f"Failed to connect to {platform_info['name']}", 'danger')
    
    return redirect(url_for('accounting.index'))

@accounting_bp.route('/import/<platform>')
@login_required
@requires_access_level('fylr_plus')
def import_data(platform):
    """Select data to import from an accounting platform"""
    if platform not in SUPPORTED_PLATFORMS:
        flash(f"Unsupported accounting platform: {platform}", 'danger')
        return redirect(url_for('accounting.index'))
    
    # Check if the platform is connected
    connected = check_platform_connected(platform, current_user.id)
    if not connected:
        flash(f"You are not connected to {SUPPORTED_PLATFORMS[platform]['name']}", 'danger')
        return redirect(url_for('accounting.index'))
    
    # Get available data for import
    available_data = get_importable_data(platform, current_user.id)
    
    return render_template('accounting/import.html',
                          platform=platform,
                          platform_info=SUPPORTED_PLATFORMS[platform],
                          available_data=available_data)

@accounting_bp.route('/import/<platform>/execute', methods=['POST'])
@login_required
@requires_access_level('fylr_plus')
def execute_import(platform):
    """Execute data import from an accounting platform"""
    if platform not in SUPPORTED_PLATFORMS:
        flash(f"Unsupported accounting platform: {platform}", 'danger')
        return redirect(url_for('accounting.index'))
    
    # Check if the platform is connected
    connected = check_platform_connected(platform, current_user.id)
    if not connected:
        flash(f"You are not connected to {SUPPORTED_PLATFORMS[platform]['name']}", 'danger')
        return redirect(url_for('accounting.index'))
    
    # Get selected data types from form
    data_types = request.form.getlist('data_types')
    if not data_types:
        flash("No data types selected for import", 'warning')
        return redirect(url_for('accounting.import_data', platform=platform))
    
    # Get tax year from form
    tax_year = request.form.get('tax_year', datetime.now().year, type=int)
    
    # Execute import for each selected data type
    import_results = {}
    for data_type in data_types:
        result = import_platform_data(platform, data_type, tax_year, current_user.id)
        import_results[data_type] = result
    
    # Log the import action
    log_entry = AuditLog(
        user_id=current_user.id,
        action=f"Imported data from {SUPPORTED_PLATFORMS[platform]['name']}",
        details=f"Data types: {', '.join(data_types)}",
        ip_address=request.remote_addr
    )
    db.session.add(log_entry)
    db.session.commit()
    
    # Redirect to import results page
    return render_template('accounting/import_results.html',
                          platform=platform,
                          platform_info=SUPPORTED_PLATFORMS[platform],
                          import_results=import_results,
                          tax_year=tax_year)

@accounting_bp.route('/data/<platform>')
@login_required
@requires_access_level('fylr_plus')
def view_imported_data(platform):
    """View previously imported data from an accounting platform"""
    if platform not in SUPPORTED_PLATFORMS:
        flash(f"Unsupported accounting platform: {platform}", 'danger')
        return redirect(url_for('accounting.index'))
    
    # Get imported data for the platform
    tax_year = request.args.get('tax_year', datetime.now().year, type=int)
    imported_data = get_imported_data(platform, tax_year, current_user.id)
    
    return render_template('accounting/view_data.html',
                          platform=platform,
                          platform_info=SUPPORTED_PLATFORMS[platform],
                          imported_data=imported_data,
                          tax_year=tax_year)

# Helper functions for QuickBooks integration
def generate_quickbooks_auth_url():
    """Generate authorization URL for QuickBooks"""
    # Replace with actual QuickBooks OAuth2 parameters
    client_id = os.environ.get("QUICKBOOKS_CLIENT_ID")
    redirect_uri = os.environ.get("QUICKBOOKS_REDIRECT_URI")
    
    if not client_id or not redirect_uri:
        raise ValueError("QuickBooks OAuth2 credentials not configured")
    
    # Construct authorization URL
    base_url = "https://appcenter.intuit.com/connect/oauth2"
    params = {
        "client_id": client_id,
        "response_type": "code",
        "scope": "com.intuit.quickbooks.accounting",
        "redirect_uri": redirect_uri,
        "state": "quickbooks"  # For identifying callback
    }
    
    auth_url = f"{base_url}?{urllib.parse.urlencode(params)}"
    return auth_url

def exchange_quickbooks_code(code, user_id):
    """Exchange authorization code for QuickBooks access token"""
    # Replace with actual QuickBooks OAuth2 parameters
    client_id = os.environ.get("QUICKBOOKS_CLIENT_ID")
    client_secret = os.environ.get("QUICKBOOKS_CLIENT_SECRET")
    redirect_uri = os.environ.get("QUICKBOOKS_REDIRECT_URI")
    
    if not client_id or not client_secret or not redirect_uri:
        raise ValueError("QuickBooks OAuth2 credentials not configured")
    
    # Exchange authorization code for tokens
    token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri
    }
    
    # In a real implementation, you would make this request
    # For the prototype, we'll simulate success
    # response = requests.post(token_url, auth=(client_id, client_secret), data=payload)
    
    # Simulated response data
    token_data = {
        "access_token": "simulated_access_token",
        "refresh_token": "simulated_refresh_token",
        "expires_in": 3600
    }
    
    # Save token data to database
    save_platform_connection(
        platform="quickbooks",
        user_id=user_id,
        token_data=token_data
    )
    
    return True

# Helper functions for database operations
def get_connected_platforms(user_id):
    """Get list of connected accounting platforms for a user"""
    # In a real implementation, this would query the database
    # For the prototype, we'll return a simulated result
    return [
        {
            'platform': 'quickbooks',
            'connected_at': datetime.now() - timedelta(days=7),
            'last_import': datetime.now() - timedelta(days=3)
        }
    ]

def check_platform_connected(platform, user_id):
    """Check if a platform is connected for a user"""
    # In a real implementation, this would query the database
    # For the prototype, we'll return a simulated result
    return platform == 'quickbooks'  # Only QuickBooks is "connected" for the prototype

def save_platform_connection(platform, user_id, token_data):
    """Save platform connection data to database"""
    # In a real implementation, this would save to the database
    # For the prototype, we'll simulate success
    return True

def remove_platform_connection(platform, user_id):
    """Remove platform connection from database"""
    # In a real implementation, this would remove from the database
    # For the prototype, we'll simulate success
    return True

def save_platform_api_key(platform, api_key, user_id):
    """Save API key for a platform"""
    # In a real implementation, this would save to the database
    # For the prototype, we'll simulate success
    return True

def get_importable_data(platform, user_id):
    """Get list of data that can be imported from a platform"""
    # In a real implementation, this would query the platform API
    # For the prototype, we'll return simulated data
    if platform == 'quickbooks':
        return [
            {
                'type': 'chart_of_accounts',
                'name': 'Chart of Accounts',
                'description': 'List of all accounts',
                'last_updated': datetime.now() - timedelta(days=7)
            },
            {
                'type': 'income_statement',
                'name': 'Income Statement (Profit & Loss)',
                'description': 'Revenue and expenses for the period',
                'last_updated': datetime.now() - timedelta(days=7)
            },
            {
                'type': 'balance_sheet',
                'name': 'Balance Sheet',
                'description': 'Assets, liabilities, and equity',
                'last_updated': datetime.now() - timedelta(days=7)
            },
            {
                'type': 'general_ledger',
                'name': 'General Ledger',
                'description': 'Detailed transaction history',
                'last_updated': datetime.now() - timedelta(days=7)
            },
            {
                'type': 'tax_documents',
                'name': 'Tax Documents',
                'description': '1099s, W-2s, and other tax forms',
                'last_updated': datetime.now() - timedelta(days=7)
            }
        ]
    elif platform == 'xero':
        return [
            {
                'type': 'chart_of_accounts',
                'name': 'Chart of Accounts',
                'description': 'List of all accounts',
                'last_updated': datetime.now() - timedelta(days=7)
            },
            {
                'type': 'income_statement',
                'name': 'Income Statement (Profit & Loss)',
                'description': 'Revenue and expenses for the period',
                'last_updated': datetime.now() - timedelta(days=7)
            },
            {
                'type': 'balance_sheet',
                'name': 'Balance Sheet',
                'description': 'Assets, liabilities, and equity',
                'last_updated': datetime.now() - timedelta(days=7)
            },
            {
                'type': 'general_ledger',
                'name': 'General Ledger',
                'description': 'Detailed transaction history',
                'last_updated': datetime.now() - timedelta(days=7)
            }
        ]
    else:
        return []

def import_platform_data(platform, data_type, tax_year, user_id):
    """Import data from a platform"""
    # In a real implementation, this would query the platform API
    # For the prototype, we'll simulate success
    return {
        'success': True,
        'records_imported': 127,
        'import_date': datetime.now(),
        'notes': f"Successfully imported {data_type} data from {platform} for tax year {tax_year}"
    }

def get_imported_data(platform, tax_year, user_id):
    """Get previously imported data from a platform"""
    # In a real implementation, this would query the database
    # For the prototype, we'll return simulated data
    if platform == 'quickbooks':
        return {
            'income_statement': {
                'revenue': {
                    'product_sales': 458750.25,
                    'service_revenue': 287300.00,
                    'other_income': 15200.75,
                    'total_revenue': 761251.00
                },
                'expenses': {
                    'cost_of_goods_sold': 225400.50,
                    'salaries_and_wages': 187300.00,
                    'rent': 48000.00,
                    'utilities': 12450.75,
                    'insurance': 24500.00,
                    'marketing_and_advertising': 35000.00,
                    'professional_fees': 42000.00,
                    'office_supplies': 8750.25,
                    'other_expenses': 22500.00,
                    'total_expenses': 605901.50
                },
                'net_income': 155349.50
            },
            'balance_sheet': {
                'assets': {
                    'cash_and_equivalents': 125000.00,
                    'accounts_receivable': 87500.00,
                    'inventory': 95000.00,
                    'fixed_assets': 275000.00,
                    'total_assets': 582500.00
                },
                'liabilities': {
                    'accounts_payable': 45000.00,
                    'loans_payable': 150000.00,
                    'total_liabilities': 195000.00
                },
                'equity': {
                    'owner_equity': 232150.50,
                    'retained_earnings': 155349.50,
                    'total_equity': 387500.00
                }
            },
            'import_date': datetime.now() - timedelta(days=3),
            'tax_year': tax_year
        }
    else:
        return {}