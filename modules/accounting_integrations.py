"""
Accounting Software Integration Module

This module provides integration with popular accounting platforms including:
- QuickBooks Online
- Xero
- FreshBooks
- Wave
- MYOB
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import login_required, current_user
from app.app import db
from app.models import User, TaxForm, TaxStrategy, UserPlan
from app.access_control import requires_access_level
import os
import json
import requests
from datetime import datetime, timedelta
import logging
import base64
import hmac
import hashlib
import time
import urllib.parse

# Create blueprint
accounting_bp = Blueprint('accounting', __name__, url_prefix='/accounting')

# Dictionary of supported platforms and their configurations
ACCOUNTING_PLATFORMS = {
    'quickbooks': {
        'name': 'QuickBooks Online',
        'icon': 'quickbooks_logo.png',
        'description': 'Connect to your QuickBooks Online account to import transactions, accounts, and reports.',
        'auth_type': 'oauth2',
        'data_types': ['chart_of_accounts', 'profit_loss', 'balance_sheet', 'tax_summary', 'transactions']
    },
    'xero': {
        'name': 'Xero',
        'icon': 'xero_logo.png',
        'description': 'Connect to your Xero account to import financial data for tax preparation.',
        'auth_type': 'oauth2',
        'data_types': ['chart_of_accounts', 'profit_loss', 'balance_sheet', 'tax_summary', 'transactions']
    },
    'freshbooks': {
        'name': 'FreshBooks',
        'icon': 'freshbooks_logo.png',
        'description': 'Import your FreshBooks data for seamless tax preparation.',
        'auth_type': 'oauth2',
        'data_types': ['profit_loss', 'balance_sheet', 'tax_summary', 'expenses']
    },
    'wave': {
        'name': 'Wave',
        'icon': 'wave_logo.png',
        'description': 'Connect to your Wave account to import financial statements and transactions.',
        'auth_type': 'oauth2',
        'data_types': ['profit_loss', 'balance_sheet', 'transactions']
    },
    'myob': {
        'name': 'MYOB',
        'icon': 'myob_logo.png',
        'description': 'Import your MYOB accounting data for tax preparation and analysis.',
        'auth_type': 'oauth2',
        'data_types': ['profit_loss', 'balance_sheet', 'tax_summary']
    }
}

@accounting_bp.route('/')
@login_required
@requires_access_level('fylr_plus')
def index():
    """Display the accounting integration dashboard"""
    # Get user's connected accounts
    connected_accounts = get_user_connected_accounts(current_user.id)
    
    # Get recent imports
    recent_imports = get_recent_imports(current_user.id)
    
    return render_template('accounting/index.html',
                          platforms=ACCOUNTING_PLATFORMS,
                          connected_accounts=connected_accounts,
                          recent_imports=recent_imports)

@accounting_bp.route('/connect/<platform>')
@login_required
@requires_access_level('fylr_plus')
def connect_platform(platform):
    """Initialize connection to an accounting platform"""
    if platform not in ACCOUNTING_PLATFORMS:
        flash(f"Unsupported platform: {platform}", "danger")
        return redirect(url_for('accounting.index'))
    
    platform_info = ACCOUNTING_PLATFORMS[platform]
    
    # Store the platform name in session for callback
    session['connecting_platform'] = platform
    
    if platform_info['auth_type'] == 'oauth2':
        # Handle OAuth2 flow based on the platform
        auth_url = None
        
        if platform == 'quickbooks':
            auth_url = get_quickbooks_auth_url()
        elif platform == 'xero':
            auth_url = get_xero_auth_url()
        elif platform == 'freshbooks':
            auth_url = get_freshbooks_auth_url()
        elif platform == 'wave':
            auth_url = get_wave_auth_url()
        elif platform == 'myob':
            auth_url = get_myob_auth_url()
        
        if auth_url:
            return redirect(auth_url)
        else:
            flash(f"Error generating authorization URL for {platform_info['name']}", "danger")
            return redirect(url_for('accounting.index'))
    else:
        flash(f"Unsupported authentication type for {platform_info['name']}", "danger")
        return redirect(url_for('accounting.index'))

@accounting_bp.route('/callback')
@login_required
@requires_access_level('fylr_plus')
def oauth_callback():
    """Handle OAuth callbacks from accounting platforms"""
    platform = session.get('connecting_platform')
    if not platform:
        flash("Invalid callback - no platform specified", "danger")
        return redirect(url_for('accounting.index'))
    
    # Clear from session
    session.pop('connecting_platform', None)
    
    # Get authorization code
    code = request.args.get('code')
    if not code:
        flash("Authorization failed - no code received", "danger")
        return redirect(url_for('accounting.index'))
    
    # Exchange code for access token based on platform
    success = False
    if platform == 'quickbooks':
        success = exchange_quickbooks_code(code, current_user.id)
    elif platform == 'xero':
        success = exchange_xero_code(code, current_user.id)
    elif platform == 'freshbooks':
        success = exchange_freshbooks_code(code, current_user.id)
    elif platform == 'wave':
        success = exchange_wave_code(code, current_user.id)
    elif platform == 'myob':
        success = exchange_myob_code(code, current_user.id)
    
    if success:
        flash(f"Successfully connected to {ACCOUNTING_PLATFORMS[platform]['name']}", "success")
    else:
        flash(f"Failed to connect to {ACCOUNTING_PLATFORMS[platform]['name']}", "danger")
    
    return redirect(url_for('accounting.index'))

@accounting_bp.route('/disconnect/<platform>')
@login_required
@requires_access_level('fylr_plus')
def disconnect_platform(platform):
    """Disconnect from an accounting platform"""
    if platform not in ACCOUNTING_PLATFORMS:
        flash(f"Unsupported platform: {platform}", "danger")
        return redirect(url_for('accounting.index'))
    
    # Remove the connection from the database
    success = remove_platform_connection(platform, current_user.id)
    
    if success:
        flash(f"Successfully disconnected from {ACCOUNTING_PLATFORMS[platform]['name']}", "success")
    else:
        flash(f"Failed to disconnect from {ACCOUNTING_PLATFORMS[platform]['name']}", "danger")
    
    return redirect(url_for('accounting.index'))

@accounting_bp.route('/import/<platform>')
@login_required
@requires_access_level('fylr_plus')
def import_page(platform):
    """Show the import page for a specific platform"""
    if platform not in ACCOUNTING_PLATFORMS:
        flash(f"Unsupported platform: {platform}", "danger")
        return redirect(url_for('accounting.index'))
    
    # Verify that the user is connected to this platform
    if not is_platform_connected(platform, current_user.id):
        flash(f"You are not connected to {ACCOUNTING_PLATFORMS[platform]['name']}", "danger")
        return redirect(url_for('accounting.index'))
    
    # Get available data types for this platform
    data_types = ACCOUNTING_PLATFORMS[platform]['data_types']
    
    # Get tax years available for import
    available_years = get_available_tax_years(platform, current_user.id)
    
    return render_template('accounting/import.html',
                          platform=platform,
                          platform_info=ACCOUNTING_PLATFORMS[platform],
                          data_types=data_types,
                          available_years=available_years)

@accounting_bp.route('/import/<platform>/execute', methods=['POST'])
@login_required
@requires_access_level('fylr_plus')
def execute_import(platform):
    """Execute data import from an accounting platform"""
    if platform not in ACCOUNTING_PLATFORMS:
        flash(f"Unsupported platform: {platform}", "danger")
        return redirect(url_for('accounting.index'))
    
    # Verify that the user is connected to this platform
    if not is_platform_connected(platform, current_user.id):
        flash(f"You are not connected to {ACCOUNTING_PLATFORMS[platform]['name']}", "danger")
        return redirect(url_for('accounting.index'))
    
    # Get selected data types and tax year
    data_types = request.form.getlist('data_types')
    tax_year = request.form.get('tax_year', datetime.now().year, type=int)
    
    if not data_types:
        flash("Please select at least one data type to import", "warning")
        return redirect(url_for('accounting.import_page', platform=platform))
    
    # Execute the import for each data type
    results = {}
    for data_type in data_types:
        if data_type in ACCOUNTING_PLATFORMS[platform]['data_types']:
            # Import data and get result
            result = import_platform_data(platform, data_type, tax_year, current_user.id)
            results[data_type] = result
    
    # Record the import in the database
    record_import(platform, data_types, tax_year, results, current_user.id)
    
    return render_template('accounting/import_results.html',
                          platform=platform,
                          platform_info=ACCOUNTING_PLATFORMS[platform],
                          results=results,
                          tax_year=tax_year)

@accounting_bp.route('/data/<platform>/<data_type>')
@login_required
@requires_access_level('fylr_plus')
def view_imported_data(platform, data_type):
    """View imported data from a platform"""
    if platform not in ACCOUNTING_PLATFORMS:
        flash(f"Unsupported platform: {platform}", "danger")
        return redirect(url_for('accounting.index'))
    
    if data_type not in ACCOUNTING_PLATFORMS[platform]['data_types']:
        flash(f"Unsupported data type for {ACCOUNTING_PLATFORMS[platform]['name']}", "danger")
        return redirect(url_for('accounting.index'))
    
    # Get tax year from query parameter
    tax_year = request.args.get('tax_year', datetime.now().year, type=int)
    
    # Get the imported data
    data = get_imported_data(platform, data_type, tax_year, current_user.id)
    
    return render_template(f'accounting/data_{data_type}.html',
                          platform=platform,
                          platform_info=ACCOUNTING_PLATFORMS[platform],
                          data_type=data_type,
                          data=data,
                          tax_year=tax_year)

@accounting_bp.route('/api/data/<platform>/<data_type>')
@login_required
@requires_access_level('fylr_plus')
def api_get_data(platform, data_type):
    """API endpoint to get imported data"""
    if platform not in ACCOUNTING_PLATFORMS:
        return jsonify({'error': f"Unsupported platform: {platform}"}), 400
    
    if data_type not in ACCOUNTING_PLATFORMS[platform]['data_types']:
        return jsonify({'error': f"Unsupported data type for {platform}"}), 400
    
    # Get tax year from query parameter
    tax_year = request.args.get('tax_year', datetime.now().year, type=int)
    
    # Get the imported data
    data = get_imported_data(platform, data_type, tax_year, current_user.id)
    
    return jsonify(data)

@accounting_bp.route('/api/map-to-form', methods=['POST'])
@login_required
@requires_access_level('fylr_plus')
def api_map_to_form():
    """API endpoint to map accounting data to tax forms"""
    data = request.get_json()
    
    platform = data.get('platform')
    data_source = data.get('data_source')
    target_form = data.get('target_form')
    mapping = data.get('mapping')
    tax_year = data.get('tax_year', datetime.now().year)
    
    if not all([platform, data_source, target_form, mapping]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    # Execute the mapping
    result = map_accounting_data_to_form(
        platform, data_source, target_form, mapping, tax_year, current_user.id
    )
    
    return jsonify(result)

# QuickBooks OAuth functions
def get_quickbooks_auth_url():
    """Generate authorization URL for QuickBooks"""
    # Get QuickBooks OAuth settings from environment variables
    client_id = os.environ.get('QUICKBOOKS_CLIENT_ID')
    redirect_uri = os.environ.get('QUICKBOOKS_REDIRECT_URI')
    
    if not client_id or not redirect_uri:
        logging.error("QuickBooks OAuth credentials not set in environment variables")
        return None
    
    # Construct the authorization URL
    auth_endpoint = "https://appcenter.intuit.com/connect/oauth2"
    params = {
        "client_id": client_id,
        "response_type": "code",
        "scope": "com.intuit.quickbooks.accounting",
        "redirect_uri": redirect_uri,
        "state": "quickbooks"
    }
    
    auth_url = f"{auth_endpoint}?{urllib.parse.urlencode(params)}"
    return auth_url

def exchange_quickbooks_code(code, user_id):
    """Exchange authorization code for QuickBooks tokens"""
    # Get QuickBooks OAuth settings
    client_id = os.environ.get('QUICKBOOKS_CLIENT_ID')
    client_secret = os.environ.get('QUICKBOOKS_CLIENT_SECRET')
    redirect_uri = os.environ.get('QUICKBOOKS_REDIRECT_URI')
    
    if not client_id or not client_secret or not redirect_uri:
        logging.error("QuickBooks OAuth credentials not set in environment variables")
        return False
    
    token_endpoint = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    # Construct the request body
    auth_string = f"{client_id}:{client_secret}"
    encoded_auth = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    headers["Authorization"] = f"Basic {encoded_auth}"
    
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri
    }
    
    # Make the token request
    try:
        # In a real implementation, we would make an actual API call
        # For this prototype, we'll simulate a successful response
        
        # response = requests.post(token_endpoint, headers=headers, data=data)
        # if response.status_code != 200:
        #     logging.error(f"Error exchanging QuickBooks code: {response.text}")
        #     return False
        
        # token_data = response.json()
        
        # Simulated token data
        token_data = {
            "access_token": "simulated_access_token",
            "refresh_token": "simulated_refresh_token",
            "expires_in": 3600,
            "x_refresh_token_expires_in": 8726400
        }
        
        # Save the token data to the database
        save_platform_connection('quickbooks', user_id, token_data)
        
        return True
    except Exception as e:
        logging.error(f"Exception exchanging QuickBooks code: {str(e)}")
        return False

# Xero OAuth functions
def get_xero_auth_url():
    """Generate authorization URL for Xero"""
    # Get Xero OAuth settings from environment variables
    client_id = os.environ.get('XERO_CLIENT_ID')
    redirect_uri = os.environ.get('XERO_REDIRECT_URI')
    
    if not client_id or not redirect_uri:
        logging.error("Xero OAuth credentials not set in environment variables")
        return None
    
    # Construct the authorization URL
    auth_endpoint = "https://login.xero.com/identity/connect/authorize"
    params = {
        "client_id": client_id,
        "response_type": "code",
        "scope": "accounting.reports.read accounting.transactions.read accounting.settings.read",
        "redirect_uri": redirect_uri,
        "state": "xero"
    }
    
    auth_url = f"{auth_endpoint}?{urllib.parse.urlencode(params)}"
    return auth_url

def exchange_xero_code(code, user_id):
    """Exchange authorization code for Xero tokens"""
    # Get Xero OAuth settings
    client_id = os.environ.get('XERO_CLIENT_ID')
    client_secret = os.environ.get('XERO_CLIENT_SECRET')
    redirect_uri = os.environ.get('XERO_REDIRECT_URI')
    
    if not client_id or not client_secret or not redirect_uri:
        logging.error("Xero OAuth credentials not set in environment variables")
        return False
    
    token_endpoint = "https://identity.xero.com/connect/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    # Make the token request
    try:
        # In a real implementation, we would make an actual API call
        # For this prototype, we'll simulate a successful response
        
        # response = requests.post(token_endpoint, headers=headers, data=data)
        # if response.status_code != 200:
        #     logging.error(f"Error exchanging Xero code: {response.text}")
        #     return False
        
        # token_data = response.json()
        
        # Simulated token data
        token_data = {
            "access_token": "simulated_access_token",
            "refresh_token": "simulated_refresh_token",
            "expires_in": 1800,
            "id_token": "simulated_id_token"
        }
        
        # Save the token data to the database
        save_platform_connection('xero', user_id, token_data)
        
        return True
    except Exception as e:
        logging.error(f"Exception exchanging Xero code: {str(e)}")
        return False

# FreshBooks OAuth functions
def get_freshbooks_auth_url():
    """Generate authorization URL for FreshBooks"""
    # Get FreshBooks OAuth settings from environment variables
    client_id = os.environ.get('FRESHBOOKS_CLIENT_ID')
    redirect_uri = os.environ.get('FRESHBOOKS_REDIRECT_URI')
    
    if not client_id or not redirect_uri:
        logging.error("FreshBooks OAuth credentials not set in environment variables")
        return None
    
    # Construct the authorization URL
    auth_endpoint = "https://my.freshbooks.com/service/auth/oauth/authorize"
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": "freshbooks"
    }
    
    auth_url = f"{auth_endpoint}?{urllib.parse.urlencode(params)}"
    return auth_url

def exchange_freshbooks_code(code, user_id):
    """Exchange authorization code for FreshBooks tokens"""
    # Get FreshBooks OAuth settings
    client_id = os.environ.get('FRESHBOOKS_CLIENT_ID')
    client_secret = os.environ.get('FRESHBOOKS_CLIENT_SECRET')
    redirect_uri = os.environ.get('FRESHBOOKS_REDIRECT_URI')
    
    if not client_id or not client_secret or not redirect_uri:
        logging.error("FreshBooks OAuth credentials not set in environment variables")
        return False
    
    token_endpoint = "https://api.freshbooks.com/auth/oauth/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    # Make the token request
    try:
        # In a real implementation, we would make an actual API call
        # For this prototype, we'll simulate a successful response
        
        # response = requests.post(token_endpoint, headers=headers, data=data)
        # if response.status_code != 200:
        #     logging.error(f"Error exchanging FreshBooks code: {response.text}")
        #     return False
        
        # token_data = response.json()
        
        # Simulated token data
        token_data = {
            "access_token": "simulated_access_token",
            "refresh_token": "simulated_refresh_token",
            "expires_in": 3600,
            "token_type": "bearer"
        }
        
        # Save the token data to the database
        save_platform_connection('freshbooks', user_id, token_data)
        
        return True
    except Exception as e:
        logging.error(f"Exception exchanging FreshBooks code: {str(e)}")
        return False

# Wave OAuth functions
def get_wave_auth_url():
    """Generate authorization URL for Wave"""
    # Get Wave OAuth settings from environment variables
    client_id = os.environ.get('WAVE_CLIENT_ID')
    redirect_uri = os.environ.get('WAVE_REDIRECT_URI')
    
    if not client_id or not redirect_uri:
        logging.error("Wave OAuth credentials not set in environment variables")
        return None
    
    # Construct the authorization URL
    auth_endpoint = "https://api.waveapps.com/oauth2/authorize/"
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": "business:read,accounting:read",
        "state": "wave"
    }
    
    auth_url = f"{auth_endpoint}?{urllib.parse.urlencode(params)}"
    return auth_url

def exchange_wave_code(code, user_id):
    """Exchange authorization code for Wave tokens"""
    # Get Wave OAuth settings
    client_id = os.environ.get('WAVE_CLIENT_ID')
    client_secret = os.environ.get('WAVE_CLIENT_SECRET')
    redirect_uri = os.environ.get('WAVE_REDIRECT_URI')
    
    if not client_id or not client_secret or not redirect_uri:
        logging.error("Wave OAuth credentials not set in environment variables")
        return False
    
    token_endpoint = "https://api.waveapps.com/oauth2/token/"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    # Make the token request
    try:
        # In a real implementation, we would make an actual API call
        # For this prototype, we'll simulate a successful response
        
        # response = requests.post(token_endpoint, headers=headers, data=data)
        # if response.status_code != 200:
        #     logging.error(f"Error exchanging Wave code: {response.text}")
        #     return False
        
        # token_data = response.json()
        
        # Simulated token data
        token_data = {
            "access_token": "simulated_access_token",
            "refresh_token": "simulated_refresh_token",
            "expires_in": 3600,
            "token_type": "Bearer"
        }
        
        # Save the token data to the database
        save_platform_connection('wave', user_id, token_data)
        
        return True
    except Exception as e:
        logging.error(f"Exception exchanging Wave code: {str(e)}")
        return False

# MYOB OAuth functions
def get_myob_auth_url():
    """Generate authorization URL for MYOB"""
    # Get MYOB OAuth settings from environment variables
    client_id = os.environ.get('MYOB_CLIENT_ID')
    redirect_uri = os.environ.get('MYOB_REDIRECT_URI')
    
    if not client_id or not redirect_uri:
        logging.error("MYOB OAuth credentials not set in environment variables")
        return None
    
    # Construct the authorization URL
    auth_endpoint = "https://secure.myob.com/oauth2/account/authorize"
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": "CompanyFile",
        "state": "myob"
    }
    
    auth_url = f"{auth_endpoint}?{urllib.parse.urlencode(params)}"
    return auth_url

def exchange_myob_code(code, user_id):
    """Exchange authorization code for MYOB tokens"""
    # Get MYOB OAuth settings
    client_id = os.environ.get('MYOB_CLIENT_ID')
    client_secret = os.environ.get('MYOB_CLIENT_SECRET')
    redirect_uri = os.environ.get('MYOB_REDIRECT_URI')
    
    if not client_id or not client_secret or not redirect_uri:
        logging.error("MYOB OAuth credentials not set in environment variables")
        return False
    
    token_endpoint = "https://secure.myob.com/oauth2/v1/authorize"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    # Make the token request
    try:
        # In a real implementation, we would make an actual API call
        # For this prototype, we'll simulate a successful response
        
        # response = requests.post(token_endpoint, headers=headers, data=data)
        # if response.status_code != 200:
        #     logging.error(f"Error exchanging MYOB code: {response.text}")
        #     return False
        
        # token_data = response.json()
        
        # Simulated token data
        token_data = {
            "access_token": "simulated_access_token",
            "refresh_token": "simulated_refresh_token",
            "expires_in": 3600,
            "token_type": "Bearer"
        }
        
        # Save the token data to the database
        save_platform_connection('myob', user_id, token_data)
        
        return True
    except Exception as e:
        logging.error(f"Exception exchanging MYOB code: {str(e)}")
        return False

# Database helper functions
def get_user_connected_accounts(user_id):
    """Get a list of accounting platforms the user has connected"""
    # In a real implementation, this would query the database
    # For this prototype, we'll simulate a user with QuickBooks connected
    
    return [
        {
            'platform': 'quickbooks',
            'name': ACCOUNTING_PLATFORMS['quickbooks']['name'],
            'connected_at': datetime.now() - timedelta(days=7),
            'last_sync': datetime.now() - timedelta(days=2),
            'status': 'active'
        }
    ]

def get_recent_imports(user_id):
    """Get a list of recent data imports"""
    # In a real implementation, this would query the database
    # For this prototype, we'll return a simulated list
    
    return [
        {
            'platform': 'quickbooks',
            'data_type': 'profit_loss',
            'tax_year': datetime.now().year - 1,
            'status': 'success',
            'imported_at': datetime.now() - timedelta(days=2),
            'records_count': 124
        },
        {
            'platform': 'quickbooks',
            'data_type': 'balance_sheet',
            'tax_year': datetime.now().year - 1,
            'status': 'success',
            'imported_at': datetime.now() - timedelta(days=2),
            'records_count': 87
        }
    ]

def is_platform_connected(platform, user_id):
    """Check if a user is connected to a specific accounting platform"""
    # In a real implementation, this would query the database
    # For this prototype, we'll simulate QuickBooks being connected
    
    return platform == 'quickbooks'

def save_platform_connection(platform, user_id, token_data):
    """Save platform connection data to the database"""
    # In a real implementation, this would save to the database
    # For this prototype, we'll simply log the action
    
    logging.info(f"Saved {platform} connection for user {user_id}")
    return True

def remove_platform_connection(platform, user_id):
    """Remove a platform connection from the database"""
    # In a real implementation, this would update the database
    # For this prototype, we'll simply log the action
    
    logging.info(f"Removed {platform} connection for user {user_id}")
    return True

def get_available_tax_years(platform, user_id):
    """Get available tax years for a platform"""
    # In a real implementation, this would query the platform API
    # For this prototype, we'll return a simulated list
    
    current_year = datetime.now().year
    return [current_year - 2, current_year - 1, current_year]

def import_platform_data(platform, data_type, tax_year, user_id):
    """Import data from a platform for a specific data type and tax year"""
    # In a real implementation, this would:
    # 1. Get the access token for the platform
    # 2. Make API calls to the platform
    # 3. Process and save the retrieved data
    # 4. Return a result summary
    
    # For this prototype, we'll simulate a successful import
    
    # Simulate different record counts based on data type
    record_counts = {
        'chart_of_accounts': 50,
        'profit_loss': 125,
        'balance_sheet': 75,
        'tax_summary': 30,
        'transactions': 250,
        'expenses': 180
    }
    
    # Simulate processing time based on data type
    import time
    processing_time = 1.5  # seconds
    
    # Simulate successful import
    result = {
        'status': 'success',
        'data_type': data_type,
        'tax_year': tax_year,
        'records_imported': record_counts.get(data_type, 100),
        'processing_time': processing_time,
        'imported_at': datetime.now().isoformat(),
        'message': f"Successfully imported {data_type} data for tax year {tax_year}"
    }
    
    return result

def record_import(platform, data_types, tax_year, results, user_id):
    """Record an import in the database"""
    # In a real implementation, this would save to the database
    # For this prototype, we'll simply log the action
    
    logging.info(f"Recorded import of {', '.join(data_types)} from {platform} for tax year {tax_year}")
    return True

def get_imported_data(platform, data_type, tax_year, user_id):
    """Get imported data for a specific platform, data type, and tax year"""
    # In a real implementation, this would query the database
    # For this prototype, we'll return simulated data based on the data type
    
    if data_type == 'chart_of_accounts':
        return get_sample_chart_of_accounts()
    elif data_type == 'profit_loss':
        return get_sample_profit_loss(tax_year)
    elif data_type == 'balance_sheet':
        return get_sample_balance_sheet(tax_year)
    elif data_type == 'tax_summary':
        return get_sample_tax_summary(tax_year)
    elif data_type == 'transactions':
        return get_sample_transactions(tax_year)
    elif data_type == 'expenses':
        return get_sample_expenses(tax_year)
    else:
        return {"error": "No data available for this data type"}

def map_accounting_data_to_form(platform, data_source, target_form, mapping, tax_year, user_id):
    """Map accounting data to a tax form"""
    # In a real implementation, this would:
    # 1. Get the source accounting data
    # 2. Get the target tax form structure
    # 3. Apply the mapping to populate the tax form
    # 4. Return the mapped form data or create a new form
    
    # For this prototype, we'll simulate a successful mapping
    
    # Get source data
    source_data = get_imported_data(platform, data_source, tax_year, user_id)
    
    # Simulate mapping process
    # In a real implementation, this would apply the mapping rules
    # to extract values from source_data and populate the form
    
    # Generate mapped data (simulated)
    mapped_data = {
        'form_type': target_form,
        'tax_year': tax_year,
        'source_platform': platform,
        'source_data_type': data_source,
        'mapping_applied': mapping,
        'status': 'draft',
        'created_at': datetime.now().isoformat()
    }
    
    # For demonstration, add some simulated mapped values
    if target_form == 'schedule_c':
        mapped_data['form_data'] = {
            'business_info': {
                'business_name': 'My Business',
                'business_code': '541990'  # Professional Services
            },
            'income': {
                'gross_receipts': source_data.get('profit_loss', {}).get('total_revenue', 0),
                'returns_allowances': 0,
                'other_income': 0
            },
            'expenses': {
                'advertising': source_data.get('profit_loss', {}).get('expenses', {}).get('marketing_and_advertising', 0),
                'car_expenses': source_data.get('profit_loss', {}).get('expenses', {}).get('vehicle_expenses', 0),
                'commissions': source_data.get('profit_loss', {}).get('expenses', {}).get('commissions', 0),
                'insurance': source_data.get('profit_loss', {}).get('expenses', {}).get('insurance', 0),
                'legal_professional': source_data.get('profit_loss', {}).get('expenses', {}).get('professional_fees', 0),
                'office_expenses': source_data.get('profit_loss', {}).get('expenses', {}).get('office_expenses', 0),
                'rent_lease_other': source_data.get('profit_loss', {}).get('expenses', {}).get('rent', 0),
                'repairs_maintenance': source_data.get('profit_loss', {}).get('expenses', {}).get('repairs_and_maintenance', 0),
                'supplies': source_data.get('profit_loss', {}).get('expenses', {}).get('supplies', 0),
                'taxes_licenses': source_data.get('profit_loss', {}).get('expenses', {}).get('taxes_and_licenses', 0),
                'travel': source_data.get('profit_loss', {}).get('expenses', {}).get('travel', 0),
                'meals': source_data.get('profit_loss', {}).get('expenses', {}).get('meals_and_entertainment', 0),
                'utilities': source_data.get('profit_loss', {}).get('expenses', {}).get('utilities', 0),
                'wages': source_data.get('profit_loss', {}).get('expenses', {}).get('salaries_and_wages', 0)
            }
        }
    
    return {
        'status': 'success',
        'message': f"Successfully mapped {data_source} data to {target_form}",
        'mapped_data': mapped_data
    }

# Sample data functions for demonstration purposes
def get_sample_chart_of_accounts():
    """Return sample chart of accounts data"""
    return {
        "accounts": [
            {"id": "1000", "name": "Cash", "type": "Asset", "subtype": "Current Asset"},
            {"id": "1100", "name": "Accounts Receivable", "type": "Asset", "subtype": "Current Asset"},
            {"id": "1200", "name": "Inventory", "type": "Asset", "subtype": "Current Asset"},
            {"id": "1500", "name": "Fixed Assets", "type": "Asset", "subtype": "Fixed Asset"},
            {"id": "1600", "name": "Accumulated Depreciation", "type": "Asset", "subtype": "Fixed Asset"},
            {"id": "2000", "name": "Accounts Payable", "type": "Liability", "subtype": "Current Liability"},
            {"id": "2100", "name": "Credit Cards", "type": "Liability", "subtype": "Current Liability"},
            {"id": "2200", "name": "Loans Payable", "type": "Liability", "subtype": "Long Term Liability"},
            {"id": "3000", "name": "Owner's Equity", "type": "Equity", "subtype": "Equity"},
            {"id": "3900", "name": "Retained Earnings", "type": "Equity", "subtype": "Equity"},
            {"id": "4000", "name": "Revenue", "type": "Income", "subtype": "Income"},
            {"id": "4100", "name": "Service Revenue", "type": "Income", "subtype": "Income"},
            {"id": "4200", "name": "Product Sales", "type": "Income", "subtype": "Income"},
            {"id": "4900", "name": "Other Income", "type": "Income", "subtype": "Other Income"},
            {"id": "5000", "name": "Cost of Goods Sold", "type": "Expense", "subtype": "Cost of Sales"},
            {"id": "6000", "name": "Advertising", "type": "Expense", "subtype": "Expense"},
            {"id": "6100", "name": "Car and Truck Expenses", "type": "Expense", "subtype": "Expense"},
            {"id": "6200", "name": "Commissions and Fees", "type": "Expense", "subtype": "Expense"},
            {"id": "6300", "name": "Insurance", "type": "Expense", "subtype": "Expense"},
            {"id": "6400", "name": "Professional Fees", "type": "Expense", "subtype": "Expense"},
            {"id": "6500", "name": "Office Expenses", "type": "Expense", "subtype": "Expense"},
            {"id": "6600", "name": "Rent", "type": "Expense", "subtype": "Expense"},
            {"id": "6700", "name": "Repairs and Maintenance", "type": "Expense", "subtype": "Expense"},
            {"id": "6800", "name": "Supplies", "type": "Expense", "subtype": "Expense"},
            {"id": "6900", "name": "Taxes and Licenses", "type": "Expense", "subtype": "Expense"},
            {"id": "7000", "name": "Travel", "type": "Expense", "subtype": "Expense"},
            {"id": "7100", "name": "Meals and Entertainment", "type": "Expense", "subtype": "Expense"},
            {"id": "7200", "name": "Utilities", "type": "Expense", "subtype": "Expense"},
            {"id": "7300", "name": "Wages", "type": "Expense", "subtype": "Expense"},
            {"id": "7900", "name": "Other Expenses", "type": "Expense", "subtype": "Expense"},
            {"id": "8000", "name": "Interest Expense", "type": "Expense", "subtype": "Other Expense"},
            {"id": "9000", "name": "Taxes", "type": "Expense", "subtype": "Other Expense"}
        ]
    }

def get_sample_profit_loss(tax_year):
    """Return sample profit and loss data"""
    return {
        "report_name": "Profit and Loss",
        "business_name": "Sample Business",
        "period": f"Jan 1 - Dec 31, {tax_year}",
        "total_revenue": 458750.25,
        "revenue": {
            "product_sales": 285450.75,
            "service_revenue": 158125.25,
            "other_income": 15174.25
        },
        "total_expenses": 325800.50,
        "expenses": {
            "cost_of_goods_sold": 125450.25,
            "salaries_and_wages": 85000.00,
            "payroll_taxes": 7650.00,
            "rent": 24000.00,
            "utilities": 5425.75,
            "insurance": 12500.00,
            "marketing_and_advertising": 18750.50,
            "professional_fees": 15000.00,
            "office_expenses": 4500.25,
            "supplies": 7500.50,
            "travel": 5250.00,
            "meals_and_entertainment": 3500.00,
            "vehicle_expenses": 4550.25,
            "repairs_and_maintenance": 2750.00,
            "taxes_and_licenses": 3500.00,
            "interest": 1500.00,
            "depreciation": 3500.00,
            "other_expenses": 2500.00
        },
        "net_income": 132949.75,
        "quarterly_breakdown": {
            "q1": {
                "revenue": 102500.25,
                "expenses": 75250.50,
                "net_income": 27249.75
            },
            "q2": {
                "revenue": 118750.00,
                "expenses": 82500.25,
                "net_income": 36249.75
            },
            "q3": {
                "revenue": 105000.00,
                "expenses": 78500.75,
                "net_income": 26499.25
            },
            "q4": {
                "revenue": 132500.00,
                "expenses": 89549.00,
                "net_income": 42951.00
            }
        }
    }

def get_sample_balance_sheet(tax_year):
    """Return sample balance sheet data"""
    return {
        "report_name": "Balance Sheet",
        "business_name": "Sample Business",
        "as_of_date": f"December 31, {tax_year}",
        "assets": {
            "current_assets": {
                "cash_and_equivalents": 75000.25,
                "accounts_receivable": 45000.50,
                "inventory": 35000.75,
                "prepaid_expenses": 5000.00,
                "other_current_assets": 2500.00,
                "total_current_assets": 162501.50
            },
            "fixed_assets": {
                "property_and_equipment": 150000.00,
                "accumulated_depreciation": -35000.00,
                "total_fixed_assets": 115000.00
            },
            "other_assets": {
                "intangible_assets": 10000.00,
                "other_long_term_assets": 5000.00,
                "total_other_assets": 15000.00
            },
            "total_assets": 292501.50
        },
        "liabilities_and_equity": {
            "liabilities": {
                "current_liabilities": {
                    "accounts_payable": 25000.50,
                    "credit_cards": 7500.25,
                    "accrued_expenses": 12500.00,
                    "current_portion_of_long_term_debt": 10000.00,
                    "other_current_liabilities": 5000.00,
                    "total_current_liabilities": 60000.75
                },
                "long_term_liabilities": {
                    "loans_payable": 75000.00,
                    "other_long_term_liabilities": 5000.00,
                    "total_long_term_liabilities": 80000.00
                },
                "total_liabilities": 140000.75
            },
            "equity": {
                "owner_capital": 100000.00,
                "retained_earnings": 52500.75,
                "net_income": 100000.00,
                "total_equity": 152500.75
            },
            "total_liabilities_and_equity": 292501.50
        }
    }

def get_sample_tax_summary(tax_year):
    """Return sample tax summary data"""
    return {
        "report_name": "Tax Summary",
        "business_name": "Sample Business",
        "tax_year": tax_year,
        "income_summary": {
            "gross_income": 458750.25,
            "returns_and_allowances": 0.00,
            "other_income": 15174.25,
            "total_income": 473924.50
        },
        "expense_summary": {
            "cost_of_goods_sold": 125450.25,
            "deductible_expenses": {
                "advertising": 18750.50,
                "car_and_truck": 4550.25,
                "commissions_and_fees": 0.00,
                "contract_labor": 0.00,
                "depletion": 0.00,
                "depreciation": 3500.00,
                "employee_benefits": 0.00,
                "insurance": 12500.00,
                "interest_mortgage": 0.00,
                "interest_other": 1500.00,
                "legal_and_professional": 15000.00,
                "office_expenses": 4500.25,
                "pension_and_profit_sharing": 0.00,
                "rent_or_lease": 24000.00,
                "repairs_and_maintenance": 2750.00,
                "supplies": 7500.50,
                "taxes_and_licenses": 3500.00,
                "travel": 5250.00,
                "meals": 3500.00,
                "utilities": 5425.75,
                "wages": 85000.00,
                "other_expenses": 2500.00
            },
            "total_expenses": 325800.50
        },
        "net_profit": 148124.00,
        "tax_deductions": {
            "section_179_expense": 0.00,
            "retirement_contributions": 0.00,
            "self_employed_health_insurance": 0.00,
            "self_employment_tax_deduction": 0.00
        },
        "taxable_income": 148124.00,
        "estimated_taxes": {
            "income_tax": 29624.80,
            "self_employment_tax": 20938.00,
            "total_estimated_tax": 50562.80
        },
        "quarterly_payment_schedule": {
            "q1_payment": 12640.70,
            "q2_payment": 12640.70,
            "q3_payment": 12640.70,
            "q4_payment": 12640.70
        }
    }

def get_sample_transactions(tax_year):
    """Return sample transaction data"""
    # Generate sample transactions spanning the tax year
    transactions = []
    
    # Sample revenue transactions
    for month in range(1, 13):
        # Product sales
        transactions.append({
            "date": f"{tax_year}-{month:02d}-{10}",
            "type": "Revenue",
            "category": "Product Sales",
            "description": f"Product sale - {month:02d}/{tax_year}",
            "amount": 23787.56 + (month * 100),
            "account": "4200 - Product Sales"
        })
        
        # Service revenue
        transactions.append({
            "date": f"{tax_year}-{month:02d}-{20}",
            "type": "Revenue",
            "category": "Service Revenue",
            "description": f"Service revenue - {month:02d}/{tax_year}",
            "amount": 13177.10 + (month * 50),
            "account": "4100 - Service Revenue"
        })
    
    # Sample expense transactions
    expense_categories = [
        {"name": "Rent", "account": "6600 - Rent", "monthly_amount": 2000.00, "day": 1},
        {"name": "Utilities", "account": "7200 - Utilities", "monthly_amount": 452.15, "day": 5},
        {"name": "Insurance", "account": "6300 - Insurance", "monthly_amount": 1041.67, "day": 10},
        {"name": "Advertising", "account": "6000 - Advertising", "monthly_amount": 1562.54, "day": 15},
        {"name": "Office Supplies", "account": "6500 - Office Expenses", "monthly_amount": 375.02, "day": 18},
        {"name": "Professional Fees", "account": "6400 - Professional Fees", "monthly_amount": 1250.00, "day": 20},
        {"name": "Salaries", "account": "7300 - Wages", "monthly_amount": 7083.33, "day": 25}
    ]
    
    for month in range(1, 13):
        for category in expense_categories:
            transactions.append({
                "date": f"{tax_year}-{month:02d}-{category['day']}",
                "type": "Expense",
                "category": category['name'],
                "description": f"{category['name']} expense - {month:02d}/{tax_year}",
                "amount": category['monthly_amount'] + (month * 0.1 * category['monthly_amount'] / 12),
                "account": category['account']
            })
    
    # Add some random one-time expenses
    one_time_expenses = [
        {
            "date": f"{tax_year}-02-15",
            "type": "Expense",
            "category": "Travel",
            "description": "Business trip to conference",
            "amount": 1875.50,
            "account": "7000 - Travel"
        },
        {
            "date": f"{tax_year}-04-22",
            "type": "Expense",
            "category": "Meals",
            "description": "Client dinner meeting",
            "amount": 325.75,
            "account": "7100 - Meals and Entertainment"
        },
        {
            "date": f"{tax_year}-06-30",
            "type": "Expense",
            "category": "Equipment Purchase",
            "description": "New computer equipment",
            "amount": 2750.00,
            "account": "1500 - Fixed Assets"
        },
        {
            "date": f"{tax_year}-09-15",
            "type": "Expense",
            "category": "Car and Truck",
            "description": "Vehicle maintenance",
            "amount": 525.25,
            "account": "6100 - Car and Truck Expenses"
        },
        {
            "date": f"{tax_year}-11-29",
            "type": "Expense",
            "category": "Repairs and Maintenance",
            "description": "Office repair work",
            "amount": 850.00,
            "account": "6700 - Repairs and Maintenance"
        }
    ]
    
    transactions.extend(one_time_expenses)
    
    # Sort transactions by date
    transactions.sort(key=lambda x: x['date'])
    
    return {
        "report_name": "Transactions",
        "business_name": "Sample Business",
        "period": f"Jan 1 - Dec 31, {tax_year}",
        "transaction_count": len(transactions),
        "transactions": transactions
    }

def get_sample_expenses(tax_year):
    """Return sample detailed expense data"""
    # Generate expense categories with subcategories and transactions
    expense_categories = [
        {
            "category": "Advertising",
            "total": 18750.50,
            "subcategories": [
                {"name": "Online Advertising", "total": 10250.25},
                {"name": "Print Advertising", "total": 5500.00},
                {"name": "Other Advertising", "total": 3000.25}
            ],
            "transactions": [
                {"date": f"{tax_year}-01-15", "description": "Google Ads", "amount": 850.25},
                {"date": f"{tax_year}-02-15", "description": "Facebook Ads", "amount": 925.50},
                {"date": f"{tax_year}-03-15", "description": "Local newspaper ad", "amount": 1200.00}
                # More transactions would be included in a real implementation
            ]
        },
        {
            "category": "Rent",
            "total": 24000.00,
            "subcategories": [
                {"name": "Office Rent", "total": 24000.00}
            ],
            "transactions": [
                {"date": f"{tax_year}-01-01", "description": "January Office Rent", "amount": 2000.00},
                {"date": f"{tax_year}-02-01", "description": "February Office Rent", "amount": 2000.00},
                {"date": f"{tax_year}-03-01", "description": "March Office Rent", "amount": 2000.00}
                # More transactions would be included in a real implementation
            ]
        },
        {
            "category": "Utilities",
            "total": 5425.75,
            "subcategories": [
                {"name": "Electricity", "total": 3250.50},
                {"name": "Internet", "total": 1375.25},
                {"name": "Phone", "total": 800.00}
            ],
            "transactions": [
                {"date": f"{tax_year}-01-05", "description": "January Electricity", "amount": 265.25},
                {"date": f"{tax_year}-01-10", "description": "January Internet", "amount": 115.00},
                {"date": f"{tax_year}-01-15", "description": "January Phone", "amount": 65.50}
                # More transactions would be included in a real implementation
            ]
        },
        {
            "category": "Office Expenses",
            "total": 4500.25,
            "subcategories": [
                {"name": "Office Supplies", "total": 2750.25},
                {"name": "Postage", "total": 750.00},
                {"name": "Printing", "total": 1000.00}
            ],
            "transactions": [
                {"date": f"{tax_year}-01-18", "description": "Office Depot - supplies", "amount": 225.50},
                {"date": f"{tax_year}-02-15", "description": "Staples - printer paper", "amount": 150.75},
                {"date": f"{tax_year}-03-22", "description": "Amazon - office supplies", "amount": 175.25}
                # More transactions would be included in a real implementation
            ]
        },
        {
            "category": "Professional Fees",
            "total": 15000.00,
            "subcategories": [
                {"name": "Accounting", "total": 7500.00},
                {"name": "Legal", "total": 5500.00},
                {"name": "Consulting", "total": 2000.00}
            ],
            "transactions": [
                {"date": f"{tax_year}-01-20", "description": "Monthly accounting service", "amount": 600.00},
                {"date": f"{tax_year}-02-15", "description": "Legal review of contract", "amount": 1500.00},
                {"date": f"{tax_year}-03-10", "description": "IT consulting", "amount": 2000.00}
                # More transactions would be included in a real implementation
            ]
        }
    ]
    
    # Calculate total expenses
    total_expenses = sum(category["total"] for category in expense_categories)
    
    return {
        "report_name": "Detailed Expenses",
        "business_name": "Sample Business",
        "period": f"Jan 1 - Dec 31, {tax_year}",
        "total_expenses": total_expenses,
        "expense_categories": expense_categories
    }