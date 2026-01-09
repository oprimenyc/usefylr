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

            # Get subscription info
            existing_sub = existing_user.subscriptions.filter_by(status='active').first()
            sub_info = existing_sub.subscription_type.value if existing_sub else 'None'
            print(f"   Subscription: {sub_info}")

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
            password_hash=generate_password_hash('FylrLaunch2026!')
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
        print("[*] Creating BusinessProfile (S-Corp, Trucking/Logistics)...")
        profile = BusinessProfile(
            user_id=user.id,
            business_type=BusinessType.S_CORP,
            business_name='Test Trucking Solutions Inc.',
            industry='Trucking / Logistics',
            annual_revenue=250000.00,  # $250k annual revenue
            operating_states=['TX'],  # Texas (JSON array)
            ein='12-3456789',  # Dummy EIN
            has_employees=True,
            employee_count=3,  # 3 employees
            has_home_office=True  # Has home office
        )
        db.session.add(profile)

        # Commit all changes
        db.session.commit()

        print("\n" + "="*60)
        print(" SUCCESS - VERIFIED TEST USER CREATED")
        print("="*60)
        print("\n[*] SANDBOX ACCOUNT FOR REVENUE GATE VERIFICATION")
        print("\n" + "-"*60)
        print("LOGIN CREDENTIALS")
        print("-"*60)
        print(f"  Email:    tester@usefylr.app")
        print(f"  Password: FylrLaunch2026!")
        print(f"  User ID:  {user.id}")
        print("\n" + "-"*60)
        print("SUBSCRIPTION STATUS")
        print("-"*60)
        print(f"  Tier:     TRIAL")
        print(f"  Status:   Active")
        print(f"  Expires:  {subscription.current_period_end.strftime('%Y-%m-%d')}")
        print("\n" + "-"*60)
        print("BUSINESS PROFILE")
        print("-"*60)
        print(f"  Entity Type:      S-Corporation")
        print(f"  Business Name:    Test Trucking Solutions Inc.")
        print(f"  Industry:         Trucking / Logistics")
        print(f"  Annual Revenue:   $250,000")
        print(f"  Operating State:  Texas")
        print(f"  EIN:              12-3456789")
        print(f"  Employees:        3")
        print(f"  Home Office:      Yes")
        print("\n" + "-"*60)
        print("PAYWALL VERIFICATION CHECKLIST (TRIAL TIER)")
        print("-"*60)
        print("  [BLOCKED] Export Forms -> Should redirect to /pricing")
        print("  [BLOCKED] Smart Ledger AI -> Should show upgrade prompt")
        print("  [BLOCKED] 1099 Management -> Should show upgrade prompt")
        print("  [LIMITED] AI Tax Assistant -> Limited to 5 questions/month")
        print("  [ACCESS]  Tax Calculator -> Basic access only")
        print("\n" + "="*60)
        print(" LOGIN URL")
        print("="*60)
        print("\n  http://127.0.0.1:5000/auth/login")
        print("\n" + "="*60)
        print("\n[*] To start the application:")
        print("    1. Run: flask run")
        print("    2. Open the login URL above")
        print("    3. Use the credentials shown above")
        print("\n[*] This account is ready for AI personalization testing")
        print("    and paywall verification.\n")
        print("="*60)

        return user

if __name__ == "__main__":
    create_test_user()
