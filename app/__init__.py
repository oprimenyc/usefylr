"""
Flask application initialization
"""

import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from flask_migrate import Migrate

# Load environment variables from .env file
load_dotenv()

# Create SQLAlchemy base class
class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    """Create and configure the Flask application"""
    # Create the app
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    
    # Configure the app
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "development_key")
    app.config["DEBUG"] = os.environ.get("FLASK_ENV") == "development"
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # Initialize extensions with the app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    from app.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    # Register authentication blueprint
    from app.auth import auth_bp
    app.register_blueprint(auth_bp)

    # Register features blueprint (AI Chat, Smart Ledger, Forms)
    from app.features import features_bp
    app.register_blueprint(features_bp)

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

    try:
        from modules.contractor_routes import contractor_bp
        app.register_blueprint(contractor_bp)
    except ImportError:
        pass

    # Database tables are managed by Flask-Migrate
    # Use 'flask db upgrade' to create/update tables

    return app