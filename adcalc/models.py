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
