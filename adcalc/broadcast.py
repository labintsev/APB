from flask import Blueprint, render_template, request, redirect, url_for
from .models import db, Organisation, Region, Broadcast
from .utils import calculate_cost
from werkzeug.utils import secure_filename
import pandas as pd
import io

broadcast_bp = Blueprint('broadcast', __name__, url_prefix='/broadcast')


@broadcast_bp.context_processor
def inject_functions():
    return dict(calculate_cost=calculate_cost)


@broadcast_bp.route('/list')
def broadcast_list():
    """List all broadcasts with their details"""
    page = request.args.get('page', 1, type=int)
    pagination = Broadcast.query.paginate(page=page, per_page=50)
    broadcasts = pagination.items
    return render_template('broadcast/broadcast-list.html', broadcasts=broadcasts, pagination=pagination)


@broadcast_bp.route('/create', methods=['GET', 'POST'])
def broadcast_create():
    """Create a new broadcast"""
    if request.method == 'POST':
        # Get form data
        org_id = request.form.get('org_id')
        smi_name = request.form.get('smi_name')
        smi_rating = request.form.get('smi_rating')
        smi_male_proportion = request.form.get('smi_male_proportion')
        district_name = request.form.get('district_name')
        district_population = request.form.get('district_population')
        region_id = request.form.get('region_id')
        frequency = request.form.get('frequency')
        power = request.form.get('power')

        # Parse numeric fields
        try:
            smi_rating = float(smi_rating) if smi_rating else None
        except ValueError:
            smi_rating = None
        try:
            smi_male_proportion = float(smi_male_proportion) if smi_male_proportion else None
        except ValueError:
            smi_male_proportion = None
        try:
            district_population = int(district_population) if district_population else None
        except ValueError:
            district_population = None
        try:
            power = float(power) if power else None
        except ValueError:
            power = None

        new_broadcast = Broadcast(
            org_id=org_id,
            smi_name=smi_name,
            smi_rating=smi_rating,
            smi_male_proportion=smi_male_proportion,
            district_name=district_name,
            district_population=district_population,
            region_id=region_id,
            frequency=frequency,
            power=power,
        )

        db.session.add(new_broadcast)
        db.session.commit()
        return redirect(url_for('broadcast.broadcast_list'))
    else:
        # Show the form for creating a new broadcast
        organisations = Organisation.query.all()
        regions = Region.query.all()
        smis = [s[0] for s in db.session.query(Broadcast.smi_name).distinct().all() if s[0]]
        districts = [d[0] for d in db.session.query(Broadcast.district_name).distinct().all() if d[0]]
        return render_template('broadcast/broadcast-create.html',
                             organisations=organisations,
                             regions=regions,
                             smis=smis,
                             districts=districts)


@broadcast_bp.route('/<int:broadcast_id>/update', methods=['GET', 'POST'])
def broadcast_update(broadcast_id):
    """Update a broadcast by ID"""
    broadcast = Broadcast.query.get_or_404(broadcast_id)

    if request.method == 'POST':
        # Update the broadcast (embedded fields)
        broadcast.org_id = request.form.get('org_id')
        broadcast.smi_name = request.form.get('smi_name')
        try:
            broadcast.smi_rating = float(request.form.get('smi_rating')) if request.form.get('smi_rating') else None
        except ValueError:
            broadcast.smi_rating = None
        try:
            broadcast.smi_male_proportion = float(request.form.get('smi_male_proportion')) if request.form.get('smi_male_proportion') else None
        except ValueError:
            broadcast.smi_male_proportion = None
        broadcast.district_name = request.form.get('district_name')
        try:
            broadcast.district_population = int(request.form.get('district_population')) if request.form.get('district_population') else None
        except ValueError:
            broadcast.district_population = None
        broadcast.frequency = request.form.get('frequency')
        try:
            broadcast.power = float(request.form.get('power')) if request.form.get('power') else None
        except ValueError:
            broadcast.power = None
        broadcast.region_id = request.form.get('region_id')
        db.session.commit()
        return redirect(url_for('broadcast.broadcast_list'))
    else:
        # Show the form for updating the broadcast
        organisations = Organisation.query.all()
        regions = Region.query.all()
        smis = [s[0] for s in db.session.query(Broadcast.smi_name).distinct().all() if s[0]]
        districts = [d[0] for d in db.session.query(Broadcast.district_name).distinct().all() if d[0]]
        return render_template('broadcast/broadcast-update.html',
                             broadcast=broadcast,
                             organisations=organisations,
                             regions=regions,
                             smis=smis,
                             districts=districts)


@broadcast_bp.route('/<int:broadcast_id>/delete', methods=['POST'])
def broadcast_delete(broadcast_id):
    """Delete a broadcast by ID"""
    broadcast = Broadcast.query.get_or_404(broadcast_id)
    db.session.delete(broadcast)
    db.session.commit()
    return redirect(url_for('broadcast.broadcast_list'))


@broadcast_bp.route('/upload_excel', methods=['POST'])
def broadcast_upload_excel():
    """Upload broadcasts from an Excel file using pandas"""
    file = request.files.get('excel_file')
    if not file or file.filename == '':
        return redirect(url_for('broadcast.broadcast_list'))
    filename = secure_filename(file.filename)
    try:
        # Read Excel file into DataFrame
        df = pd.read_excel(file)
        # Expected columns: org_id, org_name, region_id, smi_name, smi_rating, smi_male_proportion, district_name, district_population, frequency, power
        for _, row in df.iterrows():
            print(f"Processing row: {row.to_dict()}")
            # Find Organisation
            org = Organisation.query.filter_by(id=row.get('org_id')).first()
            if not org:
                raise ValueError(f"Organisation with ID {row.get('org_id')} not found")
            # Find Region
            region = Region.query.filter_by(id=row.get('region_id')).first()
            print(f"Found org: {org}, region: {region}")
            if not region:
                raise ValueError(f"Region with ID {row.get('region_id')} not found")
            # Create Broadcast
            broadcast = Broadcast(
                org_id=org.id,
                smi_name=row.get('smi_name'),
                smi_rating=row.get('smi_rating'),
                smi_male_proportion=row.get('smi_male_proportion'),
                district_name=row.get('district_name'),
                district_population=row.get('district_population'),
                region_id=region.id,
                frequency=row.get('frequency'),
                power=row.get('power'),
            )
            db.session.add(broadcast)
        db.session.commit()
    except Exception as e:
        print(f"Excel upload error: {e}")
    return redirect(url_for('broadcast.broadcast_list'))
