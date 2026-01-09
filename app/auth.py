"""
Authentication routes for the application.
"""
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from app.models import User, UserPlan, AuditLog
from app.access_control import requires_legal_acknowledgment

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        # Demo account for testing
        if email == 'demo@fylr.tax' and password == 'demo123':
            # Check if demo user exists
            user = User.query.filter_by(email='demo@fylr.tax').first()
            
            # Create demo user if it doesn't exist
            if not user:
                user = User(
                    username='demo_user',
                    email='demo@fylr.tax',
                    password_hash=generate_password_hash('demo123'),
                    plan=UserPlan.GUIDED,  # Give demo user the guided plan
                    created_at=datetime.utcnow()
                )
                db.session.add(user)
                db.session.commit()
                
                # Log demo account creation
                AuditLog.log_action(
                    user_id=user.id,
                    action='Created demo account',
                    data={'demo_account': True}
                )
            
            # Log in the demo user
            login_user(user, remember=remember)
            flash('Welcome to the demo account! You have access to the Guided Plan features.', 'success')
            return redirect(url_for('main.dashboard'))
        
        # Normal login flow
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            flash('Please check your login details and try again.', 'danger')
            return redirect(url_for('auth.login'))
            
        # Log successful login
        AuditLog.log_action(
            user_id=user.id,
            action='User logged in',
            data={'remember_me': remember}
        )

        login_user(user, remember=remember)
        return redirect(url_for('main.dashboard'))
        
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        agree_terms = request.form.get('agree_terms')
        
        # Check if email already exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists', 'danger')
            return redirect(url_for('auth.register'))
            
        # Check if username already exists
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists', 'danger')
            return redirect(url_for('auth.register'))
            
        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('auth.register'))
            
        # Check if terms are agreed to
        if not agree_terms:
            flash('You must agree to the Terms of Service and Privacy Policy', 'danger')
            return redirect(url_for('auth.register'))
            
        # Create new user
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            plan=UserPlan.SELF_SERVICE,  # Default to self-service plan
            created_at=datetime.utcnow()
        )
        db.session.add(new_user)
        db.session.commit()
        
        # Log new user registration
        AuditLog.log_action(
            user_id=new_user.id,
            action='User registered',
            data={'username': username, 'email': email}
        )
        
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Log out the current user"""
    # Log user logout
    AuditLog.log_action(
        user_id=current_user.id,
        action='User logged out',
        data={}
    )
    
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/acknowledge-disclaimer', methods=['POST'])
@login_required
def acknowledge_disclaimer():
    """Acknowledge the legal disclaimer"""
    current_user.has_acknowledged_disclaimer = True
    db.session.commit()
    
    # Log disclaimer acknowledgment
    AuditLog.log_action(
        user_id=current_user.id,
        action='Acknowledged legal disclaimer',
        data={}
    )

    # Redirect to the requested page or dashboard
    next_page = request.args.get('next', url_for('main.dashboard'))
    return redirect(next_page)

def init_app(app):
    """Initialize authentication routes with the Flask app"""
    app.register_blueprint(auth_bp)