import enum
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.app import db

class UserPlan(enum.Enum):
    BASIC = "basic"   # Free or low-cost tier
    FYLR_PLUS = "fylr_plus"  # $47 tier
    PRO = "pro"  # $97-$197 tier
    
class TaxFormType(enum.Enum):
    FORM_1120 = "1120"
    FORM_1065 = "1065"
    SCHEDULE_C = "Schedule C"
    
class LetterType(enum.Enum):
    # Standard IRS response letters
    PENALTY_ABATEMENT = "penalty_abatement"
    REASONABLE_CAUSE = "reasonable_cause" 
    LATE_FILING_RELIEF = "late_filing_relief"
    
    # Advanced IRS response letters
    AUDIT_RESPONSE = "audit_response"
    CP2000_RESPONSE = "cp2000_response"
    INSTALLMENT_REQUEST = "installment_request"
    OFFER_IN_COMPROMISE = "offer_in_compromise"
    INNOCENT_SPOUSE_RELIEF = "innocent_spouse_relief"
    
    # Business tax notices
    EMPLOYMENT_TAX_ISSUE = "employment_tax_issue"
    BACKUP_WITHHOLDING = "backup_withholding"
    ESTIMATED_TAX_PENALTY = "estimated_tax_penalty"
    TRUST_FUND_RECOVERY = "trust_fund_recovery"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    wordpress_id = db.Column(db.Integer, nullable=True)
    plan = db.Column(db.Enum(UserPlan), default=UserPlan.BASIC)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subscription_member = db.Column(db.Boolean, default=False)
    
    # Relationships
    subscriptions = db.relationship('Subscription', backref='user', lazy=True)
    payments = db.relationship('Payment', backref='user', lazy=True)
    tax_forms = db.relationship('TaxForm', backref='user', lazy=True)
    irs_letters = db.relationship('IRSLetter', backref='user', lazy=True)
    tax_strategies = db.relationship('TaxStrategy', backref='user', lazy=True)
    legal_acknowledgments = db.relationship('LegalAcknowledgment', backref='user', lazy=True)
    
    # Additional fields for feature access
    has_acknowledged_disclaimer = db.Column(db.Boolean, default=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_access_level(self):
        if self.plan == UserPlan.PRO:
            return "pro"
        elif self.plan == UserPlan.FYLR_PLUS:
            return "plus"
        else:
            return "basic"
    
    def has_paid(self, feature):
        """
        Check if a user has access to a specific feature based on their plan.
        
        Args:
            feature: Can be a specific feature name or a plan tier ('pro', 'plus', 'basic')
            
        Returns:
            Boolean indicating if user has access to the feature
        """
        # If checking access level directly
        if feature in ['pro', 'fylr_pro', 'pro_tier']:
            return self.plan == UserPlan.PRO
            
        if feature in ['plus', 'fylr_plus', 'plus_tier']:
            return self.plan in [UserPlan.PRO, UserPlan.FYLR_PLUS]
            
        if feature in ['basic', 'basic_tier']:
            # All users have access to basic features
            return True
        
        # Pro tier users have access to all features
        if self.plan == UserPlan.PRO:
            return True
            
        # For .fylr+ tier, check specific premium features
        if self.plan == UserPlan.FYLR_PLUS:
            # Define .fylr+ (Plus) tier features
            fylr_plus_features = [
                'save_progress', 'resume_progress', 'smart_form_logic',
                'enhanced_ai_support', 'dynamic_checklist', 'export_forms',
                'priority_support'
            ]
            
            # Plus users have access to plus features and basic features
            if feature in fylr_plus_features or feature in ['plus', 'fylr_plus', 'plus_tier']:
                return True
                
        # Define Basic tier features (available to all users)
        basic_features = [
            'guided_input', 'auto_fill', 'generate_documents',
            'pdf_export', 'educational_guidance', 'form_generation'
        ]
        
        if feature in basic_features:
            return True
            
        # Define Pro-only features
        pro_features = [
            'ai_deduction_detection', 'ai_sorted_uploads', 
            'filing_export_support', 'audit_protection',
            'enhanced_audit_protection', 'priority_support'
        ]
        
        if feature in pro_features:
            # Only Pro users have access to these features
            return self.plan == UserPlan.PRO
            
        # Check for individual feature purchases (for a la carte purchases)
        payment = Payment.query.filter_by(
            user_id=self.id, 
            feature=feature, 
            status="completed"
        ).first()
        
        if payment:
            return True
            
        return False
    
    def __repr__(self):
        return f'<User {self.username}>'

class SubscriptionType(enum.Enum):
    BASIC = "basic"  # Free or low-cost tier
    FYLR_PLUS_MONTHLY = "fylr_plus_monthly"  # $47/month
    FYLR_PLUS_ONETIME = "fylr_plus_onetime"  # $47 one-time
    PRO_BASIC = "pro_basic"  # $97 one-time
    PRO_STANDARD = "pro_standard"  # $147 one-time
    PRO_PREMIUM = "pro_premium"  # $197 one-time

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stripe_subscription_id = db.Column(db.String(120), unique=True, nullable=True)
    subscription_type = db.Column(db.Enum(SubscriptionType), nullable=False)
    price = db.Column(db.Float, nullable=False)
    is_recurring = db.Column(db.Boolean, default=False)
    billing_period = db.Column(db.String(20), nullable=True)  # monthly, yearly, one-time
    starts_at = db.Column(db.DateTime, default=datetime.utcnow)
    ends_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(30), default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Subscription {self.subscription_type.value}>'

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

class LegalAcknowledgment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    acknowledged_accuracy = db.Column(db.Boolean, default=False)
    acknowledged_not_professional = db.Column(db.Boolean, default=False)
    acknowledged_no_liability = db.Column(db.Boolean, default=False)
    full_name = db.Column(db.String(100), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<LegalAcknowledgment by {self.full_name}>'

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(64), nullable=False)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AuditLog {self.action}>'