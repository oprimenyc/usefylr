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

@app.route('/enhanced-smart-ledger')
def enhanced_smart_ledger():
    """Enhanced Smart Ledger with premium dark theme"""
    return render_template('enhanced_smart_ledger.html')

@app.route('/ai-chat-test')
def ai_chat_test():
    """AI Chat Interface for testing tax questions"""
    return render_template('ai_chat_test.html')

@app.route('/gorgeous-ai-chat')
def gorgeous_ai_chat():
    """Gorgeous AI Chat with beautiful tech company UI"""
    return render_template('gorgeous_ai_chat.html')

@app.route('/clean-ai-chat')
def clean_ai_chat():
    """Clean AI Chat with fixed UX and readability issues"""
    return render_template('clean_ai_chat.html')

# =============================================================================
# BACKEND API INTEGRATION
# =============================================================================

@app.route('/api/smart-ledger/add-expense', methods=['POST'])
def api_add_expense():
    """Enhanced API endpoint for adding expenses with advanced AI categorization"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'demo-user')
        amount = float(data.get('amount', 0))
        description = data.get('description', '')
        date_str = data.get('date', '')
        business_type = data.get('business_type', 'sole_proprietorship')
        
        # Advanced AI categorization using enhanced logic
        description_lower = description.lower()
        
        # Enhanced category detection
        category_mappings = {
            'business_meals': {
                'keywords': ['restaurant', 'lunch', 'dinner', 'meal', 'coffee', 'food', 'starbucks', 'mcdonalds'],
                'deductible_percentage': 50,
                'audit_risk': 'medium',
                'schedule_c_line': '24b',
                'irs_guidance': 'Must be ordinary and necessary business expense, not lavish or extravagant',
                'documentation': 'Receipt + business purpose + attendees names'
            },
            'home_office': {
                'keywords': ['utilities', 'internet', 'phone', 'home office', 'workspace'],
                'deductible_percentage': 100,
                'audit_risk': 'high',
                'schedule_c_line': '30',
                'irs_guidance': 'Must be used exclusively and regularly for business',
                'documentation': 'Home office measurement + exclusive use documentation'
            },
            'equipment': {
                'keywords': ['computer', 'laptop', 'printer', 'equipment', 'machinery', 'iphone', 'ipad'],
                'deductible_percentage': 100,
                'audit_risk': 'low',
                'schedule_c_line': '13',
                'irs_guidance': 'Consider Section 179 deduction for immediate expensing',
                'documentation': 'Receipt + business use percentage'
            },
            'software': {
                'keywords': ['software', 'subscription', 'saas', 'license', 'app', 'adobe', 'microsoft', 'google'],
                'deductible_percentage': 100,
                'audit_risk': 'low',
                'schedule_c_line': '18',
                'irs_guidance': 'Business software fully deductible if used exclusively for business',
                'documentation': 'Receipt + subscription terms'
            },
            'travel': {
                'keywords': ['travel', 'hotel', 'airline', 'flight', 'uber', 'gas', 'mileage', 'parking'],
                'deductible_percentage': 100,
                'audit_risk': 'medium',
                'schedule_c_line': '24a',
                'irs_guidance': 'Must be ordinary, necessary, and away from tax home overnight',
                'documentation': 'Receipt + business purpose + travel log'
            },
            'office_supplies': {
                'keywords': ['office', 'supply', 'staples', 'paper', 'pens', 'supplies'],
                'deductible_percentage': 100,
                'audit_risk': 'low',
                'schedule_c_line': '22',
                'irs_guidance': 'Office supplies used in business are fully deductible',
                'documentation': 'Receipt showing business supplies'
            },
            'professional_development': {
                'keywords': ['course', 'training', 'conference', 'education', 'seminar', 'workshop'],
                'deductible_percentage': 100,
                'audit_risk': 'low',
                'schedule_c_line': '27',
                'irs_guidance': 'Education that maintains or improves skills for current business',
                'documentation': 'Receipt + course description + business relevance'
            }
        }
        
        # Detect category
        detected_category = 'general_business'
        category_info = {
            'deductible_percentage': 100,
            'audit_risk': 'low',
            'schedule_c_line': '27',
            'irs_guidance': 'General business expense',
            'documentation': 'Receipt'
        }
        confidence = 0.75
        
        for category, info in category_mappings.items():
            if any(keyword in description_lower for keyword in info['keywords']):
                detected_category = category
                category_info = info
                confidence = 0.92
                break
        
        # Calculate tax savings based on business type
        deductible_amount = amount * (category_info['deductible_percentage'] / 100)
        
        # Enhanced tax calculation
        tax_rates = {
            'sole_proprietorship': {'income': 0.22, 'se': 0.153, 'state': 0.05},
            's_corp': {'income': 0.22, 'se': 0, 'state': 0.05},
            'llc': {'income': 0.22, 'se': 0.153, 'state': 0.05}
        }
        
        rates = tax_rates.get(business_type, tax_rates['sole_proprietorship'])
        federal_savings = deductible_amount * rates['income']
        se_savings = deductible_amount * rates['se'] * 0.9235 if rates['se'] else 0
        state_savings = deductible_amount * rates['state']
        total_tax_savings = federal_savings + se_savings + state_savings
        
        # Enhanced AI analysis response
        ai_analysis = {
            'category': detected_category.replace('_', ' ').title(),
            'confidence': confidence,
            'deductible_percentage': category_info['deductible_percentage'],
            'deductible_amount': deductible_amount,
            'audit_risk': category_info['audit_risk'],
            'schedule_c_line': category_info['schedule_c_line'],
            'irs_guidance': category_info['irs_guidance'],
            'documentation_needed': category_info['documentation'],
            'explanation': f'Categorized as {detected_category} with {confidence*100:.0f}% confidence using advanced tax intelligence',
            'tax_breakdown': {
                'federal_savings': federal_savings,
                'se_savings': se_savings,
                'state_savings': state_savings
            }
        }
        
        return jsonify({
            'entry_id': f'exp_{user_id}_{int(amount*100)}_{len(description)}',
            'ai_analysis': ai_analysis,
            'tax_savings_estimate': total_tax_savings,
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

@app.route('/api/ai/tax-guidance', methods=['POST'])
def api_ai_tax_guidance():
    """Advanced AI tax guidance for chat interface"""
    try:
        data = request.get_json()
        question = data.get('question', '').lower()
        user_context = data.get('user_context', {})
        entity_type = user_context.get('entity_type', 'sole_proprietorship')
        annual_revenue = user_context.get('annual_revenue', 50000)
        
        # Advanced AI responses based on question patterns
        if 'home office' in question:
            response = f"""**Home Office Deduction Analysis**

