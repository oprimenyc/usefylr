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
        # In a real implementation, we would call the WordPress site API
        # to validate the token and get user information
        # For now, we'll simulate this process with a placeholder
        
        # Placeholder logic for WordPress token validation
        # This would be replaced with actual API calls to WordPress
        wp_user_data = {
            'id': 123,  # WordPress user ID
            'username': 'wp_user',
            'email': 'wp_user@example.com',
            'subscription_status': 'active',  # or 'inactive'
            'plan': 'business_builder'  # or 'standard' or 'free'
        }
        
        # Check if user with this WordPress ID already exists
        user = User.query.filter_by(wordpress_id=wp_user_data['id']).first()
        
        if user:
            # Update user information
            user.username = wp_user_data['username']
            user.email = wp_user_data['email']
            user.subscription_member = wp_user_data['subscription_status'] == 'active'
            
            if wp_user_data['plan'] == 'business_builder':
                user.plan = UserPlan.BUSINESS_BUILDER
            elif wp_user_data['plan'] == 'standard':
                user.plan = UserPlan.STANDARD
            else:
                user.plan = UserPlan.FREE
                
            db.session.commit()
        else:
            # Create new user
            user = User(
                username=wp_user_data['username'],
                email=wp_user_data['email'],
                wordpress_id=wp_user_data['id'],
                subscription_member=wp_user_data['subscription_status'] == 'active'
            )
            
            if wp_user_data['plan'] == 'business_builder':
                user.plan = UserPlan.BUSINESS_BUILDER
            elif wp_user_data['plan'] == 'standard':
                user.plan = UserPlan.STANDARD
            else:
                user.plan = UserPlan.FREE
                
            # Generate a random password (not used for WP users)
            import secrets
            random_password = secrets.token_urlsafe(16)
            user.set_password(random_password)
            
            db.session.add(user)
            db.session.commit()
        
        return user
    except Exception as e:
        logging.error(f"Error validating WordPress token: {e}")
        return None