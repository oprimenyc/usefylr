from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import custom modules
from modules.smart_ledger import init_smart_ledger
# from ai.openai_interface import get_openai_response

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fylr_dev_secret_key")

# Initialize modules
init_smart_ledger(app)

# Available form templates
FORM_TEMPLATES = {
    'schedule_c': {
        'id': 'schedule_c',
        'title': 'Schedule C - Profit or Loss From Business',
        'description': 'Use Schedule C to report income or loss from a business you operated or a profession you practiced as a sole proprietor.'
    },
    'schedule_se': {
        'id': 'schedule_se',
        'title': 'Schedule SE - Self-Employment Tax',
        'description': 'Use Schedule SE to figure the tax due on net earnings from self-employment.'
    }
}

def load_form_template(form_id):
    """Load a form template from JSON file"""
    template_path = f"form_templates/{form_id}.json"
    if not os.path.exists(template_path):
        return None
    with open(template_path, 'r') as f:
        return json.load(f)

@app.route('/')
def index():
    """Premium dark theme homepage"""
    return render_template('premium_homepage.html')

@app.route('/form-demo')
def form_demo():
    form_id = request.args.get('form_id')
    section = request.args.get('section', 0, type=int)
    
    form_template = None
    if form_id:
        form_template = load_form_template(form_id)
    
    return render_template(
        'form_demo.html',
        form_templates=FORM_TEMPLATES,
        selected_form_id=form_id,
        form_template=form_template,
        current_section=section
    )

@app.route('/smart-ledger')
def smart_ledger():
    """Smart Ledger with AI categorization"""
    return render_template('smart_ledger.html')

@app.route('/tax-form-builder')
def tax_form_builder():
    """AI-guided tax form builder"""
    return render_template('tax_form_builder.html')

@app.route('/dashboard')
def dashboard():
    """Premium dashboard"""
    return render_template('premium_dashboard.html')

@app.route('/react-dashboard')
def react_dashboard():
    """React-powered dashboard with integrated components"""
    return render_template('react_dashboard.html')

# =============================================================================
# BACKEND API INTEGRATION
# =============================================================================

