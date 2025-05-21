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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)