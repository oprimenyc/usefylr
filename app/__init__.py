"""
Flask application initialization
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager

# Create SQLAlchemy base class
class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

def create_app():
    """Create and configure the Flask application"""
    # Create the app
    app = Flask(__name__, template_folder="../templates")
    
    # Configure the app
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "development_key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # Initialize extensions with the app
    db.init_app(app)
    login_manager.init_app(app)
    
    from app.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    # Try to register optional blueprints if they exist
    try:
        from modules.tax_strategy_routes import tax_strategy_bp
        app.register_blueprint(tax_strategy_bp)
    except ImportError:
        pass
    
    try:
        from modules.accounting_integrations import accounting_bp
        app.register_blueprint(accounting_bp)
    except ImportError:
        pass
    
    try:
        from modules.form_builder import form_builder_bp
        app.register_blueprint(form_builder_bp)
    except ImportError:
        pass
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app