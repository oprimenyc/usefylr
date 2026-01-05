"""
Database Models

This module defines the database models for the .fylr tax platform.
"""

from app import db
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import enum

class UserPlan(enum.Enum):
    """User subscription plan levels"""
    SELF_SERVICE = "self_service"
    GUIDED = "guided" 
    CONCIERGE = "concierge"

class BusinessType(enum.Enum):
    """Business entity types"""
    SOLE_PROPRIETOR = "sole_proprietor"
    LLC = "llc"
    S_CORP = "s_corp"
    C_CORP = "c_corp"

class TaxFormType(enum.Enum):
    """Tax form types"""
    SCHEDULE_C = "schedule_c"
    SCHEDULE_SE = "schedule_se"
    FORM_1065 = "1065"
    FORM_1120S = "1120s"
    FORM_1120 = "1120"
    FORM_4562 = "4562"
    FORM_8825 = "8825"
    FORM_8832 = "8832"
    FORM_2553 = "2553"
    FORM_941 = "941"
    FORM_940 = "940"
    FORM_W2 = "w2"
    FORM_W3 = "w3"
    FORM_1099NEC = "1099nec"
    FORM_1099MISC = "1099misc"
    FORM_1096 = "1096"

class SubscriptionType(enum.Enum):
    """Subscription plan types for Stripe integration"""
    SELF_SERVICE = "self_service"
    GUIDED = "guided"
    CONCIERGE = "concierge"
    TRIAL = "trial"
    CANCELLED = "cancelled"

class User(UserMixin, db.Model):
    """User model"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # User subscription information
    plan = db.Column(db.Enum(UserPlan), default=UserPlan.SELF_SERVICE)
    has_audit_protection = db.Column(db.Boolean, default=False)
    plan_expiry = db.Column(db.DateTime)
    
    # Stripe customer information
    stripe_customer_id = db.Column(db.String(128))
    stripe_subscription_id = db.Column(db.String(128))
    
    # WordPress integration information (if applicable)
    wp_user_id = db.Column(db.String(128))
    
    # Relationships
    business_profile = db.relationship('BusinessProfile', backref='user', uselist=False)
    tax_forms = db.relationship('TaxForm', backref='user')
    tax_strategies = db.relationship('TaxStrategy', backref='user')
    subscriptions = db.relationship('Subscription', backref='user', lazy='dynamic')

    def has_paid(self) -> bool:
        """
        Check if user has an active paid subscription.

        Returns:
            bool: True if user has active subscription, False otherwise
        """
        active_subscription = self.subscriptions.filter_by(status='active').first()
        return active_subscription is not None

    def has_feature(self, feature_name: str) -> bool:
        """
        Check if user's subscription includes a specific feature.

        Feature access by subscription type:
        - SELF_SERVICE: basic features only
        - GUIDED: includes AI assistance, export forms
        - CONCIERGE: includes all features plus audit protection

        Args:
            feature_name: Feature to check (e.g., 'export_forms', 'smart_ledger_ai', 'audit_protection')

        Returns:
            bool: True if user has access to the feature, False otherwise
        """
        active_subscription = self.subscriptions.filter_by(status='active').first()

        if not active_subscription:
            return False

        # Feature matrix by subscription type
        feature_map = {
            SubscriptionType.SELF_SERVICE: [
                'basic_forms',
                'tax_calculator',
            ],
            SubscriptionType.GUIDED: [
                'basic_forms',
                'tax_calculator',
                'export_forms',
                'smart_ledger_ai',
                'tax_optimization',
            ],
            SubscriptionType.CONCIERGE: [
                'basic_forms',
                'tax_calculator',
                'export_forms',
                'smart_ledger_ai',
                'tax_optimization',
                'audit_protection',
                'priority_support',
                'tax_strategy_consultation',
            ],
            SubscriptionType.TRIAL: [
                'basic_forms',
                'tax_calculator',
                'export_forms',
                'smart_ledger_ai',
            ],
        }

        allowed_features = feature_map.get(active_subscription.subscription_type, [])
        return feature_name in allowed_features

    def __repr__(self):
        return f'<User {self.username}>'

class BusinessProfile(db.Model):
    """Business profile model"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # Business information
    business_name = db.Column(db.String(128))
    business_type = db.Column(db.Enum(BusinessType), default=BusinessType.SOLE_PROPRIETOR)
    ein = db.Column(db.String(20))
    business_address = db.Column(db.Text)
    business_phone = db.Column(db.String(20))
    business_email = db.Column(db.String(120))
    
    # Industry and financial information
    industry = db.Column(db.String(64))
    annual_revenue = db.Column(db.Float, default=0.0)
    tax_year = db.Column(db.Integer, default=datetime.utcnow().year)
    
    # Additional business details
    has_employees = db.Column(db.Boolean, default=False)
    employee_count = db.Column(db.Integer, default=0)
    contractor_count = db.Column(db.Integer, default=0)
    operating_states = db.Column(JSONB)  # Stored as JSON array of state codes
    
    # Deduction-relevant fields
    has_home_office = db.Column(db.Boolean, default=False)
    has_vehicle = db.Column(db.Boolean, default=False)
    has_travel_expenses = db.Column(db.Boolean, default=False)
    has_equipment_purchases = db.Column(db.Boolean, default=False)
    
    # Risk factors
    high_cash_transactions = db.Column(db.Boolean, default=False)
    reported_losses = db.Column(db.Integer, default=0)  # Number of years with losses
    large_charitable_contributions = db.Column(db.Boolean, default=False)
    vehicle_deduction = db.Column(db.Float, default=0.0)
    
    # Optimization opportunities
    expense_ratio = db.Column(db.Float)  # Expenses / Revenue
    potential_deductions = db.Column(JSONB)  # JSON array of potential deduction categories
    
    # Additional financial data
    has_capital_gains = db.Column(db.Boolean, default=False)
    has_capital_losses = db.Column(db.Boolean, default=False)
    
    # Document completeness indicators
    missing_receipts = db.Column(db.Boolean, default=False)
    incomplete_records = db.Column(db.Boolean, default=False)
    
    # Extended data storage
    data = db.Column(JSONB)  # For extensibility without schema changes
    
    def __repr__(self):
        return f'<BusinessProfile {self.business_name}>'

