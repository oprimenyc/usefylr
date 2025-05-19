"""
Form Library Module

This module provides reusable form components and templates for the tax application.
It includes dynamic form generation, validation, and specialized field types for tax forms.
"""
import os
import json
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, current_app, abort

class FormField:
    """Base class for form fields"""
    def __init__(self, name, label, required=False, help_text=None, validation=None, default=None):
        self.name = name
        self.label = label
        self.required = required
        self.help_text = help_text
        self.validation = validation or {}
        self.default = default
        
    def to_dict(self):
        """Convert field to dictionary representation"""
        return {
            'name': self.name,
            'label': self.label,
            'type': self.__class__.__name__.lower().replace('field', ''),
            'required': self.required,
            'help_text': self.help_text,
            'validation': self.validation,
            'default': self.default
        }
        
    def validate(self, value):
        """Validate field value"""
        errors = []
        
        # Check required
        if self.required and (value is None or value == ''):
            errors.append(f"{self.label} is required")
            
        return errors

class TextField(FormField):
    """Text input field"""
    def __init__(self, name, label, required=False, help_text=None, validation=None, default=None, placeholder=None, max_length=None):
        super().__init__(name, label, required, help_text, validation, default)
        self.placeholder = placeholder
        self.max_length = max_length
        
    def to_dict(self):
        field_dict = super().to_dict()
        field_dict.update({
            'placeholder': self.placeholder,
            'max_length': self.max_length
        })
        return field_dict
        
    def validate(self, value):
        errors = super().validate(value)
        
        # Check max length
        if value and self.max_length and len(value) > self.max_length:
            errors.append(f"{self.label} must be less than {self.max_length} characters")
        
        # Check pattern if specified
        if value and 'pattern' in self.validation:
            import re
            pattern = self.validation['pattern']
            if not re.match(pattern, value):
                error_message = self.validation.get('pattern_error', f"{self.label} has an invalid format")
                errors.append(error_message)
                
        return errors

class NumberField(FormField):
    """Numeric input field"""
    def __init__(self, name, label, required=False, help_text=None, validation=None, default=None, 
                min_value=None, max_value=None, step=None, currency=False, percentage=False):
        super().__init__(name, label, required, help_text, validation, default)
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.currency = currency
        self.percentage = percentage
        
    def to_dict(self):
        field_dict = super().to_dict()
        field_dict.update({
            'min_value': self.min_value,
            'max_value': self.max_value,
            'step': self.step,
            'currency': self.currency,
            'percentage': self.percentage
        })
        return field_dict
        
    def validate(self, value):
        errors = super().validate(value)
        
        # Skip validation if value is empty and not required
        if value in (None, '') and not self.required:
            return errors
            
        try:
            num_value = float(value)
            
            # Check min value
            if self.min_value is not None and num_value < self.min_value:
                errors.append(f"{self.label} must be at least {self.min_value}")
                
            # Check max value
            if self.max_value is not None and num_value > self.max_value:
                errors.append(f"{self.label} must be no more than {self.max_value}")
                
        except (ValueError, TypeError):
            errors.append(f"{self.label} must be a valid number")
            
        return errors

class DateField(FormField):
    """Date input field"""
    def __init__(self, name, label, required=False, help_text=None, validation=None, default=None,
                min_date=None, max_date=None, format='YYYY-MM-DD'):
        super().__init__(name, label, required, help_text, validation, default)
        self.min_date = min_date
        self.max_date = max_date
        self.format = format
        
    def to_dict(self):
        field_dict = super().to_dict()
        field_dict.update({
            'min_date': self.min_date,
            'max_date': self.max_date,
            'format': self.format
        })
        return field_dict
        
    def validate(self, value):
        errors = super().validate(value)
        
        # Skip validation if value is empty and not required
        if value in (None, '') and not self.required:
            return errors
            
        try:
            from datetime import datetime
            
            # Try to parse the date based on the format
            if self.format == 'YYYY-MM-DD':
                format_string = '%Y-%m-%d'
            elif self.format == 'MM/DD/YYYY':
                format_string = '%m/%d/%Y'
            else:
                format_string = '%Y-%m-%d'  # Default
                
            date_value = datetime.strptime(value, format_string)
            
            # Check min date
            if self.min_date:
                min_date = datetime.strptime(self.min_date, format_string)
                if date_value < min_date:
                    errors.append(f"{self.label} must be on or after {self.min_date}")
                    
            # Check max date
            if self.max_date:
                max_date = datetime.strptime(self.max_date, format_string)
                if date_value > max_date:
                    errors.append(f"{self.label} must be on or before {self.max_date}")
                    
        except ValueError:
            errors.append(f"{self.label} must be a valid date in {self.format} format")
            
        return errors

