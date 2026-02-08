from sqlite3 import IntegrityError
from flask import Blueprint, logging, render_template, request, redirect, url_for
from .models import db, Organisation, Region, Broadcast
from .utils import calculate_cost

org_bp = Blueprint('org', __name__, url_prefix='/org')


@org_bp.context_processor
def inject_functions():
    return dict(calculate_cost=calculate_cost) 


@org_bp.route('/list')
def org_list():
    # Fetch all organizations from the database
    organizations = Organisation.query.all()
    
    # For every organisation read total smi, total districts, total population and total cost
    for org in organizations:
        # Get all broadcasts for this organization
        broadcasts = Broadcast.query.filter_by(org_id=org.id).all()

        # Calculate total unique SMI names
        org.total_smi = len({b.smi_name for b in broadcasts if b.smi_name})

        # Calculate total unique districts
        org.total_districts = len({b.district_name for b in broadcasts if b.district_name})

        # Calculate total population covered by this organization (distinct districts)
        districts_covered = set()
        total_population = 0
        for b in broadcasts:
            if b.district_name and b.district_name not in districts_covered:
                if b.district_population:
                    total_population += b.district_population
                districts_covered.add(b.district_name)
        org.total_population = total_population

        # Calculate total cost for this organization
        total_cost = sum(calculate_cost(b) for b in broadcasts)
        org.total_cost = total_cost
        
    return render_template('org/org-list.html', organisations=organizations)


@org_bp.route('/<int:id>')
def org_detail(id):
    # Show details for a specific organization
    org = Organisation.query.get_or_404(id)
    return render_template('org/org-read.html', organisation=org)


@org_bp.route('/create', methods=['GET', 'POST'])
def org_create():
    # Handle both GET (show form) and POST (submit form) requests
    if request.method == 'POST':
        # Create a new organization instance and add it to the database
        new_org = Organisation(
            name=request.form['name'], 
            inn=request.form['inn'],
            ogrn=request.form['ogrn'],
            address=request.form['address'],
            phone=request.form['phone'],
            email=request.form['email'],
            arv_member=request.form.get('arv_member') == 1
            )
        db.session.add(new_org)
        db.session.commit()
        return redirect(url_for('org.org_list'))
    else:
        # Show the form for creating a new organization
        regions = Region.query.all()
        return render_template('org/org-create.html', regions=regions)


@org_bp.route('/<int:org_id>/update', methods=['GET', 'POST'])
def org_update(org_id):
    # Handle both GET (show form) and POST (submit form) requests
    org = Organisation.query.get_or_404(org_id)
    
    if request.method == 'POST':
        # Update the organization
        org.name = request.form['name']
        org.inn = request.form['inn']
        org.ogrn = request.form['ogrn']
        org.address = request.form['address']
        org.phone = request.form['phone']
        org.email = request.form['email']
        org.arv_member = request.form.get('arv_member') == 1
        db.session.commit()
        return redirect(url_for('org.org_list'))
    else:
        # Show the form for updating the organization
        return render_template('org/org-update.html', organisation=org)


@org_bp.route('/<int:org_id>/delete', methods=['POST'])
def org_delete(org_id):
    try:
        org = Organisation.query.get_or_404(org_id)
        db.session.delete(org)
        db.session.commit()
    except IntegrityError as e:
        logging.error(e)

    return redirect(url_for('org.org_list'))


@org_bp.route('/<int:org_id>/broadcasts')
def org_broadcasts(org_id):
    org = Organisation.query.get_or_404(org_id)
    # Provide existing distinct names for convenience and region list
    smis = [s[0] for s in db.session.query(Broadcast.smi_name).distinct().all() if s[0]]
    districts = [d[0] for d in db.session.query(Broadcast.district_name).distinct().all() if d[0]]
    regions = Region.query.all()
    return render_template('org/org-broadcast.html', organisation=org, smis=smis, districts=districts, regions=regions)


@org_bp.route('/<int:org_id>/broadcast_create', methods=['POST'])
def broadcast_create(org_id):
    # Get the organization
    org = Organisation.query.get_or_404(org_id)
    
    # Get form data (smi and district are embedded now)
    smi_name = request.form.get('smi_name')
    smi_rating = request.form.get('smi_rating')
    smi_male = request.form.get('smi_male')
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
        smi_male_proportion = float(smi_male) if smi_male else None
    except ValueError:
        smi_male_proportion = None
    try:
        district_population = int(district_population) if district_population else None
    except ValueError:
        district_population = None

    new_broadcast = Broadcast(
        org_id=org.id,
        smi_name=smi_name,
        smi_rating=smi_rating,
        smi_male_proportion=smi_male_proportion,
        district_name=district_name,
        district_population=district_population,
        region_id=region_id,
        frequency=frequency,
        power=power,
    )
    
    # Add to database
    db.session.add(new_broadcast)
    db.session.commit()
    # Redirect back to organization broadcasts page
    return redirect(url_for('org.org_broadcasts', org_id=org.id))


@org_bp.route('/broadcast/<int:bro_id>/update', methods=['POST', 'GET'])
def broadcast_update(bro_id):
    # Update a broadcast by ID
    broadcast = Broadcast.query.get_or_404(bro_id)
    
    if request.method == 'POST':
        # Update the broadcast (embedded fields)
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
        broadcast.power = request.form.get('power')
        broadcast.region_id = request.form.get('region_id')
        db.session.commit()
        return redirect(url_for('org.org_broadcasts', org_id=broadcast.org_id))
    else:
        # Show the form for updating the broadcast
        org = Organisation.query.get_or_404(broadcast.org_id)
        smis = [s[0] for s in db.session.query(Broadcast.smi_name).distinct().all() if s[0]]
        districts = [d[0] for d in db.session.query(Broadcast.district_name).distinct().all() if d[0]]
        regions = Region.query.all()
        return render_template('org/broadcast-update.html', 
                             broadcast=broadcast, 
                             organisation=org, 
                             smis=smis, 
                             districts=districts,
                             regions=regions)


@org_bp.route('/broadcast/<int:bro_id>/delete')
def broadcast_delete(bro_id):
    if request.method == 'GET':
        # Delete a broadcast by ID with get method
        bro = Broadcast.query.get_or_404(bro_id)
        db.session.delete(bro)
        db.session.commit()
        return redirect(url_for('org.org_broadcasts', org_id=bro.org_id))
