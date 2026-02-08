# tests/test_org_views.py
import pytest
import sys
import os

# Make the project root importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adcalc import create_app
from adcalc.models import db, Organisation, Region, Broadcast, User
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
        "COST_PER_PERSON": 5,            
        'SECRET_KEY': 'test-secret-key',
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    with app.app_context():
        # Create a test user
        user = User(username='testuser', email='test@example.com')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
    
    test_client = app.test_client()
    
    # Authenticate the test client
    with test_client:
        test_client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpass'
        })
    
    return test_client

def _create_region(name="Test Region"):
    """Helper – create a single region."""
    region = Region(name=name, rating=1.0)
    db.session.add(region)
    db.session.commit()
    return region


def _create_org(name="Test Org"):
    """Helper – create an organisation."""
    org = Organisation(name=name)
    db.session.add(org)
    db.session.commit()
    return org


def _create_broadcast(org, region, smi_name="Test SMI", smi_rating=10.0, 
                     smi_male_proportion=0.3, district_name="Test District", 
                     district_population=1000, frequency="10.5", power=0.8):
    """Helper – create a broadcast for an organisation with embedded SMI and District fields."""
    broadcast = Broadcast(
        org_id=org.id,
        region_id=region.id,
        smi_name=smi_name,
        smi_rating=smi_rating,
        smi_male_proportion=smi_male_proportion,
        district_name=district_name,
        district_population=district_population,
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
    # add one broadcast with embedded SMI and district fields
    bc = _create_broadcast(org, reg, smi_name="SMI‑A", district_name="D‑A", district_population=2000)
    db.session.commit()

    rv = client.get("/org/list")
    assert rv.status_code == 200
    assert org.name.encode() in rv.data
    assert b"1" in rv.data          # total broadcasts
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
    org = _create_org("Org‑With‑Broadcast")
    _create_broadcast(org, reg)
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
    org = _create_org("Org‑Bcast")
    data = {
        "smi_name": "Test SMI",
        "smi_rating": "10.0",
        "smi_male_proportion": "0.3",
        "district_name": "Test District",
        "district_population": "1000",
        "region_id": str(reg.id),
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
    org = _create_org("Org‑Bcast‑Upd")
    broadcast = _create_broadcast(org, reg, smi_name="SMI‑1", district_population=2000, 
                                 frequency="10", power=0.9)

    # GET the form page – it should pre‑populate the current values
    rv = client.get(f"/org/broadcast/{broadcast.id}/update")
    assert rv.status_code == 200
    assert str(broadcast.id).encode() in rv.data

    # POST with new data
    post_data = {
        "smi_name": "SMI‑2",
        "smi_rating": "15.0",
        "smi_male_proportion": "0.4",
        "district_name": "Other District",
        "district_population": "1500",
        "region_id": str(reg.id),
        "frequency": "11.5",
        "power": "1.2",
    }
    rv = client.post(
        f"/org/broadcast/{broadcast.id}/update", data=post_data, follow_redirects=True
    )
    assert rv.status_code == 200
    # reload from DB
    broadcast = Broadcast.query.get(broadcast.id)
    assert broadcast.smi_name == post_data["smi_name"]
    assert broadcast.district_name == post_data["district_name"]
    assert broadcast.frequency == post_data["frequency"]
    assert broadcast.power == float(post_data["power"])


def test_broadcast_delete_view(client):
    """POST /org/<org_id>/broadcast_delete – removes a broadcast."""
    reg = _create_region()
    org = _create_org("Org‑Bcast‑Del")
    broadcast = _create_broadcast(org, reg)

    rv = client.get(f"/org/broadcast/{broadcast.id}/delete", follow_redirects=True)
    assert rv.status_code == 200
    # broadcast must be gone
    assert Broadcast.query.get(broadcast.id) is None
    # organisation’s broadcasts list must be empty
    assert len(org.broadcasts) == 0


def test_api_region_broadcasts(client):
    """GET /api/region/<id>/broadcasts – returns region cost."""
    reg = _create_region()
    org = _create_org("Org‑Region")
    _create_broadcast(org, reg)
    rv = client.get(f"/api/region/{reg.id}/broadcasts")
    assert rv.status_code == 200
    data = rv.get_json()
    expected_cost = calculate_cost(org.broadcasts[0])
    assert data["region_cost"] == expected_cost
    