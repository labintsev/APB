from flask import Blueprint, render_template
from .models import db, Organisation, Smi, Region, District, Broadcast

district_bp = Blueprint('district', __name__, url_prefix='/district')


@district_bp.route('/list')
def district_list():
    # Fetch all districts from the database
    districts = District.query.all()
    return render_template('district/district-list.html', districts=districts)


@district_bp.route('/district/<int:dis_id>')
def district_detail(dis_id):
    # Show details for a specific district
    district = District.query.get_or_404(dis_id)
    return render_template('district/district-read.html', district=district)


@district_bp.route('/create', methods=['GET', 'POST'])
def district_create():
    # Handle both GET (show form) and POST (submit form) requests
    if request.method == 'POST':
        # Create a new district instance and add it to the database
        new_district = District(
            name=request.form['name'],
            population=request.form['population'],
            region_id=request.form['region_id'],
        )
        db.session.add(new_district)
        db.session.commit()
        return redirect(url_for('district_list'))
    else:
        # Show the form for creating a new district
        regions = Region.query.all()
        return render_template('district/district-create.html', regions=regions)


@district_bp.route('/<int:dis_id>/update', methods=['GET', 'POST'])
def district_update(dis_id):
    # Handle both GET (show form) and POST (submit form) requests
    district = District.query.get_or_404(dis_id)
    
    if request.method == 'POST':
        # Update the district
        district.name = request.form['name']
        district.population = request.form['population']
        district.region_id = request.form['region_id']
        db.session.commit()
        return redirect(url_for('district_list'))
    else:
        # Show the form for updating the district
        regions = Region.query.all()
        return render_template(
            'district-update.html', 
            district=district, 
            regions=regions)


@district_bp.route('/<int:dis_id>/delete', methods=['POST'])
def district_delete(dis_id):
    # Delete a district by ID
    district = District.query.get_or_404(dis_id)
    db.session.delete(district)
    db.session.commit()
    return redirect(url_for('district_list'))
