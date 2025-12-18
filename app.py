from flask import Flask, redirect, render_template, jsonify, request, url_for
from models import db, Organisation, Smi, Region, District, Broadcast

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///broadcasts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db.init_app(app)

# Базовый коэфициент для расчета 5 копеек per person
cost_per_person = 5  


def calculate_cost(broadcast):
    try:
        # Get the broadcast details
        smi = Smi.query.get(broadcast.smi_id)
        district = District.query.get(broadcast.district_id)
        
        if not smi or not district or not district.population:
            return 0
            
        region = Region.query.get(district.region_id)
        if not region:
            return 0
            
        cost = cost_per_person * smi.rating * district.population * region.rating
        return cost
    except Exception as e:
        print(f"Error calculating cost: {e}")
        return 0  # Return 0 if calculation fails
    

@app.context_processor
def inject_functions():
    return dict(calculate_cost=calculate_cost) 


@app.route('/')
def index():
    """Главная страница: отображает список регионов с возможностью раскрытия СМИ"""
    regions = Region.query.all()
    return render_template('index.html', regions=regions)


@app.route('/org_list')
def org_list():
    # Fetch all organizations from the database
    organizations = Organisation.query.all()
    
    # For every organisation read total smi, total districts, total population and total cost
    for org in organizations:
        # Calculate total SMI for this organization
        org.total_smi = Smi.query.join(Broadcast).filter(Broadcast.org_id == org.id).distinct().count()
        
        # Calculate total districts for this organization
        org.total_districts = District.query.join(Broadcast).filter(Broadcast.org_id == org.id).distinct().count()
        
        # Calculate total population covered by this organization
        total_population = 0
        districts_covered = set()
        
        # Get all broadcasts for this organization
        broadcasts = Broadcast.query.filter_by(org_id=org.id).all()
        
        # Calculate total population for districts in these broadcasts
        for broadcast in broadcasts:
            if broadcast.district_id not in districts_covered:
                district = District.query.get(broadcast.district_id)
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
        
    return render_template('org-list.html', organisations=organizations)


@app.route('/organisation/<int:id>')
def org_detail(id):
    # Show details for a specific organization
    org = Organisation.query.get_or_404(id)
    return render_template('org-read.html', organisation=org)


@app.route('/organisation/create', methods=['GET', 'POST'])
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
        return redirect(url_for('org_list'))
    else:
        # Show the form for creating a new organization
        regions = Region.query.all()
        return render_template('org-create.html', regions=regions)


@app.route('/organisation/<int:org_id>/update', methods=['GET', 'POST'])
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
        return redirect(url_for('org_list'))
    else:
        # Show the form for updating the organization
        return render_template('org-update.html', organisation=org)


# In app.py - Add the route to display broadcasts for an organization
@app.route('/organisation/<int:org_id>/broadcasts')
def org_broadcasts(org_id):
    org = Organisation.query.get_or_404(org_id)
    smis = Smi.query.all()
    districts = District.query.all()
    return render_template('org-broadcast.html', organisation=org, smis=smis, districts=districts)


@app.route('/organisation/<int:org_id>/broadcast_create', methods=['POST'])
def broadcast_create(org_id):
    # Get the organization
    org = Organisation.query.get_or_404(org_id)
    
    # Get form data
    smi_id = request.form['smi_id']
    district_id = request.form['district_id']
    frequency = request.form.get('frequency')
    power = request.form.get('power')
    
    # Create new broadcast
    new_broadcast = Broadcast(
        org_id=org.id,
        smi_id=smi_id,
        district_id=district_id,
        frequency=frequency,
        power=power
    )
    
    # Add to database
    db.session.add(new_broadcast)
    db.session.commit()
    # Redirect back to organization broadcasts page
    return redirect(url_for('org_broadcasts', org_id=org.id))


@app.route('/broadcast/<int:bro_id>/update', methods=['POST', 'GET'])
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
        return redirect(url_for('org_broadcasts', org_id=broadcast.org_id))
    else:
        # Show the form for updating the broadcast
        org = Organisation.query.get_or_404(broadcast.org_id)
        smis = Smi.query.all()
        districts = District.query.all()
        return render_template('broadcast-update.html', 
                             broadcast=broadcast, 
                             organisation=org, 
                             smis=smis, 
                             districts=districts)


