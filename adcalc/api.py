from flask import Blueprint, jsonify, request
from .models import Organisation, Broadcast, db
from .utils import calculate_cost

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/organisations-detailed')
def api_organisations_detailed():
    """API для получения детальной информации об организациях и их broadcasts
    Используется в интерфейсе выбора организаций"""
    organisations_list = []
    organisations = Organisation.query.all()
    
    for organisation in organisations:
        org_data = {
            'id': organisation.id,
            'name': organisation.name,
            'cost': sum([calculate_cost(broadcast) for broadcast in organisation.broadcasts]),
            'broadcasts': []
        }
        
        for broadcast in organisation.broadcasts:
            broadcast_cost = calculate_cost(broadcast)
            smi_name = broadcast.smi_name or "<none>"
            district_name = broadcast.district_name or "<none>"

            broadcast_data = {
                'id': broadcast.id,
                'smi': smi_name,
                'district': district_name,
                'cost': broadcast_cost
            }
            org_data['broadcasts'].append(broadcast_data)
        
        organisations_list.append(org_data)
    
    return jsonify(organisations_list)


@api_bp.route('/region/<int:reg_id>/broadcasts')
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


@api_bp.route('/broadcasts/delete', methods=['POST'])
def api_broadcasts_delete():
    """API для удаления нескольких трансляций по их ID
    Ожидает JSON: {"ids": [1, 2, 3, ...]}"""
    data = request.get_json()
    if not data or 'ids' not in data:
        return jsonify({'error': 'Missing ids field'}), 400
    
    ids = data.get('ids', [])
    if not isinstance(ids, list) or not ids:
        return jsonify({'error': 'ids must be a non-empty list'}), 400
    
    deleted_count = 0
    try:
        for bid in ids:
            broadcast = Broadcast.query.get(int(bid))
            if broadcast:
                db.session.delete(broadcast)
                deleted_count += 1
        db.session.commit()
        return jsonify({'success': True, 'deleted': deleted_count}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
