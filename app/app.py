import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create database base class
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Initialize Flask app
app = Flask(__name__, 
            template_folder="../templates", 
            static_folder="../static")

# Set up configuration
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Import routes
with app.app_context():
    # Import models
    from app.models import User
    
    # Setup user loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Create tables
    # db.create_all()  # DISABLED - Using Flask-Migrate instead
    
    # Import and register blueprints
    from app.routes import main_bp
    from app.auth import auth_bp
    from app.billing import billing_bp
    
    # Import module blueprints
    from modules.form_routes import form_bp
    from modules.strategy_routes import strategy_bp
    from modules.letter_routes import letter_bp
    from modules.tax_questionnaire import questionnaire_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(form_bp)
    app.register_blueprint(strategy_bp)
    app.register_blueprint(letter_bp)
    app.register_blueprint(questionnaire_bp)
    
    # Error handlers
    from app.routes import page_not_found, server_error
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(500, server_error)