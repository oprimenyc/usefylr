"""
Feature routes for AI Chat, Smart Ledger, and Form Builder
"""
from flask import Blueprint, render_template

# Create blueprint for feature routes
features_bp = Blueprint('features', __name__)

# Questionnaire constants
BUSINESS_TYPES = {
    'sole_proprietor': 'Sole Proprietor',
    'llc_single': 'LLC (Single Member)',
    'llc_multi': 'LLC (Multiple Members)',
    's_corp': 'S Corporation',
    'c_corp': 'C Corporation',
    'partnership': 'Partnership'
}

STATES = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
    'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
    'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
    'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri',
    'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
    'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
    'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
    'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming',
    'DC': 'District of Columbia'
}

TAX_YEARS = list(range(2023, 2027))  # 2023-2026

@features_bp.route('/smart-ledger')
def smart_ledger():
    """Smart Ledger with AI categorization"""
    return render_template('smart_ledger.html')

@features_bp.route('/tax-form-builder')
def tax_form_builder():
    """AI-guided tax form builder"""
    return render_template('tax_form_builder.html')

@features_bp.route('/enhanced-smart-ledger')
def enhanced_smart_ledger():
    """Enhanced Smart Ledger with premium dark theme"""
    return render_template('enhanced_smart_ledger.html')

@features_bp.route('/ai-chat-test')
def ai_chat_test():
    """AI Chat Interface for testing tax questions"""
    return render_template('ai_chat_test.html')

@features_bp.route('/gorgeous-ai-chat')
def gorgeous_ai_chat():
    """Gorgeous AI Chat with beautiful tech company UI"""
    return render_template('gorgeous_ai_chat.html')

@features_bp.route('/clean-ai-chat')
def clean_ai_chat():
    """Clean AI Chat with fixed UX and readability issues"""
    return render_template('clean_ai_chat.html')

@features_bp.route('/fullwidth-ai-chat')
def fullwidth_ai_chat():
    """Full-Width AI Chat with no dead space or margins"""
    return render_template('fullwidth_ai_chat.html')

@features_bp.route('/form-demo')
def form_demo():
    """Form demo page"""
    return render_template('form_demo.html')

@features_bp.route('/questionnaire')
def questionnaire():
    """AI Tax Questionnaire - Start"""
    return render_template('questionnaire/start.html',
                          business_types=BUSINESS_TYPES,
                          states=STATES,
                          tax_years=TAX_YEARS)

@features_bp.route('/questionnaire/questions')
def questionnaire_questions():
    """AI Tax Questionnaire - Questions"""
    return render_template('questionnaire/index.html')

@features_bp.route('/questionnaire/results')
def questionnaire_results():
    """AI Tax Questionnaire - Results"""
    return render_template('questionnaire/results.html')
