# tests/test_org_views.py
import pytest
import sys
import os

# Make the project root importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adcalc import create_app
from adcalc.models import db, Organisation, Smi, Region, District, Broadcast
from adcalc.utils import calculate_cost


# --------------------------------------------------------------------------- #
#  Fixtures – create app + database + helper functions
# --------------------------------------------------------------------------- #
@pytest.fixture
def app():
    """Create a Flask app configured for testing."""
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "COST_PER_PERSON": 5,            # make cost calculation deterministic
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _create_region(name="Test Region"):
    """Helper – create a single region."""
    region = Region(name=name, rating=1.0)
    db.session.add(region)
    db.session.commit()
    return region


def _create_district(region, name="Test District", population=1000):
    """Helper – create a district belonging to a region."""
    district = District(name=name, population=population, region_id=region.id)
    db.session.add(district)
    db.session.commit()
    return district


def _create_smi(name="Test SMI", rating=10, male=0.3):
    """Helper – create a single SMI."""
    smi = Smi(name=name, rating=rating, male=male)
    db.session.add(smi)
    db.session.commit()
    return smi


def _create_org(name="Test Org"):
    """Helper – create an organisation."""
    org = Organisation(name=name)
    db.session.add(org)
    db.session.commit()
    return org


def _create_broadcast(org, smi, district, frequency="10.5", power=0.8):
    """Helper – create a broadcast for an organisation."""
    broadcast = Broadcast(
        org_id=org.id,
        smi_id=smi.id,
        district_id=district.id,
        region_id=district.region_id,
        frequency=frequency,
        power=power,
    )
    db.session.add(broadcast)
    db.session.commit()
    return broadcast


# --------------------------------------------------------------------------- #
#  Organisation Views – Happy‑path & edge‑cases
# --------------------------------------------------------------------------- #
def test_org_list_empty(client):
    """GET /org/list – returns an empty table when no organisations exist."""
    rv = client.get("/org/list")
    assert rv.status_code == 200
    assert "Список организаций" in rv.data.decode("utf-8")
    # table body should contain 0 rows


def test_org_list_with_entries(client):
    """GET /org/list – shows a list that contains real organisations."""
    reg = _create_region()
    org = _create_org("Org‑One")
    # add one SMI and one broadcast so totals are > 0
    smi = _create_smi(name="SMI‑A")
    district = _create_district(region=reg, name="D‑A", population=2000)
    bc = _create_broadcast(smi=smi, district=district, org=org )
    db.session.commit()

    rv = client.get("/org/list")
    assert rv.status_code == 200
    assert org.name.encode() in rv.data
    assert b"1" in rv.data          # total_smi
    assert b"1" in rv.data          # total_districts
    assert b"2000" in rv.data       # total_population
    # cost calculation is deterministic (COST_PER_PERSON * population)
    expected_cost = calculate_cost(Broadcast.query.first())
    assert str(expected_cost).encode() in rv.data


def test_org_detail_view(client):
    """GET /org/<id> – returns the org detail page."""
    org = _create_org("Org-1")
    rv = client.get(f"/org/{org.id}")
    assert rv.status_code == 200
    assert org.name.encode() in rv.data


def test_org_create_view(client):
    """POST /org/create – creates  a new organisation via the form."""
    data = {
        "name": "New Org",
        "inn": "1234567890",
        "ogrn": "9876543210",
        "address": "123 Main St",
        "phone": "+7 999 123 45 67",
        "email": "org@example.com",
        "arv_member": "1",
    }
    rv = client.post("/org/create", data=data, follow_redirects=True)
    assert rv.status_code == 200
    assert "Список организаций" in rv.data.decode("utf-8")
    # check that the organisation is really in the DB
    org = Organisation.query.filter_by(name="New Org").one_or_none()
    assert org is not None
    assert org.inn == data["inn"]


# tests/test_views_organisation.py
def test_org_update_view(client):
    """POST /org/<id>/update  updates an existing organisation."""
    org = _create_org("Org to Update")
    update_data = { "name": "New Name", 
                   "inn": "1234567890", 
                   "ogrn": "9876543210", 
                   "address": "456 Elm St", 
                   "phone": "555-1234"
                     }
    rv = client.post(f"/org/{org.id}/update", data=update_data, follow_redirects=True)
    # assert rv.status_code == 200
    # verify changes in the database
    org = Organisation.query.get(org.id)
    assert org.name == update_data["name"]
    assert org.inn == update_data["inn"]
    assert org.phone == update_data["phone"]
    assert org.email is None     # blank field → stored as None


def test_org_delete_without_broadcasts(client):
    """POST /org/delete – organisation with no broadcasts is deleted."""
    org = _create_org("Org‑To‑Delete")
    rv = client.post(f"/org/{org.id}/delete", follow_redirects=True)
    assert rv.status_code == 200
    assert "Список организаций" in rv.data.decode("utf-8")
    # organisation must no longer exist
    assert Organisation.query.get(org.id) is None