@app.route('/broadcast/<int:bro_id>/delete')
def broadcast_delete(bro_id):
    # Delete a broadcast by ID
    bro = Broadcast.query.get_or_404(bro_id)
    db.session.delete(bro)
    db.session.commit()
    return redirect(url_for('org_broadcasts', org_id=bro.org_id))


@app.route('/organisation/<int:org_id>/delete', methods=['POST'])
def org_delete(org_id):
    # Delete an organization by ID
    org = Organisation.query.get_or_404(org_id)
    db.session.delete(org)
    db.session.commit()
    return redirect(url_for('org_list'))


@app.route('/smi_list')
def smi_list():
    # Fetch all SMI from the database
    smis = Smi.query.all()
    return render_template('smi-list.html', smis=smis)


@app.route('/smi/<int:smi_id>')
def smi_detail(smi_id):
    # Show details for a specific SMIs
    smi = Smi.query.get_or_404(smi_id)
    return render_template('smi-read.html', smi=smi)


@app.route('/smi/create', methods=['GET', 'POST'])
def smi_create():
    # Handle both GET (show form) and POST (submit form) requests
    if request.method == 'POST':
        # Create a new SMIs instance and add it to the database
        new_smi = Smi(
            name=request.form['name'], 
            rating=request.form['rating'],
            male=request.form['male']
        )
        db.session.add(new_smi)
        db.session.commit()
        return redirect(url_for('smi_list'))
    else:
        # Show the form for creating a new SMIs
        return render_template('smi-create.html')


@app.route('/smi/<int:smi_id>/update', methods=['GET', 'POST'])
def smi_update(smi_id):
    # Handle both GET (show form) and POST (submit form) requests
    smis = Smi.query.get_or_404(smi_id)
    
    if request.method == 'POST':
        # Update the SMIs
        smis.name = request.form['name']
        smis.rating = request.form['rating']
        smis.male = request.form['male']
        db.session.commit()
        return redirect(url_for('smi_list'))
    else:
        # Show the form for updating the SMIs
        return render_template('smi-update.html', smi=smis)


@app.route('/smi/<int:smi_id>/delete', methods=['POST'])
def smi_delete(smi_id):
    # Delete an SMIs by ID
    smi = Smi.query.get_or_404(smi_id)
    db.session.delete(smi)
    db.session.commit()
    return redirect(url_for('smi_list'))


@app.route('/region_list')
def region_list():
    # Fetch all regions from the database
    regions = Region.query.all()
    return render_template('region.html', regions=regions)


@app.route('/district_list')
def district_list():
    # Fetch all districts from the database
    districts = District.query.all()
    return render_template('district-list.html', districts=districts)


@app.route('/district/<int:dis_id>')
def district_detail(dis_id):
    # Show details for a specific district
    district = District.query.get_or_404(dis_id)
    return render_template('district-read.html', district=district)


@app.route('/district/create', methods=['GET', 'POST'])
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
        return render_template('district-create.html', regions=regions)


@app.route('/district/<int:dis_id>/update', methods=['GET', 'POST'])
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


@app.route('/district/<int:dis_id>/delete', methods=['POST'])
def district_delete(dis_id):
    # Delete a district by ID
    district = District.query.get_or_404(dis_id)
    db.session.delete(district)
    db.session.commit()
    return redirect(url_for('district_list'))


@app.route('/api/regions')
def api_regions():
    """API для получения JSON всех регионов с суммарным населением"""
    regions = Region.query.all()
    regions_data = []
    
    for region in regions:
        # Calculate total population for the region
        total_population = 0
        for district in region.districts:
            total_population += district.population if district.population else 0
        
        regions_data.append({
            'id': region.id,
            'name': region.name,
            'population_sum': total_population,
            'rating': region.rating
        })
    
    return jsonify(regions_data)


@app.route('/api/region/<int:reg_id>/broadcasts')
def api_region_smi(reg_id):
    """API для получения JSON вещаний для конкретного региона"""
    output = {}
    region_broadcasts = []
    # Get all broadcasts for this region Todo optimize query
    districts = District.query.filter_by(region_id=reg_id).all()
    for district in districts:
        broadcasts = Broadcast.query.filter_by(district_id=district.id).all()
        region_broadcasts.extend(broadcasts)

    # Calculate total cost of broadcasts
    region_cost = sum([calculate_cost(broadcast) for broadcast in region_broadcasts])
    output['region_cost'] = region_cost  

    return jsonify(output)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