class TaxForm(db.Model):
    """Tax form model"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    form_type = db.Column(db.Enum(TaxFormType), nullable=False)
    tax_year = db.Column(db.Integer, default=datetime.utcnow().year - 1)  # Previous tax year by default
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # Form status
    status = db.Column(db.String(20), default='draft')  # draft, complete, filed, etc.
    
    # Form data
    data = db.Column(JSONB)  # Stores the actual form data as JSON
    
    # Validation results
    validation_results = db.Column(JSONB)  # JSON object containing validation results
    
    def __repr__(self):
        return f'<TaxForm {self.form_type.name} {self.tax_year}>'

class TaxStrategy(db.Model):
    """Tax strategy model"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Strategy information
    strategy_name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    estimated_savings = db.Column(db.String(64))  # Could be a range or "Varies"
    implementation_steps = db.Column(JSONB)  # JSON array of implementation steps
    qualifications = db.Column(JSONB)  # JSON array of qualifications or limitations
    
    # Metadata
    tax_year = db.Column(db.Integer, default=datetime.utcnow().year - 1)
    tier = db.Column(db.String(20), default='basic')  # Which subscription tier this strategy is for
    
    # Extended data storage
    data = db.Column(JSONB)  # For storing additional contextual data
    
    def __repr__(self):
        return f'<TaxStrategy {self.strategy_name}>'

