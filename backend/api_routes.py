# .fylr Flask API Routes
# Complete backend API for all core features

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
import os
import json

# Import the core components
from core_components import (
    User, TaxForm, SmartLedgerEntry, 
    AITaxAssistant, SmartLedger, TaxFormGenerator, SubscriptionManager,
    Base, create_engine
)

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    CORS(app)

    # Database setup
    database_url = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/fylr')
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    # Initialize components
    ai_assistant = AITaxAssistant(os.getenv('OPENAI_API_KEY'))
    form_generator = TaxFormGenerator()
    subscription_manager = SubscriptionManager(os.getenv('STRIPE_SECRET_KEY'))

    # =============================================================================
    # AUTHENTICATION ROUTES
    # =============================================================================

    @app.route('/api/auth/register', methods=['POST'])
    def register():
        """Register new user"""
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        db = Session()
        try:
            # Check if user exists
            existing_user = db.query(User).filter_by(email=email).first()
            if existing_user:
                return jsonify({'error': 'User already exists'}), 400
            
            # Create new user
            user = User(
                email=email,
                password_hash=generate_password_hash(password),
                subscription_tier='trial'
            )
            db.add(user)
            db.commit()
            
            # Generate JWT token
            token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.utcnow() + timedelta(days=30)
            }, app.config['SECRET_KEY'], algorithm='HS256')
            
            return jsonify({
                'token': token,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'tier': user.subscription_tier
                }
            })
            
        except Exception as e:
            db.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            db.close()

    @app.route('/api/auth/login', methods=['POST'])
    def login():
        """User login"""
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        db = Session()
        try:
            user = db.query(User).filter_by(email=email).first()
            
            if not user or not check_password_hash(user.password_hash, password):
                return jsonify({'error': 'Invalid credentials'}), 401
            
            token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.utcnow() + timedelta(days=30)
            }, app.config['SECRET_KEY'], algorithm='HS256')
            
            return jsonify({
                'token': token,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'tier': user.subscription_tier
                }
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            db.close()

    # =============================================================================
    # TAX FORM ROUTES
    # =============================================================================

    @app.route('/api/forms/create/<form_type>', methods=['POST'])
    def create_form(form_type):
        """Create or retrieve existing tax form"""
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
        
        db = Session()
        try:
            # Check if form already exists
            existing_form = db.query(TaxForm).filter_by(
                user_id=user_id, 
                form_type=form_type
            ).first()
            
            if existing_form:
                # Return existing form
                form_template = form_generator.form_templates.get(form_type)
                return jsonify({
                    'template': form_template,
                    'data': existing_form.form_data,
                    'completion_percentage': existing_form.completion_percentage,
                    'form_id': existing_form.id
                })
            
            # Create new form
            form_data = form_generator.create_form(form_type, user_id)
            
            # Save to database
            tax_form = TaxForm(
                user_id=user_id,
                form_type=form_type,
                form_data=form_data['data'],
                completion_percentage=form_data['completion_percentage']
            )
            db.add(tax_form)
            db.commit()
            
            return jsonify({
                'template': form_data['template'],
                'data': form_data['data'],
                'completion_percentage': form_data['completion_percentage'],
                'form_id': tax_form.id
            })
            
        except Exception as e:
            db.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            db.close()

    @app.route('/api/forms/update/<int:form_id>', methods=['PUT'])
    def update_form(form_id):
        """Update form data"""
        data = request.get_json()
        form_data = data.get('form_data')
        
        db = Session()
        try:
            tax_form = db.query(TaxForm).get(form_id)
            if not tax_form:
                return jsonify({'error': 'Form not found'}), 404
            
            # Update form data
            tax_form.form_data = form_data
            tax_form.updated_at = datetime.utcnow()
            
            # Recalculate completion percentage
            template = form_generator.form_templates.get(tax_form.form_type)
            if template:
                completion = form_generator._calculate_completion(form_data, template)
                tax_form.completion_percentage = completion
            
            db.commit()
            
            return jsonify({
                'success': True,
                'completion_percentage': tax_form.completion_percentage
            })
            
        except Exception as e:
            db.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            db.close()

    # =============================================================================
    # AI GUIDANCE ROUTES
    # =============================================================================

    @app.route('/api/ai/guidance', methods=['POST'])
    def get_ai_guidance():
        """Get AI guidance for tax form completion"""
        data = request.get_json()
        form_type = data.get('form_type')
        form_data = data.get('form_data')
        user_id = data.get('user_id')
        
        db = Session()
        try:
            # Get user profile
            user = db.query(User).get(user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            user_profile = user.business_profile or {}
            
            # Get AI guidance based on form type
            if form_type == 'schedule_c':
                guidance = ai_assistant.get_schedule_c_guidance(user_profile, form_data)
            else:
                guidance = {'message': 'AI guidance not available for this form type yet'}
            
            return jsonify(guidance)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            db.close()

    # =============================================================================
    # SMART LEDGER ROUTES
    # =============================================================================

    @app.route('/api/smart-ledger/add-expense', methods=['POST'])
    def add_expense():
        """Add expense to smart ledger with AI categorization"""
        data = request.get_json()
        user_id = data.get('user_id')
        amount = data.get('amount')
        description = data.get('description')
        date_str = data.get('date')
        
        if not all([user_id, amount, description]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        db = Session()
        try:
            # Parse date
            expense_date = datetime.fromisoformat(date_str.replace('Z', '+00:00')) if date_str else datetime.now()
            
            # Get user business type
            user = db.query(User).get(user_id)
            business_profile = user.business_profile or {}
            business_type = business_profile.get('entity_type', 'sole_proprietorship')
            
            # Initialize smart ledger
            smart_ledger = SmartLedger(db, ai_assistant)
            
            # Add expense with AI categorization
            result = smart_ledger.add_expense(
                user_id=user_id,
                amount=float(amount),
                description=description,
                date=expense_date,
                business_type=business_type
            )
            
            return jsonify(result)
            
        except Exception as e:
            db.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            db.close()

    @app.route('/api/smart-ledger/expenses/<int:user_id>', methods=['GET'])
    def get_expenses(user_id):
        """Get user's smart ledger expenses"""
        db = Session()
        try:
            entries = db.query(SmartLedgerEntry).filter_by(user_id=user_id).order_by(
                SmartLedgerEntry.date.desc()
            ).limit(50).all()
            
            expenses = [
                {
                    'id': entry.id,
                    'amount': entry.amount,
                    'description': entry.description,
                    'category': entry.category,
                    'tax_deductible': entry.tax_deductible,
                    'ai_confidence': entry.ai_confidence,
                    'date': entry.date.isoformat(),
                    'created_at': entry.created_at.isoformat()
                }
                for entry in entries
            ]
            
            return jsonify({'expenses': expenses})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            db.close()

    @app.route('/api/smart-ledger/tax-readiness/<int:user_id>', methods=['GET'])
    def get_tax_readiness(user_id):
        """Get user's tax readiness score"""
        db = Session()
        try:
            smart_ledger = SmartLedger(db, ai_assistant)
            score_data = smart_ledger.get_tax_readiness_score(user_id)
            return jsonify(score_data)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            db.close()

    # =============================================================================
    # SUBSCRIPTION ROUTES
    # =============================================================================

    @app.route('/api/subscription/upgrade-trigger', methods=['POST'])
    def check_upgrade_trigger():
        """Check if user should see upgrade prompt"""
        data = request.get_json()
        current_tier = data.get('current_tier', 'trial')
        estimated_savings = data.get('estimated_savings', 0)
        completion_percentage = data.get('completion_percentage', 0)
        
        try:
            trigger_data = subscription_manager.check_upgrade_trigger(
                current_tier, estimated_savings, completion_percentage
            )
            return jsonify(trigger_data)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/subscription/create', methods=['POST'])
    def create_subscription():
        """Create new subscription"""
        data = request.get_json()
        user_email = data.get('email')
        tier = data.get('tier')
        
        if not user_email or not tier:
            return jsonify({'error': 'Email and tier required'}), 400
        
        try:
            result = subscription_manager.create_subscription(user_email, tier)
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # =============================================================================
    # HEALTH CHECK
    # =============================================================================

    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        })

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)