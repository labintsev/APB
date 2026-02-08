from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from .models import db, Organisation, Region, Broadcast
from functools import wraps
from flask import session


def login_required(f):
    """Decorator to require login for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

region_bp = Blueprint('region', __name__, url_prefix='/region')


@region_bp.route('/list')
@login_required
def region_list():
    """Список регионов с редакцией коэфициентов"""
    regions = Region.query.all()
    return render_template('region/region-list.html', regions=regions)


@region_bp.route('/coverage')
@login_required
def region_coverage():
    """Отображает список регионов с возможностью раскрытия деталей по вещанию СМИ"""
    regions = Region.query.all()
    return render_template('region/region-coverage.html', regions=regions)


@region_bp.route('/<int:region_id>/update', methods=['POST'])
@login_required
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
