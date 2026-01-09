#!/usr/bin/env python
"""
Create Test User Script for .fylr Platform
Creates a TRIAL user with complete BusinessProfile for testing
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# Load environment variables
load_dotenv()

from app import create_app, db
from app.models import User, Subscription, BusinessProfile, SubscriptionType, BusinessType

def create_test_user():
    """Create a test user with TRIAL subscription and complete BusinessProfile"""

    app = create_app()

    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter_by(email='tester@usefylr.app').first()
        if existing_user:
            print("[X] User tester@usefylr.app already exists!")
            print(f"   User ID: {existing_user.id}")
            print(f"   Subscription: {existing_user.subscription_type.value if existing_user.subscription_type else 'None'}")

            # Offer to delete and recreate
            response = input("\nDelete and recreate? (yes/no): ")
            if response.lower() == 'yes':
                # Delete existing profile and subscription if they exist
                BusinessProfile.query.filter_by(user_id=existing_user.id).delete()
                Subscription.query.filter_by(user_id=existing_user.id).delete()
                db.session.delete(existing_user)
                db.session.commit()
                print("[OK] Existing user deleted")
            else:
                print("Aborted.")
                return

        # Create new user
        print("\n[*] Creating test user...")
        user = User(
            username='tester',
            email='tester@usefylr.app',
            password_hash=generate_password_hash('Password123!')
        )

        db.session.add(user)
        db.session.flush()  # Flush to get user.id

        # Create subscription record
        print("[*] Creating TRIAL subscription...")
        subscription = Subscription(
            user_id=user.id,
            subscription_type=SubscriptionType.TRIAL,
            status='active',
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30),  # 30-day trial
            stripe_subscription_id=f'trial_sub_{user.id}',  # Placeholder for trial
            stripe_customer_id=f'trial_cust_{user.id}'  # Placeholder for trial
        )
        db.session.add(subscription)

        # Create BusinessProfile with S-Corp in Trucking
        print("[*] Creating BusinessProfile (S-Corp, Trucking)...")
        profile = BusinessProfile(
            user_id=user.id,
            business_type=BusinessType.S_CORP,
            business_name='Test Trucking Solutions Inc.',
            industry='Trucking',
            annual_revenue=350000.00,  # $350k annual revenue
            operating_states=['TX'],  # Texas (JSON array)
            ein='12-3456789',  # Dummy EIN
            has_employees=True,
            employee_count=3,  # 3 employees
            has_home_office=True  # Has home office
        )
        db.session.add(profile)

        # Commit all changes
        db.session.commit()

        print("\n[OK] Test user created successfully!")
        print("\n" + "="*50)
        print("TEST USER CREDENTIALS")
        print("="*50)
        print(f"Email:    tester@usefylr.app")
        print(f"Password: Password123!")
        print(f"User ID:  {user.id}")
        print("\n" + "="*50)
        print("SUBSCRIPTION DETAILS")
        print("="*50)
        print(f"Tier:     TRIAL")
        print(f"Status:   active")
        print(f"Expires:  {subscription.current_period_end.strftime('%Y-%m-%d')}")
        print("\n" + "="*50)
        print("BUSINESS PROFILE")
        print("="*50)
        print(f"Entity:   S-Corporation")
        print(f"Name:     Test Trucking Solutions Inc.")
        print(f"Industry: Trucking")
        print(f"Revenue:  $350,000/year")
        print(f"State:    Texas")
        print(f"EIN:      12-3456789")
        print(f"Employees: 3")
        print(f"Home Office: Yes")
        print("\n" + "="*50)
        print("EXPECTED RESTRICTIONS (TRIAL TIER)")
        print("="*50)
        print("[X] Export Forms - Should redirect to /pricing")
        print("[X] Smart Ledger AI - Should show upgrade prompt")
        print("[X] 1099 Management - Should show upgrade prompt")
        print("[OK] AI Tax Assistant - Limited to 5 questions/month")
        print("[OK] Tax Calculator - Basic access only")
        print("\n" + "="*50)
        print("\nTest this user by:")
        print("1. Starting Flask: flask run")
        print("2. Navigate to: http://127.0.0.1:5000/auth/login")
        print("3. Login with credentials above")
        print("4. Try accessing:")
        print("   - Dashboard export button -> Should redirect to /pricing")
        print("   - Smart Ledger features -> Should show upgrade prompt")
        print("   - Contractor management -> Should show upgrade prompt")
        print("="*50)

        return user

if __name__ == "__main__":
    create_test_user()
