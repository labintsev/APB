from flask import Blueprint, render_template
from .models import db, Organisation, Smi, Region, District, Broadcast

region_bp = Blueprint('region', __name__, url_prefix='/region')


@region_bp.route('/list')
def region_list():
    """Главная страница: отображает список регионов с возможностью раскрытия СМИ"""
    regions = Region.query.all()
    return render_template('region/region-list.html', regions=regions)


