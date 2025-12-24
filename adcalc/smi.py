from flask import Blueprint, render_template, request, redirect, url_for
from .models import db, Organisation, Smi, Region, District, Broadcast


smi_bp = Blueprint('smi', __name__, url_prefix='/smi')


@smi_bp.route('/list')
def smi_list():
    # Fetch all SMI from the database
    smis = Smi.query.all()
    return render_template('smi/smi-list.html', smis=smis)


@smi_bp.route('/create', methods=['GET', 'POST'])
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
        return redirect(url_for('smi.smi_list'))
    else:
        # Show the form for creating a new SMIs
        return render_template('smi/smi-create.html')


@smi_bp.route('/<int:smi_id>/update', methods=['GET', 'POST'])
def smi_update(smi_id):
    # Handle both GET (show form) and POST (submit form) requests
    smis = Smi.query.get_or_404(smi_id)
    
    if request.method == 'POST':
        # Update the SMIs
        smis.name = request.form['name']
        smis.rating = request.form['rating']
        smis.male = request.form['male']
        db.session.commit()
        return redirect(url_for('smi.smi_list'))
    else:
        # Show the form for updating the SMIs
        return render_template('smi/smi-update.html', smi=smis)


@smi_bp.route('/<int:smi_id>/delete', methods=['POST'])
def smi_delete(smi_id):
    # Delete an SMIs by ID
    smi = Smi.query.get_or_404(smi_id)
    db.session.delete(smi)
    db.session.commit()
    return redirect(url_for('smi.smi_list'))
