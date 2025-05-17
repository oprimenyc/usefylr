"""
Authentication routes for the application.
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User
from app import db

# Create blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(email=email).first()
        
        # Check if user exists and password is correct
        if not user or not check_password_hash(user.password_hash, password):
            flash('Please check your login details and try again.', 'danger')
            return redirect(url_for('auth.login'))
        
        # If we get here, user exists and password is correct
        login_user(user, remember=remember)
        next_page = request.args.get('next')
        
        if next_page:
            return redirect(next_page)
        return redirect(url_for('main.dashboard'))
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if email already exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Check if username already exists
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Create new user
        new_user = User(
            email=email,
            username=username,
            password_hash=generate_password_hash(password)
        )
        
        # Add user to database
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Log out the current user"""
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('main.index'))