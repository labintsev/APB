from sqlite3 import IntegrityError
from flask import Blueprint, logging, render_template, request, redirect, url_for
from .models import db, Organisation, Smi, Region, District, Broadcast
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
        # Calculate total SMI for this organization
        org.total_smi = Smi.query.join(Broadcast).filter(
            Broadcast.org_id == org.id).distinct().count()
        
        # Calculate total districts for this organization
        org.total_districts = District.query.join(Broadcast).filter(
            Broadcast.org_id == org.id).distinct().count()
        
        # Calculate total population covered by this organization
        total_population = 0
        districts_covered = set()
        
        # Get all broadcasts for this organization
        broadcasts = Broadcast.query.filter_by(org_id=org.id).all()
        
        # Calculate total population for districts in these broadcasts
        for broadcast in broadcasts:
            if broadcast.district_id not in districts_covered:
                district = District.query.get_or_404(broadcast.district_id)
                if district and district.population:
                    total_population += district.population
                    districts_covered.add(broadcast.district_id)
        
        org.total_population = total_population
        
        # Calculate total cost for this organization
        total_cost = 0
        for broadcast in broadcasts:
            cost = calculate_cost(broadcast)
            total_cost += cost
        
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
    smis = Smi.query.all()
    districts = District.query.all()
    return render_template('org/org-broadcast.html', organisation=org, smis=smis, districts=districts)


@org_bp.route('/<int:org_id>/broadcast_create', methods=['POST'])
def broadcast_create(org_id):
    # Get the organization
    org = Organisation.query.get_or_404(org_id)
    
    # Get form data
    smi_id = request.form['smi_id']
    district_id = request.form['district_id']
    frequency = request.form.get('frequency')
    power = request.form.get('power')
    region = District.query.get_or_404(district_id).region
    # Create new broadcast
    new_broadcast = Broadcast(
        org_id=org.id,
        smi_id=smi_id,
        district_id=district_id,
        region_id = region.id,
        frequency=frequency,
        power=power
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
        # Update the broadcast
        broadcast.smi_id = request.form['smi_id']
        broadcast.district_id = request.form['district_id']
        broadcast.frequency = request.form['frequency']
        broadcast.power = request.form['power']
        db.session.commit()
        return redirect(url_for('org.org_broadcasts', org_id=broadcast.org_id))
    else:
        # Show the form for updating the broadcast
        org = Organisation.query.get_or_404(broadcast.org_id)
        smis = Smi.query.all()
        districts = District.query.all()
        return render_template('org/broadcast-update.html', 
                             broadcast=broadcast, 
                             organisation=org, 
                             smis=smis, 
                             districts=districts)


@org_bp.route('/broadcast/<int:bro_id>/delete')
def broadcast_delete(bro_id):
    if request.method == 'GET':
        # Delete a broadcast by ID with get method
        bro = Broadcast.query.get_or_404(bro_id)
        db.session.delete(bro)
        db.session.commit()
        return redirect(url_for('org.org_broadcasts', org_id=bro.org_id))