class SelectField(FormField):
    """Select dropdown field"""
    def __init__(self, name, label, options, required=False, help_text=None, validation=None, default=None, multiple=False):
        super().__init__(name, label, required, help_text, validation, default)
        self.options = options
        self.multiple = multiple
        
    def to_dict(self):
        field_dict = super().to_dict()
        field_dict.update({
            'options': self.options,
            'multiple': self.multiple
        })
        return field_dict
        
    def validate(self, value):
        errors = super().validate(value)
        
        # Skip validation if value is empty and not required
        if value in (None, '') and not self.required:
            return errors
            
        valid_values = [o['value'] for o in self.options]
        
        if self.multiple:
            # For multiple select, value should be a list
            if not isinstance(value, list):
                errors.append(f"{self.label} must have at least one selection")
            else:
                for val in value:
                    if val not in valid_values:
                        errors.append(f"{val} is not a valid option for {self.label}")
        else:
            # For single select
            if value not in valid_values:
                errors.append(f"{value} is not a valid option for {self.label}")
                
        return errors

class CheckboxField(FormField):
    """Checkbox field"""
    def __init__(self, name, label, required=False, help_text=None, validation=None, default=False):
        super().__init__(name, label, required, help_text, validation, default)
        
    def validate(self, value):
        errors = super().validate(value)
        
        # For checkbox, if required, it must be True
        if self.required and not value:
            errors.append(f"{self.label} must be checked")
            
        return errors

class RadioField(FormField):
    """Radio button field"""
    def __init__(self, name, label, options, required=False, help_text=None, validation=None, default=None):
        super().__init__(name, label, required, help_text, validation, default)
        self.options = options
        
    def to_dict(self):
        field_dict = super().to_dict()
        field_dict.update({
            'options': self.options
        })
        return field_dict
        
    def validate(self, value):
        errors = super().validate(value)
        
        # Skip validation if value is empty and not required
        if value in (None, '') and not self.required:
            return errors
            
        valid_values = [o['value'] for o in self.options]
        if value not in valid_values:
            errors.append(f"{value} is not a valid option for {self.label}")
            
        return errors

class TextareaField(FormField):
    """Textarea field for longer text input"""
    def __init__(self, name, label, required=False, help_text=None, validation=None, default=None, 
                rows=3, max_length=None, placeholder=None):
        super().__init__(name, label, required, help_text, validation, default)
        self.rows = rows
        self.max_length = max_length
        self.placeholder = placeholder
        
    def to_dict(self):
        field_dict = super().to_dict()
        field_dict.update({
            'rows': self.rows,
            'max_length': self.max_length,
            'placeholder': self.placeholder
        })
        return field_dict
        
    def validate(self, value):
        errors = super().validate(value)
        
        # Check max length
        if value and self.max_length and len(value) > self.max_length:
            errors.append(f"{self.label} must be less than {self.max_length} characters")
            
        return errors

class EINField(TextField):
    """Specialized field for Employer Identification Numbers"""
    def __init__(self, name="ein", label="Employer Identification Number (EIN)", required=False, 
                help_text="Enter your 9-digit EIN (XX-XXXXXXX)"):
        validation = {
            'pattern': r'^\d{2}-\d{7}$',
            'pattern_error': 'EIN must be in XX-XXXXXXX format'
        }
        super().__init__(name, label, required, help_text, validation, placeholder="XX-XXXXXXX")

class SSNField(TextField):
    """Specialized field for Social Security Numbers"""
    def __init__(self, name="ssn", label="Social Security Number (SSN)", required=False, 
                help_text="Enter your 9-digit SSN (XXX-XX-XXXX)"):
        validation = {
            'pattern': r'^\d{3}-\d{2}-\d{4}$',
            'pattern_error': 'SSN must be in XXX-XX-XXXX format'
        }
        super().__init__(name, label, required, help_text, validation, placeholder="XXX-XX-XXXX")

class PhoneField(TextField):
    """Specialized field for phone numbers"""
    def __init__(self, name, label="Phone Number", required=False, 
                help_text="Enter phone number in format (XXX) XXX-XXXX"):
        validation = {
            'pattern': r'^\(\d{3}\)\s\d{3}-\d{4}$',
            'pattern_error': 'Phone number must be in (XXX) XXX-XXXX format'
        }
        super().__init__(name, label, required, help_text, validation, placeholder="(XXX) XXX-XXXX")

class ZipCodeField(TextField):
    """Specialized field for ZIP codes"""
    def __init__(self, name, label="ZIP Code", required=False, help_text="Enter 5-digit ZIP code"):
        validation = {
            'pattern': r'^\d{5}(-\d{4})?$',
            'pattern_error': 'ZIP code must be 5 digits (XXXXX) or 9 digits (XXXXX-XXXX)'
        }
        super().__init__(name, label, required, help_text, validation, placeholder="XXXXX")

