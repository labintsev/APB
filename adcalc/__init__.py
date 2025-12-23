from flask import Flask, render_template, jsonify
from .models import db, Organisation, Smi, Region, District, Broadcast
from .region import region_bp
from .org import org_bp
from .district import district_bp
from .smi import smi_bp
from .utils import calculate_cost


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


    @app.route('/')
    def index():
        """Главная страница: отображает калькулятор рекламного бюджета"""
        regions = Region.query.all()
        return render_template('index.html', regions=regions)

    @app.route('/api/organisations')
    def api_organisations():
        """API для получения JSON всех организаций со стоимостью вещаний
        Используется для калькулятора на главной странице"""
        organisations_data = {}
        organisations = Organisation.query.all()
        for organisation in organisations:
            organisations_data[organisation.name] = sum(
                [calculate_cost(broadcast) for broadcast in organisation.broadcasts])
        return jsonify(organisations_data)


    @app.route('/api/region/<int:reg_id>/broadcasts')
    def api_region_smi(reg_id):
        """API для получения JSON вещаний для конкретного региона
        Используется в списке регионов"""
        output = {}
        if reg_id == 0:
            region_broadcasts = Broadcast.query.all()
        else:
            region_broadcasts = Broadcast.query.filter_by(region_id=reg_id).all()

        # Calculate total cost of broadcasts
        region_cost = sum([calculate_cost(broadcast) for broadcast in region_broadcasts])
        output['region_cost'] = region_cost  

        return jsonify(output)

    app.register_blueprint(region_bp)
    app.register_blueprint(org_bp)
    app.register_blueprint(district_bp)
    app.register_blueprint(smi_bp)

    return app