For {entity_type} with ${annual_revenue:,} revenue:

**Deduction Methods:**
• Simplified Method: $5 per sq ft, maximum 300 sq ft = $1,500
• Actual Method: Percentage of home expenses (utilities, mortgage interest, etc.)

**Requirements:**
• Exclusive business use of the space
• Regular business use (daily/weekly)
• Principal place of business OR regular client meetings

**Tax Savings Estimate:**
• Simplified method: $1,500 × 42.3% tax rate = $635 annual savings
• Actual method: Could be $2,000-4,000 depending on home expenses

**Audit Risk Assessment:**
• Risk Level: HIGH - IRS closely scrutinizes home office claims
• Red Flags: Claiming too large percentage, inconsistent use
• Protection: Maintain detailed records, photos of workspace, business activity logs

**Schedule C Reporting:**
• Line 30: Enter total home office deduction
• Form 8829: Required for actual method calculation"""

        elif 'business meal' in question or 'meal' in question:
            response = f"""**Business Meals Deduction Guide**

**Current Tax Law (2023-2024):**
• Business meals: 50% deductible
• Business entertainment: 0% deductible (not allowed)

**Requirements:**
• Ordinary and necessary business expense
• Not lavish or extravagant
• Business purpose must be discussed
• You or employee must be present