class CurrencyField(NumberField):
    """Specialized field for currency amounts"""
    def __init__(self, name, label, required=False, help_text=None, min_value=None, max_value=None):
        super().__init__(
            name, label, required, help_text, 
            validation=None, default=None,
            min_value=min_value, max_value=max_value, 
            step="0.01", currency=True
        )

class PercentageField(NumberField):
    """Specialized field for percentage values"""
    def __init__(self, name, label, required=False, help_text=None, min_value=0, max_value=100):
        super().__init__(
            name, label, required, help_text, 
            validation=None, default=None,
            min_value=min_value, max_value=max_value, 
            step="0.01", percentage=True
        )

class TaxYearField(SelectField):
    """Specialized field for tax years"""
    def __init__(self, name="tax_year", label="Tax Year", required=True, current_year=None):
        from datetime import datetime
        
        current_year = current_year or datetime.now().year
        # Generate options for the last 3 years and current year
        years = list(range(current_year-3, current_year+1))
        options = [{'value': str(year), 'label': str(year)} for year in years]
        
        help_text = "Select the tax year you are filing for"
        super().__init__(name, label, options, required, help_text, default=str(current_year-1))

class StateField(SelectField):
    """Specialized field for US states"""
    def __init__(self, name, label="State", required=False, help_text="Select a state"):
        states = [
            {"value": "AL", "label": "Alabama"},
            {"value": "AK", "label": "Alaska"},
            {"value": "AZ", "label": "Arizona"},
            {"value": "AR", "label": "Arkansas"},
            {"value": "CA", "label": "California"},
            {"value": "CO", "label": "Colorado"},
            {"value": "CT", "label": "Connecticut"},
            {"value": "DE", "label": "Delaware"},
            {"value": "FL", "label": "Florida"},
            {"value": "GA", "label": "Georgia"},
            {"value": "HI", "label": "Hawaii"},
            {"value": "ID", "label": "Idaho"},
            {"value": "IL", "label": "Illinois"},
            {"value": "IN", "label": "Indiana"},
            {"value": "IA", "label": "Iowa"},
            {"value": "KS", "label": "Kansas"},
            {"value": "KY", "label": "Kentucky"},
            {"value": "LA", "label": "Louisiana"},
            {"value": "ME", "label": "Maine"},
            {"value": "MD", "label": "Maryland"},
            {"value": "MA", "label": "Massachusetts"},
            {"value": "MI", "label": "Michigan"},
            {"value": "MN", "label": "Minnesota"},
            {"value": "MS", "label": "Mississippi"},
            {"value": "MO", "label": "Missouri"},
            {"value": "MT", "label": "Montana"},
            {"value": "NE", "label": "Nebraska"},
            {"value": "NV", "label": "Nevada"},
            {"value": "NH", "label": "New Hampshire"},
            {"value": "NJ", "label": "New Jersey"},
            {"value": "NM", "label": "New Mexico"},
            {"value": "NY", "label": "New York"},
            {"value": "NC", "label": "North Carolina"},
            {"value": "ND", "label": "North Dakota"},
            {"value": "OH", "label": "Ohio"},
            {"value": "OK", "label": "Oklahoma"},
            {"value": "OR", "label": "Oregon"},
            {"value": "PA", "label": "Pennsylvania"},
            {"value": "RI", "label": "Rhode Island"},
            {"value": "SC", "label": "South Carolina"},
            {"value": "SD", "label": "South Dakota"},
            {"value": "TN", "label": "Tennessee"},
            {"value": "TX", "label": "Texas"},
            {"value": "UT", "label": "Utah"},
            {"value": "VT", "label": "Vermont"},
            {"value": "VA", "label": "Virginia"},
            {"value": "WA", "label": "Washington"},
            {"value": "WV", "label": "West Virginia"},
            {"value": "WI", "label": "Wisconsin"},
            {"value": "WY", "label": "Wyoming"},
            {"value": "DC", "label": "District of Columbia"},
            {"value": "PR", "label": "Puerto Rico"},
            {"value": "VI", "label": "Virgin Islands"},
            {"value": "GU", "label": "Guam"},
            {"value": "AS", "label": "American Samoa"},
            {"value": "MP", "label": "Northern Mariana Islands"}
        ]
        super().__init__(name, label, states, required, help_text)

class FormSection:
    """A section of a form containing multiple fields"""
    def __init__(self, title, description=None, fields=None, conditional=None):
        self.title = title
        self.description = description
        self.fields = fields or []
        self.conditional = conditional  # Dict with field and value that controls visibility
        
    def add_field(self, field):
        """Add a field to this section"""
        self.fields.append(field)
        
    def to_dict(self):
        """Convert section to dictionary representation"""
        return {
            'title': self.title,
            'description': self.description,
            'fields': [field.to_dict() for field in self.fields],
            'conditional': self.conditional
        }
        
    def validate(self, data):
        """Validate all fields in this section"""
        errors = {}
        
        for field in self.fields:
            field_name = field.name
            field_value = data.get(field_name)
            
            field_errors = field.validate(field_value)
            if field_errors:
                errors[field_name] = field_errors
                
        return errors

