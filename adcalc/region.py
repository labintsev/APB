from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from .models import db, Organisation, Smi, Region, District, Broadcast

region_bp = Blueprint('region', __name__, url_prefix='/region')


@region_bp.route('/list')
def region_list():
    """Список регионов с редакцией коэфициентов"""
    regions = Region.query.all()
    return render_template('region/region-list.html', regions=regions)


@region_bp.route('/coverage')
def region_coverage():
    """Отображает список регионов с возможностью раскрытия деталей по вещанию СМИ"""
    regions = Region.query.all()
    return render_template('region/region-coverage.html', regions=regions)


@region_bp.route('/<int:region_id>/update', methods=['POST'])
def region_update(region_id):
    """Обновление коэффициентов для региона"""
    region = Region.query.get_or_404(region_id)
    rating = request.form['rating']
    try:
        rating = float(rating)
    except ValueError:
        return jsonify({'error': 'Invalid rating value'}), 500
    # Обновляем коэффициенты и сохраняем изменения в базе данных
    region.rating = rating
    db.session.commit()
    return redirect(url_for('region.region_list'))