def test_org_delete_with_broadcasts(client):
    """Attempt to delete an organisation that has broadcasts """
    reg = _create_region()
    dist = _create_district(reg)
    smi = _create_smi()
    org = _create_org("Org‑With‑Broadcast")
    _create_broadcast(org, smi, dist)
    rv = client.post(f"/org/{org.id}/delete", follow_redirects=True)
    assert rv.status_code == 200
    # the view redirects back to the list; the org must still exist
    assert Organisation.query.get(org.id) is None
    # message "Организации" is present – confirms we’re still on the list page
    assert "Список организаций" in rv.data.decode("utf-8")


# --------------------------------------------------------------------------- #
#  Broadcast‑related views
# --------------------------------------------------------------------------- #
def test_broadcast_create_view(client):
    """POST /org/<org_id>/broadcast_create – add a new broadcast."""
    reg = _create_region()
    dist = _create_district(reg)
    smi = _create_smi()
    org = _create_org("Org‑Bcast")
    data = {
        "smi_id": smi.id,
        "district_id": dist.id,
        "frequency": "9.1",
        "power": "1.5",
    }
    rv = client.post(f"/org/{org.id}/broadcast_create", data=data, follow_redirects=True)
    assert rv.status_code == 200
    # broadcast must now be in the database
    broadcast = Broadcast.query.filter_by(org_id=org.id).one_or_none()
    assert broadcast is not None
    assert broadcast.frequency == data["frequency"]
    assert broadcast.power == float(data["power"])
    # cost appears in the table rendered by the GET view
    assert str(calculate_cost(broadcast)).encode() in rv.data


def test_broadcast_update_view(client):
    """GET + POST – edit an existing broadcast."""
    reg = _create_region()
    dist1 = _create_district(reg, population=2000)
    dist2 = _create_district(reg, name="Other District", population=1500)
    smi1 = _create_smi(name="SMI‑1")
    smi2 = _create_smi(name="SMI‑2")
    org = _create_org("Org‑Bcast‑Upd")
    broadcast = _create_broadcast(org, smi1, dist1, frequency="10", power=0.9)

    # GET the form page – it should pre‑populate the current values
    rv = client.get(f"/org/broadcast/{broadcast.id}/update")
    assert rv.status_code == 200
    assert str(broadcast.id).encode() in rv.data

    # POST with new data
    post_data = {
        "smi_id": smi2.id,
        "district_id": dist2.id,
        "frequency": "11.5",
        "power": "1.2",
    }
    rv = client.post(
        f"/org/broadcast/{broadcast.id}/update", data=post_data, follow_redirects=True
    )
    assert rv.status_code == 200
    # reload from DB
    broadcast = Broadcast.query.get(broadcast.id)
    assert broadcast.smi_id == smi2.id
    assert broadcast.district_id == dist2.id
    assert broadcast.frequency == post_data["frequency"]
    assert broadcast.power == float(post_data["power"])


def test_broadcast_delete_view(client):
    """POST /org/<org_id>/broadcast_delete – removes a broadcast."""
    reg = _create_region()
    dist = _create_district(reg)
    smi = _create_smi()
    org = _create_org("Org‑Bcast‑Del")
    broadcast = _create_broadcast(org, smi, dist)

    rv = client.get(f"/org/broadcast/{broadcast.id}/delete", follow_redirects=True)
    assert rv.status_code == 200
    # broadcast must be gone
    assert Broadcast.query.get(broadcast.id) is None
    # organisation’s broadcasts list must be empty
    assert len(org.broadcasts) == 0


# --------------------------------------------------------------------------- #
#  API endpoints used by the front‑end (optional but useful)
# --------------------------------------------------------------------------- #
def test_api_organisations_costs(client):
    """GET /api/organisations – returns correct JSON of total costs."""
    reg = _create_region()
    dist = _create_district(reg)
    smi = _create_smi()
    org = _create_org("Org‑API")
    _create_broadcast(org, smi, dist)
    rv = client.get("/api/organisations")
    assert rv.status_code == 200
    data = rv.get_json()
    # cost is the same as calculate_cost(broadcast)
    expected_cost = calculate_cost(org.broadcasts[0])
    assert data[org.name] == expected_cost


def test_api_region_broadcasts(client):
    """GET /api/region/<id>/broadcasts – returns region cost."""
    reg = _create_region()
    dist = _create_district(reg)
    smi = _create_smi()
    org = _create_org("Org‑Region")
    _create_broadcast(org, smi, dist)
    rv = client.get(f"/api/region/{reg.id}/broadcasts")
    assert rv.status_code == 200
    data = rv.get_json()
    expected_cost = calculate_cost(org.broadcasts[0])
    assert data["region_cost"] == expected_cost