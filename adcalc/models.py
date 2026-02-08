from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches the hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"<User {self.username}>"


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
        return str(self.name)


class Region(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Float)

    broadcasts = db.relationship("Broadcast", backref="region", lazy=True)

    def __repr__(self):
        return str(self.name)


class Broadcast(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    org_id = db.Column(
        db.Integer,
        db.ForeignKey("organisation.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Embedded SMI fields (smi table removed)
    smi_name = db.Column(db.String(200), nullable=True)
    smi_rating = db.Column(db.Float, nullable=True)
    smi_male_proportion = db.Column(db.Float, nullable=True)

    # Embedded District fields (district table removed)
    district_name = db.Column(db.String(200), nullable=True)
    district_population = db.Column(db.Integer, nullable=True)

    # Region relationship remains
    region_id = db.Column(db.Integer, db.ForeignKey("region.id"), nullable=False)

    frequency = db.Column(db.String(50), nullable=True)
    power = db.Column(db.Float, nullable=True)

    org = db.relationship(
        "Organisation",
        backref=db.backref("broadcasts", passive_deletes=True),
    )

    def __repr__(self):
        smi = self.smi_name or "<none>"
        district = self.district_name or "<none>"
        return f"{self.org.name}, {district}, {smi}"