@app.route('/api/smart-ledger/add-expense', methods=['POST'])
def api_add_expense():
    """API endpoint for adding expenses"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'demo-user')
        amount = float(data.get('amount', 0))
        description = data.get('description', '')
        date_str = data.get('date', '')
        
        # Mock AI categorization for demo
        ai_analysis = {
            'category': 'Office Supplies' if 'office' in description.lower() else 'Business Expense',
            'confidence': 0.89,
            'deductible_percentage': 100,
            'explanation': 'Categorized using intelligent pattern recognition',
            'special_considerations': 'Ensure proper documentation for audit purposes'
        }
        
        # Mock tax savings calculation
        tax_savings_estimate = amount * 0.25  # 25% tax rate assumption
        
        return jsonify({
            'entry_id': f'exp_{len(description)}_{amount}',
            'ai_analysis': ai_analysis,
            'tax_savings_estimate': tax_savings_estimate,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/smart-ledger/tax-readiness/<user_id>', methods=['GET'])
def api_tax_readiness(user_id):
    """Get tax readiness score"""
    try:
        # Mock tax readiness score
        return jsonify({
            'score': 75,
            'total_entries': 23,
            'categorized_entries': 20,
            'entries_with_receipts': 15,
            'recommendations': [
                'Upload receipts for recent expenses',
                'Review AI categorizations monthly',
                'Track business mileage'
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/forms/create/<form_type>', methods=['POST'])
def api_create_form(form_type):
    """Create tax form"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'demo-user')
        
        # Load form template
        template = load_form_template(form_type)
        if not template:
            return jsonify({'error': 'Form template not found'}), 404
        
        # Initialize empty form data
        form_data = {}
        completion_percentage = 0
        
        return jsonify({
            'template': template,
            'data': form_data,
            'completion_percentage': completion_percentage,
            'form_id': f'{form_type}_{user_id}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/guidance', methods=['POST'])
def api_ai_guidance():
    """Get AI guidance for form completion"""
    try:
        data = request.get_json()
        field_context = data.get('field_context', 'general')
        
        # Mock AI guidance response
        response = {
            'explanation': f'For {field_context}: This field is used to report your business income/expenses. Ensure accuracy as this affects your tax liability.',
            'tax_implications': 'This amount will be included in your Schedule C calculations.',
            'common_mistakes': 'Common mistakes include double-counting expenses or mixing personal and business items.',
            'confidence': 88,
            'suggestions': ['Review supporting documentation', 'Consider quarterly estimates']
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/subscription/upgrade-trigger', methods=['POST'])
def api_upgrade_trigger():
    """Check upgrade trigger conditions"""
    try:
        data = request.get_json()
        current_tier = data.get('current_tier', 'trial')
        estimated_savings = data.get('estimated_savings', 0)
        completion_percentage = data.get('completion_percentage', 0)
        
        trigger = None
        
        # Check if upgrade trigger should be shown
        if current_tier == 'trial' and (estimated_savings > 1000 or completion_percentage > 50):
            if estimated_savings > 1000:
                trigger = {
                    'message': f'You\'ve found ${estimated_savings:,.0f} in potential savings! Upgrade to unlock advanced tax strategies.',
                    'cta': 'Upgrade to Guided - $197',
                    'suggested_tier': 'guided',
                    'urgency': 'high'
                }
            else:
                trigger = {
                    'message': f'You\'re {completion_percentage}% complete! Upgrade for AI-guided completion and audit protection.',
                    'cta': 'Upgrade to Guided - $197', 
                    'suggested_tier': 'guided',
                    'urgency': 'medium'
                }
        
        return jsonify({'trigger': trigger})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def api_health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': '2025-01-01T00:00:00Z',
        'version': '1.0.0',
        'environment': os.environ.get('FLASK_ENV', 'development')
    })

@app.route('/pricing')
def pricing():
    """Pricing page"""
    return render_template('pricing.html')

@app.route('/legal/disclaimer')
def legal_disclaimer():
    """Legal disclaimer page"""
    return render_template('legal/legal_disclaimer.html')

# API Routes
@app.route('/api/ai-guidance', methods=['POST'])
def ai_guidance():
    """AI guidance for form fields"""
    try:
        data = request.get_json()
        field_context = data.get('context', '')
        user_input = data.get('input', '')
        
        prompt = f"""
        Provide helpful tax guidance for this field:
        Field Context: {field_context}
        User Input: {user_input}
        
        Provide:
        1. Brief explanation of this field
        2. Tax implications
        3. Common mistakes to avoid
        4. Confidence level (0-100%)
        
        Keep response concise and actionable.
        """
        
        # Mock AI response for demo (replace with actual OpenAI when API key is configured)
        response = {
            'explanation': f'For {field_context}: This field is used to report your business income/expenses. Ensure accuracy as this affects your tax liability.',
            'tax_implications': 'This amount will be included in your Schedule C calculations.',
            'common_mistakes': 'Common mistakes include double-counting expenses or mixing personal and business items.',
            'confidence': 88
        }
        
        return jsonify(response or {'error': 'AI guidance unavailable'})
        
    except Exception as e:
        logging.error(f"AI guidance error: {str(e)}")
        return jsonify({'error': 'Guidance unavailable'}), 500

@app.route('/api/validate-form', methods=['POST'])
def validate_form():
    """Validate form data with AI"""
    try:
        form_data = request.get_json()
        
        # Basic validation logic
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        # Add validation logic here
        
        return jsonify(validation_results)
        
    except Exception as e:
        logging.error(f"Form validation error: {str(e)}")
        return jsonify({'error': 'Validation failed'}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)