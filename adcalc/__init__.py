from flask import Flask, render_template, jsonify
from .models import db, Organisation, Smi, Region, District, Broadcast
from .region import region_bp
from .org import org_bp
from .district import district_bp
from .smi import smi_bp
from .api import api_bp
from .utils import calculate_cost
import logging
from logging.handlers import RotatingFileHandler
import os


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///broadcasts.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        # Базовый коэфициент для расчета - 1 копейка за человека
        app.config['COST_PER_PERSON'] = 1
    else:
        app.config.from_mapping(test_config)

    # Initialize the database
    db.init_app(app)

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
        return render_template('index.html')

    app.register_blueprint(api_bp)
    app.register_blueprint(region_bp)
    app.register_blueprint(org_bp)
    app.register_blueprint(district_bp)
    app.register_blueprint(smi_bp)

    return app