class AccountingConnection(db.Model):
    """Model for storing accounting software connections"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    platform = db.Column(db.String(64), nullable=False)  # quickbooks, xero, etc.
    connected_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_sync = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')
    
    # Connection credentials (encrypted in production)
    credentials = db.Column(JSONB)
    
    # Metadata
    data = db.Column(JSONB)  # Additional metadata about the connection
    
    def __repr__(self):
        return f'<AccountingConnection {self.platform}>'

class DataImport(db.Model):
    """Model for storing accounting data import records"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    platform = db.Column(db.String(64), nullable=False)
    data_type = db.Column(db.String(64), nullable=False)  # e.g., chart_of_accounts, profit_loss
    tax_year = db.Column(db.Integer, nullable=False)
    imported_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='success')
    records_count = db.Column(db.Integer)
    
    # Import results and data
    results = db.Column(JSONB)
    data = db.Column(JSONB)  # The actual imported data
    
    def __repr__(self):
        return f'<DataImport {self.platform} {self.data_type} {self.tax_year}>'

class QuestionnaireResponse(db.Model):
    """Model for storing tax questionnaire responses"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Questionnaire metadata
    tax_year = db.Column(db.Integer, default=datetime.utcnow().year - 1)
    questionnaire_type = db.Column(db.String(64))  # e.g., business_info, deductions, etc.

    # Response data
    responses = db.Column(JSONB)  # JSON object containing question IDs and responses

    def __repr__(self):
        return f'<QuestionnaireResponse {self.questionnaire_type} {self.tax_year}>'

class Subscription(db.Model):
    """Model for storing user subscriptions"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Stripe subscription information
    stripe_subscription_id = db.Column(db.String(128), unique=True, nullable=False)
    stripe_customer_id = db.Column(db.String(128), nullable=False)
    stripe_price_id = db.Column(db.String(128))

    # Subscription details
    subscription_type = db.Column(db.Enum(SubscriptionType), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # active, cancelled, past_due, trialing

    # Billing cycle
    current_period_start = db.Column(db.DateTime)
    current_period_end = db.Column(db.DateTime)
    cancel_at_period_end = db.Column(db.Boolean, default=False)
    cancelled_at = db.Column(db.DateTime)

    # Trial information
    trial_start = db.Column(db.DateTime)
    trial_end = db.Column(db.DateTime)

    # Features
    has_audit_protection = db.Column(db.Boolean, default=False)

    # Relationships
    payments = db.relationship('Payment', backref='subscription', lazy='dynamic')

    # Extended data storage
    metadata = db.Column(JSONB)  # Additional subscription metadata from Stripe

    def __repr__(self):
        return f'<Subscription {self.subscription_type.value} - {self.status}>'

class Payment(db.Model):
    """Model for storing payment transactions"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Stripe payment information
    stripe_payment_id = db.Column(db.String(128), unique=True, nullable=False)
    stripe_payment_intent_id = db.Column(db.String(128))
    stripe_charge_id = db.Column(db.String(128))

    # Payment details
    amount = db.Column(db.Float, nullable=False)  # Amount in dollars
    currency = db.Column(db.String(3), default='usd')
    status = db.Column(db.String(20), nullable=False)  # succeeded, failed, pending, refunded

    # Payment metadata
    description = db.Column(db.String(256))
    receipt_url = db.Column(db.String(512))

    # Subscription link (if payment is for a subscription)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscription.id'))

    # Extended data storage
    metadata = db.Column(JSONB)  # Additional payment metadata from Stripe

    def __repr__(self):
        return f'<Payment {self.stripe_payment_id} ${self.amount}>'

class AuditLog(db.Model):
    """Model for storing audit trail of critical actions"""
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # User information
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    username = db.Column(db.String(64))  # Denormalized for audit integrity

    # Action details
    action = db.Column(db.String(64), nullable=False, index=True)  # e.g., "user.login", "payment.created"
    resource_type = db.Column(db.String(64))  # e.g., "User", "Payment", "Subscription"
    resource_id = db.Column(db.Integer)

    # Request metadata
    ip_address = db.Column(db.String(45))  # IPv6 compatible
    user_agent = db.Column(db.String(256))

    # Status and result
    status = db.Column(db.String(20), nullable=False)  # success, failure, error
    error_message = db.Column(db.Text)

    # Extended data storage
    details = db.Column(JSONB)  # Additional context about the action

    def __repr__(self):
        return f'<AuditLog {self.action} by {self.username} - {self.status}>'