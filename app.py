from flask import Flask, redirect, render_template, jsonify, request, url_for
from models import db, Organisation, Smi, Region, District, Broadcast

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///broadcasts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db.init_app(app)

# Базовый коэфициент для расчета 5 копеек per person
cost_per_person = 0.005  


@app.route('/')
def index():
    """Главная страница: отображает список регионов с возможностью раскрытия СМИ"""
    regions = Region.query.all()
    return render_template('index.html', regions=regions)

@app.route('/org_list')
def org_list():
    # Fetch all organizations from the database
    organizations = Organisation.query.all()
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
    return render_template('districts.html', districts=districts)


@app.route('/district/<int:id>')
def district_detail(id):
    # Show details for a specific district
    district = District.query.get_or_404(id)
    return render_template('district.html', district=district)


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


@app.route('/api/region/<int:id>/smi')
def api_region_smi(id):
    """API для получения JSON СМИ для конкретного региона"""
    region = Region.query.get_or_404(id)
    smi_list = []
    
    # Get all broadcasts for this region
    broadcasts = Broadcast.query.filter_by(district_id=id).all()
    
    # Get unique SMIs from these broadcasts
    smi_ids = set(broadcast.smi_id for broadcast in broadcasts if broadcast.smi_id)
    
    for smi_id in smi_ids:
        smi = Smi.query.get(smi_id)
        if smi:
            smi_list.append({
                'id': smi.id,
                'name': smi.name,
                'rating': smi.rating
            })
    
    return jsonify(smi_list)


@app.route('/api/organisations')
def api_organisations():
    """API для получения JSON всех организаций"""
    organisations = Organisation.query.all()
    orgs_data = []
    
    for org in organisations:
        orgs_data.append({
            'id': org.id,
            'name': org.name,
            'name_short': org.name_short,
            'inn': org.inn,
            'ogrn': org.ogrn,
            'address': org.address,
            'phone': org.phone,
            'email': org.email,
            'arv_member': org.arv_member,
            'population_sum': org.population_sum
        })
    
    return jsonify(orgs_data)


@app.route('/api/calculation/<int:org_id>')
def api_calculation(org_id):
    """API для получения JSON расчета стоимости для организации"""
    org = Organisation.query.get_or_404(org_id)
    
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
    
    # Calculate cost - simplified calculation

    total_cost = total_population * cost_per_person
    
    return jsonify({
        'org_id': org.id,
        'org_name': org.name,
        'total_population': total_population,
        'total_cost': total_cost
    })




if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)