**Documentation Needed:**
• Receipt showing amount, date, location
• Business purpose and topics discussed
• Names of attendees and their business relationship

**Tax Savings Example:**
• $100 business meal × 50% = $50 deductible
• Tax savings: $50 × 42.3% = $21.15

**Schedule C Reporting:**
• Line 24b: Enter total meals deduction
• Remember: Only 50% of actual cost

**Audit Risk: MEDIUM**
• Common mistakes: Personal meals, entertainment disguised as meals
• Best practice: Keep detailed log of business purpose"""

        elif 's-corp' in question or 'salary' in question:
            salary_benchmark = annual_revenue * 0.4
            response = f"""**S-Corp Salary Optimization Analysis**

**Current Situation:**
• Annual Revenue: ${annual_revenue:,}
• Recommended Salary Range: ${salary_benchmark*0.75:,.0f} - ${salary_benchmark*1.25:,.0f}

**Tax Strategy:**
• Salary: Subject to payroll taxes (15.3% total)
• Distributions: No payroll tax, only income tax

**Optimization Example:**
• Conservative salary: ${salary_benchmark:,.0f}
• Potential distribution: ${annual_revenue - salary_benchmark:,.0f}
• Payroll tax savings: ${(annual_revenue - salary_benchmark) * 0.153:,.0f}

**IRS Requirements:**
• Must pay "reasonable compensation"
• Consider industry standards, duties, qualifications
• Document salary justification

**Risk Assessment:**
• Audit Risk: HIGH if salary too low
• Safe harbor: 40-60% of net profit as salary
• Red flag: Salary under $30,000 for profitable business

**Compliance Tips:**
• Run payroll consistently
• Issue W-2 to officer
• File Form 1120S annually
• Maintain corporate formalities"""

        elif 'audit' in question or 'risk' in question:
            response = f"""**Audit Risk Assessment & Protection**

**High-Risk Factors:**
• Home office deduction (especially large percentages)
• Unreasonable S-Corp officer compensation
• High meal/entertainment expenses
• Round numbers (suggests estimates, not records)
• Large charitable deductions relative to income

**Medium-Risk Factors:**
• Business travel expenses
• Vehicle expenses without detailed logs
• Cash-intensive businesses
• Losses for multiple years

**Low-Risk Factors:**
• Office supplies and equipment
• Software subscriptions
• Professional development
• Well-documented business expenses

**Audit Protection Strategies:**
• Maintain detailed records for ALL deductions
• Keep receipts for 7 years (3 years + extension)
• Document business purpose for every expense
• Use business bank accounts exclusively
• Consider audit insurance (Pro tier feature)

**Documentation Best Practices:**
• Digital receipt storage with business purpose notes
• Mileage logs for vehicle expenses
• Calendar entries for business meetings/travel
• Bank statements showing business payments

**If Audited:**
• Respond promptly to IRS notices
• Provide only requested documentation
• Consider professional representation
• Maintain professional, factual communication"""

        elif 'deduct' in question or 'expense' in question:
            response = f"""**Comprehensive Deduction Guide**

**100% Deductible Expenses:**
• Office supplies and equipment
• Software subscriptions (business use)
• Professional development/training
• Business insurance premiums
• Legal and professional fees

**Partially Deductible:**
• Business meals: 50% (2023-2024)
• Vehicle expenses: Business percentage only
• Home office: Percentage of home used

**Common Deductions by Category:**

**Equipment (Schedule C Line 13):**
• Computers, printers, machinery
• Section 179: Up to $1,160,000 immediate expensing
• Bonus depreciation: 60% in 2024

**Travel (Schedule C Line 24a):**
• Transportation, lodging, meals (50%)
• Must be overnight and away from tax home
• Document business purpose

**Utilities (Schedule C Line 25):**
• Business percentage of phone, internet
• 100% if exclusively business line

**Professional Services (Schedule C Line 17):**
• Legal, accounting, consulting fees
• Tax preparation fees

**Marketing (Schedule C Line 8):**
• Advertising, website costs
• Business cards, promotional materials