class FormTemplate:
    """A complete form template with multiple sections"""
    def __init__(self, form_id, title, description=None, sections=None, metadata=None):
        self.form_id = form_id
        self.title = title
        self.description = description
        self.sections = sections or []
        self.metadata = metadata or {}
        
    def add_section(self, section):
        """Add a section to this form"""
        self.sections.append(section)
        
    def to_dict(self):
        """Convert form template to dictionary representation"""
        return {
            'form_id': self.form_id,
            'title': self.title,
            'description': self.description,
            'sections': [section.to_dict() for section in self.sections],
            'metadata': self.metadata
        }
        
    def validate(self, data):
        """Validate all sections in this form"""
        errors = {}
        
        for section in self.sections:
            section_errors = section.validate(data)
            if section_errors:
                errors.update(section_errors)
                
        return errors
        
    @classmethod
    def from_json(cls, json_file):
        """Load form template from JSON file"""
        with open(json_file, 'r') as f:
            data = json.load(f)
            
        form = cls(
            form_id=data.get('form_id'),
            title=data.get('title'),
            description=data.get('description'),
            metadata=data.get('metadata', {})
        )
        
        # Create sections
        for section_data in data.get('sections', []):
            section = FormSection(
                title=section_data.get('title'),
                description=section_data.get('description'),
                conditional=section_data.get('conditional')
            )
            
            # Create fields for this section
            for field_data in section_data.get('fields', []):
                field_type = field_data.get('type', '').lower()
                field_class = None
                
                # Select the appropriate field class
                if field_type == 'text':
                    field_class = TextField
                elif field_type == 'number':
                    field_class = NumberField
                elif field_type == 'date':
                    field_class = DateField
                elif field_type == 'select':
                    field_class = SelectField
                elif field_type == 'checkbox':
                    field_class = CheckboxField
                elif field_type == 'radio':
                    field_class = RadioField
                elif field_type == 'textarea':
                    field_class = TextareaField
                elif field_type == 'ein':
                    field_class = EINField
                elif field_type == 'ssn':
                    field_class = SSNField
                elif field_type == 'phone':
                    field_class = PhoneField
                elif field_type == 'zipcode':
                    field_class = ZipCodeField
                elif field_type == 'currency':
                    field_class = CurrencyField
                elif field_type == 'percentage':
                    field_class = PercentageField
                elif field_type == 'taxyear':
                    field_class = TaxYearField
                elif field_type == 'state':
                    field_class = StateField
                
                if field_class:
                    # Create field instance with appropriate parameters
                    field = field_class(**field_data)
                    section.add_field(field)
            
            form.add_section(section)
        
        return form

# Form template registry
_form_templates = {}

def register_form_template(template):
    """Register a form template in the registry"""
    global _form_templates
    _form_templates[template.form_id] = template
    
def get_form_template(form_id):
    """Get a form template from the registry"""
    return _form_templates.get(form_id)

def load_form_templates(directory):
    """Load all form templates from a directory"""
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            try:
                template = FormTemplate.from_json(file_path)
                register_form_template(template)
                print(f"Loaded form template: {template.title}")
            except Exception as e:
                print(f"Error loading form template {filename}: {str(e)}")

# Create Form Blueprints
form_library_bp = Blueprint('form_library', __name__, url_prefix='/form-library')

@form_library_bp.route('/templates')
def list_templates():
    """List all available form templates"""
    templates = []
    for form_id, template in _form_templates.items():
        templates.append({
            'id': form_id,
            'title': template.title,
            'description': template.description
        })
    return jsonify(templates)

@form_library_bp.route('/templates/<form_id>')
def get_template(form_id):
    """Get a specific form template"""
    template = get_form_template(form_id)
    if not template:
        abort(404, description=f"Form template {form_id} not found")
    return jsonify(template.to_dict())

@form_library_bp.route('/validate', methods=['POST'])
def validate_form():
    """Validate form data against a template"""
    data = request.json
    form_id = data.get('form_id')
    form_data = data.get('data', {})
    
    template = get_form_template(form_id)
    if not template:
        abort(404, description=f"Form template {form_id} not found")
        
    errors = template.validate(form_data)
    
    return jsonify({
        'is_valid': len(errors) == 0,
        'errors': errors
    })

# Load default tax form templates
def init_app(app):
    """Initialize the form library with the Flask app"""
    templates_dir = os.path.join(app.root_path, 'form_templates')
    if os.path.exists(templates_dir):
        load_form_templates(templates_dir)
    app.register_blueprint(form_library_bp)