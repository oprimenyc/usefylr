from flask import session

class FormSession:
    """Manages multi-step form sessions"""
    
    @staticmethod
    def save_form_progress(form_type, form_data):
        """Save the current progress of a multi-step form to session"""
        if 'form_progress' not in session:
            session['form_progress'] = {}
        
        session['form_progress'][form_type] = form_data
        session.modified = True
    
    @staticmethod
    def get_form_progress(form_type=None):
        """Get the current progress of a form from session"""
        if 'form_progress' not in session:
            return {} if form_type is None else None
        
        if form_type is None:
            return session['form_progress']
        else:
            return session['form_progress'].get(form_type)
    
    @staticmethod
    def clear_form_progress():
        """Clear the form progress from session"""
        if 'form_progress' in session:
            del session['form_progress']
            session.modified = True
    
    @staticmethod
    def save_tax_context(context_data):
        """Save tax filing context (year, entity type, etc.)"""
        session['tax_context'] = context_data
        session.modified = True
    
    @staticmethod
    def get_tax_context():
        """Get the current tax filing context"""
        return session.get('tax_context', {})
    
    @staticmethod
    def save_strategy_answers(answers):
        """Save strategy questionnaire answers"""
        session['strategy_answers'] = answers
        session.modified = True
    
    @staticmethod
    def get_strategy_answers():
        """Get saved strategy questionnaire answers"""
        return session.get('strategy_answers', {})