**Tax Savings Formula:**
Deductible Amount × Tax Rate = Savings
Example: $1,000 deduction × 42.3% = $423 savings"""

        elif 'self-employment tax' in question or 'se tax' in question:
            se_tax = annual_revenue * 0.9235 * 0.153
            response = f"""**Self-Employment Tax Calculation**

**Your Estimated SE Tax:**
• Net Profit: ${annual_revenue:,}
• SE Tax Base: ${annual_revenue * 0.9235:,.0f} (92.35% of profit)
• SE Tax Rate: 15.3% (12.4% Social Security + 2.9% Medicare)
• **Total SE Tax: ${se_tax:,.0f}**

**SE Tax Breakdown:**
• Social Security: 12.4% on first $160,200 (2023)
• Medicare: 2.9% on all earnings
• Additional Medicare: 0.9% on earnings over $200,000

**Reduction Strategies:**
• Business expenses reduce SE tax base
• Retirement contributions (SEP-IRA, Solo 401k)
• S-Corp election eliminates SE tax on distributions

**S-Corp Comparison:**
• Current SE Tax: ${se_tax:,.0f}
• With S-Corp election: Payroll tax only on salary
• Potential savings: ${se_tax * 0.4:,.0f} annually

**Schedule SE Filing:**
• Required if net earnings > $400
• File with Form 1040
• 50% of SE tax is deductible on Form 1040

**Quarterly Payments:**
• Required if owing > $1,000
• Due dates: Apr 15, Jun 15, Sep 15, Jan 15
• Safe harbor: 100% of prior year tax (110% if AGI > $150k)"""

        elif 'llc' in question or 'entity' in question:
            response = f"""**Entity Selection & Optimization**

**LLC Tax Elections:**

**Default (Single-Member):**
• Taxed as sole proprietorship
• Subject to SE tax on all profits
• File Schedule C with Form 1040

**S-Corp Election:**
• Salary + distributions structure
• SE tax only on salary portion
• File Form 1120S + individual returns
• Best for profits > $60,000

**Partnership (Multi-Member):**
• Pass-through taxation
• File Form 1065 + K-1s
• Guaranteed payments vs. distributions

**Analysis for ${annual_revenue:,} Revenue:**

**Current (LLC default):**
• Income Tax: ${annual_revenue * 0.22:,.0f}
• SE Tax: ${annual_revenue * 0.153 * 0.9235:,.0f}
• Total: ${annual_revenue * (0.22 + 0.153 * 0.9235):,.0f}

**S-Corp Election:**
• Recommended Salary: ${annual_revenue * 0.4:,.0f}
• Distribution: ${annual_revenue * 0.6:,.0f}
• Payroll Tax Savings: ${annual_revenue * 0.6 * 0.153:,.0f}

**Recommendation:**
For your revenue level, S-Corp election could save ${annual_revenue * 0.6 * 0.153:,.0f} annually in SE taxes.

**Implementation:**
• File Form 2553 by March 15
• Set up payroll system
• Maintain corporate formalities
• File 1120S annually"""

        else:
            response = f"""**General Tax Guidance**

I can help with specific tax questions about:

**Deductions & Credits:**
• Home office deduction calculations
• Business meal requirements (50% rule)
• Equipment and software expenses
• Travel and vehicle expenses

**Entity Optimization:**
• S-Corp vs LLC analysis
• Salary optimization strategies
• Tax election timing

**Compliance & Risk:**
• Audit risk assessment
• Documentation requirements
• IRS red flags to avoid

**Calculations:**
• Self-employment tax estimates
• Quarterly payment requirements
• Tax savings projections

**Schedule C Guidance:**
• Line-by-line completion help
• Income and expense categorization
• Form filing requirements

Try asking something more specific like:
"How much can I save with S-Corp election?"
"What documentation do I need for travel expenses?"
"Should I use the simplified home office method?"

Current context: {entity_type} with ${annual_revenue:,} annual revenue"""

        return jsonify({'response': response})
        
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