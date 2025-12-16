from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Organisation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    inn = db.Column(db.String(20), unique=True, nullable=True)
    ogrn = db.Column(db.String(20), unique=True, nullable=True)
    address = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    arv_member = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Organisation {self.name}>'


class Smi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    rating = db.Column(db.Integer)
    male = db.Column(db.Float)
    def __repr__(self):
        return f'<Smi {self.name}>'


class Region(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Float)
    
    # Relationship with districts
    districts = db.relationship('District', backref='region', lazy=True)
    
    def __repr__(self):
        return f'<Region {self.name}>'


class District(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    population = db.Column(db.Integer, nullable=True)
    region_id = db.Column(db.Integer, db.ForeignKey('region.id'), nullable=False)
    
    def __repr__(self):
        return f'<District {self.name}>'

class Broadcast(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey('organisation.id'), nullable=False)
    smi_id = db.Column(db.Integer, db.ForeignKey('smi.id'))
    district_id = db.Column(db.Integer, db.ForeignKey('district.id'), nullable=False)
    frequency = db.Column(db.String(50), nullable=True)
    power = db.Column(db.Float, nullable=True)
    
    # Relationships
    org = db.relationship('Organisation', backref='broadcasts')
    smi = db.relationship('Smi', backref='broadcasts')
    district = db.relationship('District', backref='broadcasts')
    
    def __repr__(self):
        return f'<Broadcast {self.id}>'