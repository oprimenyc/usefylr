import enum
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.app import db

class UserPlan(enum.Enum):
    FREE = "free"
    BUSINESS_BUILDER = "business_builder"
    STANDARD = "standard"
    
class TaxFormType(enum.Enum):
    FORM_1120 = "1120"
    FORM_1065 = "1065"
    SCHEDULE_C = "Schedule C"
    
class LetterType(enum.Enum):
    PENALTY_ABATEMENT = "penalty_abatement"
    REASONABLE_CAUSE = "reasonable_cause"
    LATE_FILING_RELIEF = "late_filing_relief"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    wordpress_id = db.Column(db.Integer, nullable=True)
    plan = db.Column(db.Enum(UserPlan), default=UserPlan.FREE)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subscription_member = db.Column(db.Boolean, default=False)
    
    # Relationships
    subscriptions = db.relationship('Subscription', backref='user', lazy=True)
    payments = db.relationship('Payment', backref='user', lazy=True)
    tax_forms = db.relationship('TaxForm', backref='user', lazy=True)
    irs_letters = db.relationship('IRSLetter', backref='user', lazy=True)
    tax_strategies = db.relationship('TaxStrategy', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_access_level(self):
        if self.plan == UserPlan.BUSINESS_BUILDER:
            return "full_access"
        elif self.subscription_member:
            return "discounted"
        else:
            return "standard"
    
    def has_paid(self, feature, discounted=False):
        # Check if user has paid for a specific feature
        for payment in self.payments:
            if payment.feature == feature and payment.status == "completed":
                return True
                
        # Check for active subscriptions that include the feature
        for subscription in self.subscriptions:
            if subscription.status == "active":
                # Business builder includes all features
                if subscription.plan_name == "business_builder":
                    return True
                # Check if feature is included in the subscription
                if feature in subscription.features.split(','):
                    return True
                    
        return False
    
    def __repr__(self):
        return f'<User {self.username}>'

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stripe_subscription_id = db.Column(db.String(120), unique=True, nullable=True)
    plan_name = db.Column(db.String(64), nullable=False)
    features = db.Column(db.String(256), nullable=True)  # Comma-separated list of included features
    starts_at = db.Column(db.DateTime, default=datetime.utcnow)
    ends_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(30), default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Subscription {self.plan_name}>'

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stripe_payment_id = db.Column(db.String(120), unique=True, nullable=True)
    amount = db.Column(db.Float, nullable=False)
    feature = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(30), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Payment ${self.amount} for {self.feature}>'

class TaxForm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    form_type = db.Column(db.Enum(TaxFormType), nullable=False)
    tax_year = db.Column(db.Integer, nullable=False)
    data = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(30), default="draft")
    pdf_path = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<TaxForm {self.form_type.value} for {self.tax_year}>'

class IRSLetter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    letter_type = db.Column(db.Enum(LetterType), nullable=False)
    data = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(30), default="draft")
    pdf_path = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<IRSLetter {self.letter_type.value}>'

class TaxStrategy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    strategy_name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    estimated_savings = db.Column(db.Float, nullable=True)
    answers = db.Column(db.JSON, nullable=True)
    status = db.Column(db.String(30), default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<TaxStrategy {self.strategy_name}>'

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(64), nullable=False)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AuditLog {self.action}>'