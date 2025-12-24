# adcalc/models.py
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
        return str(self.name)


class Smi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    rating = db.Column(db.Integer)
    male = db.Column(db.Float)

    def __repr__(self):
        return str(self.name)


class Region(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Float)

    # Relationship with districts
    districts = db.relationship("District", backref="region", lazy=True)

    def __repr__(self):
        return str(self.name)


class District(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    population = db.Column(db.Integer, nullable=True)
    region_id = db.Column(db.Integer, db.ForeignKey("region.id"), nullable=False)

    def __repr__(self):
        return str(self.name)


class Broadcast(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    org_id = db.Column(
        db.Integer,
        db.ForeignKey("organisation.id", ondelete="RESTRICT"),
        nullable=False,
    )
    smi_id = db.Column(db.Integer, db.ForeignKey("smi.id"))
    district_id = db.Column(
        db.Integer,
        db.ForeignKey("district.id"),
        nullable=False,
    )
    region_id = db.Column(
        db.Integer,
        db.ForeignKey("region.id"),
        nullable=False,
    )
    frequency = db.Column(db.String(50), nullable=True)
    power = db.Column(db.Float, nullable=True)

    # Relationships – keep passive_deletes so that no SQLAlchemy‑level cascade happens.
    org = db.relationship(
        "Organisation",
        backref=db.backref("broadcasts", passive_deletes=True),
    )
    smi = db.relationship("Smi", backref="broadcasts")
    district = db.relationship("District", backref="broadcasts")
    region = db.relationship("Region", backref="broadcasts")

    def __repr__(self):
        # Safeguard against `smi` being None: fall back to “<unknown>”.
        smi_name = self.smi.name if self.smi else "<none>"
        return f"{self.org.name}, {self.district.name}, {smi_name}"
    