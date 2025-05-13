from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import requests
import json
from app.app import db
from app.models import User, AuditLog, UserPlan

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login - both standalone and WordPress integration"""
    # Check if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    # Check if there's a WordPress token in the query string
    wp_token = request.args.get('wp_token')
    if wp_token:
        # Try to validate WordPress token
        user = validate_wp_token(wp_token)
        if user:
            login_user(user)
            # Log successful login
            log = AuditLog(
                user_id=user.id,
                action="login",
                details="Login via WordPress integration",
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            # Redirect to dashboard
            next_page = request.args.get('next')
            if not next_page or url_for('main.index') in next_page:
                next_page = url_for('main.dashboard')
            return redirect(next_page)
        else:
            flash('Invalid WordPress authentication token.', 'danger')
    
    # Handle regular login form submission
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        # Validate input
        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('auth/login.html')
        
        # Find user by username or email
        user = User.query.filter((User.username == username) | (User.email == username)).first()
        
        # Check if user exists and password is correct
        if user and user.check_password(password):
            login_user(user, remember=remember)
            
            # Log successful login
            log = AuditLog(
                user_id=user.id,
                action="login",
                details="Direct login",
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if not next_page or url_for('main.index') in next_page:
                next_page = url_for('main.dashboard')
            return redirect(next_page)
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user"""
    # Check if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    # Handle form submission
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate input
        if not username or not email or not password or not confirm_password:
            flash('All fields are required.', 'danger')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return render_template('auth/register.html')
        
        # Create new user
        user = User(
            username=username,
            email=email,
            plan=UserPlan.FREE,
            subscription_member=False
        )
        user.set_password(password)
        
        # Add user to database
        db.session.add(user)
        
        # Log registration
        log = AuditLog(
            user_id=user.id,
            action="register",
            details="New user registration",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        # Log user in
        login_user(user)
        flash('Registration successful!', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Log out the current user"""
    # Log logout
    log = AuditLog(
        user_id=current_user.id,
        action="logout",
        details="User logout",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    # Log out user
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

def validate_wp_token(token):
    """Validate WordPress authentication token and return/create a user"""
    try:
        # Set up WordPress API endpoint
        # This should be the REST API endpoint for your WordPress site
        wordpress_api_url = "https://federalfundingclub.com/wp-json/jwt-auth/v1/token/validate"
        
        # Headers for the API request
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Make the request to WordPress to validate the token
        response = requests.post(wordpress_api_url, headers=headers)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the response data
            data = response.json()
            
            if data.get('success', False):
                # Get the user data from the response
                wp_user_data = data.get('data', {})
                
                # If we don't have a WordPress user ID, we can't proceed
                if not wp_user_data.get('id'):
                    logging.error("No WordPress user ID provided in token response")
                    return None
                
                # Get the user's membership status and level
                # This would depend on your WordPress site setup
                subscription_status = "active" if wp_user_data.get('membership_active', False) else "inactive"
                plan_level = wp_user_data.get('membership_level', 'free').lower()
                
                # Check if user with this WordPress ID already exists
                user = User.query.filter_by(wordpress_id=wp_user_data['id']).first()
                
                if user:
                    # Update user information
                    user.username = wp_user_data.get('username', user.username)
                    user.email = wp_user_data.get('email', user.email)
                    user.subscription_member = subscription_status == 'active'
                    
                    # Update the user's plan based on WordPress membership level
                    if plan_level == 'business_builder':
                        user.plan = UserPlan.BUSINESS_BUILDER
                    elif plan_level == 'standard':
                        user.plan = UserPlan.STANDARD
                    else:
                        user.plan = UserPlan.FREE
                        
                    db.session.commit()
                    logging.info(f"Updated existing user from WordPress: {user.username}")
                else:
                    # Create new user
                    username = wp_user_data.get('username', f"wp_user_{wp_user_data['id']}")
                    email = wp_user_data.get('email', f"wp_{wp_user_data['id']}@federalfundingclub.com")
                    
                    user = User(
                        username=username,
                        email=email,
                        wordpress_id=wp_user_data['id'],
                        subscription_member=subscription_status == 'active'
                    )
                    
                    # Set the user's plan based on WordPress membership level
                    if plan_level == 'business_builder':
                        user.plan = UserPlan.BUSINESS_BUILDER
                    elif plan_level == 'standard':
                        user.plan = UserPlan.STANDARD
                    else:
                        user.plan = UserPlan.FREE
                    
                    # Generate a random password (not used for WP users, as they authenticate via token)
                    import secrets
                    random_password = secrets.token_urlsafe(16)
                    user.set_password(random_password)
                    
                    db.session.add(user)
                    db.session.commit()
                    logging.info(f"Created new user from WordPress: {user.username}")
                
                return user
            else:
                logging.warning(f"WordPress token validation failed: {data.get('message', 'Unknown error')}")
                return None
        else:
            logging.error(f"WordPress API request failed with status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error validating WordPress token: {e}")
        return None