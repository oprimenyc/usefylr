from flask import Flask, render_template, request, redirect, url_for
import json
import os

app = Flask(__name__)
app.secret_key = "fylr_dev_secret_key"

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
    return redirect(url_for('form_demo'))

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fylr_dev_secret_key")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///fylr.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

# Initialize login manager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize components
init_auth(app)
init_routes(app)
init_form_library(app)
init_form_handler(app)

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
        
    # Get user's business profile
    business_profile = BusinessProfile.query.filter_by(user_id=current_user.id).first()
    
    # Get user's recent tax forms
    recent_forms = TaxForm.query.filter_by(user_id=current_user.id).order_by(TaxForm.updated_at.desc()).limit(5).all()
    
    # Get current tax year
    current_tax_year = datetime.now().year - 1  # Previous tax year
    
    return render_template(
        'dashboard.html',
        user=current_user,
        business_profile=business_profile,
        recent_forms=recent_forms,
        current_tax_year=current_tax_year
    )

@app.route('/legal/disclaimer')
def legal_disclaimer():
    return render_template('legal/legal_disclaimer.html')

@app.route('/legal/terms')
def terms():
    return render_template('legal/terms.html')

@app.route('/legal/privacy')
def privacy():
    return render_template('legal/privacy.html')

@app.route('/export')
def export():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
        
    form_ids = request.args.getlist('form_ids')
    form_types = request.args.getlist('form_types')
    
    # Get user's forms that match the criteria
    forms = []
    if form_ids:
        # Get specific forms by ID
        forms = TaxForm.query.filter(
            TaxForm.user_id == current_user.id,
            TaxForm.id.in_([int(id) for id in form_ids])
        ).all()
    elif form_types:
        # Get forms by type
        forms = TaxForm.query.filter(
            TaxForm.user_id == current_user.id,
            TaxForm.form_type.in_([TaxFormType[ft] for ft in form_types])
        ).all()
    else:
        # Get all user's forms
        forms = TaxForm.query.filter_by(user_id=current_user.id).all()
    
    return render_template(
        'export.html',
        forms=forms
    )

# Create database tables
with app.app_context():
    db.create_all()
    logging.info("Database tables created")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)