from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import os
import logging

# Import custom modules
from modules.smart_ledger import init_smart_ledger
# from ai.openai_interface import get_openai_response

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = "fylr_dev_secret_key"

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