from flask import Flask, render_template, jsonify
from .models import db, Organisation, Region, Broadcast
from .region import region_bp
from .org import org_bp
from .broadcast import broadcast_bp
from .api import api_bp
from .auth import auth_bp
from .utils import calculate_cost
import logging
from logging.handlers import RotatingFileHandler
import os
from functools import wraps
from flask import session, redirect, url_for
import dotenv

dotenv.load_dotenv()  # Load environment variables from .env file if it exists


def login_required(f):
    """Decorator to require login for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///broadcasts.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        # Базовый коэфициент для расчета - 1 копейка за человека
        app.config['COST_PER_PERSON'] = 1
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
        # Optional email whitelist: comma-separated values in environment or .env file
        # Examples: 'alice@example.com,bob@example.com,@example.org'
        app.config['EMAIL_WHITELIST'] = os.environ.get('EMAIL_WHITELIST')
    else:
        app.config.from_mapping(test_config)

    # Initialize the database
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # Setup logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/adcalc.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('AdCalc application startup')

    @app.route('/')
    def index():
        """Главная страница: отображает калькулятор рекламного бюджета"""
        if not session.get('user_id'):
            return redirect(url_for('auth.login'))
        return render_template('index.html')

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(region_bp)
    app.register_blueprint(org_bp)
    app.register_blueprint(broadcast_bp)

    return app
