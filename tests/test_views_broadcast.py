# tests/test_views_broadcast.py
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adcalc import create_app
from adcalc.models import db, Organisation, Region, Broadcast, User
from adcalc.utils import calculate_cost


@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'COST_PER_PERSON': 5,
        'SECRET_KEY': 'test-secret-key'
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


# -------- Helper Functions -------- #
def _create_region(name="Test Region", rating=1.0):
    """Helper – create a region."""
    region = Region(name=name, rating=rating)
    db.session.add(region)
    db.session.commit()
    return region


def _create_organisation(name="Test Org"):
    """Helper – create an organisation."""
    org = Organisation(name=name)
    db.session.add(org)
    db.session.commit()
    return org


def _create_broadcast(
    org,
    region,
    smi_name="Test SMI",
    smi_rating=10.0,
    smi_male_proportion=0.3,
    district_name="Test District",
    district_population=5000,
    frequency="9.5",
    power=1.0,
):
    """Helper – create a broadcast."""
    broadcast = Broadcast(
        org_id=org.id,
        smi_name=smi_name,
        smi_rating=smi_rating,
        smi_male_proportion=smi_male_proportion,
        district_name=district_name,
        district_population=district_population,
        region_id=region.id,
        frequency=frequency,
        power=power,
    )
    db.session.add(broadcast)
    db.session.commit()
    return broadcast


# -------- Broadcast List Tests -------- #
def test_broadcast_list_empty(client):
    """GET /broadcast/list – returns empty list when no broadcasts exist."""
    rv = client.get("/broadcast/list")
    assert rv.status_code == 200
    assert "Все трансляции" in rv.data.decode("utf-8")


def test_broadcast_list_with_broadcasts(client):
    """GET /broadcast/list – shows all broadcasts with their details."""
    region = _create_region("Region 1")
    org = _create_organisation("Org 1")
    broadcast = _create_broadcast(
        org, region, smi_name="СМИ-1", district_name="Район-1", district_population=10000
    )

    rv = client.get("/broadcast/list")
    assert rv.status_code == 200
    assert "Все трансляции" in rv.data.decode("utf-8") 
    assert "СМИ-1" in rv.data.decode("utf-8")
    assert "1.0" in rv.data.decode("utf-8")  
    assert "Район-1" in rv.data.decode("utf-8")
    assert "10000" in rv.data.decode("utf-8")


def test_broadcast_list_shows_cost(client):
    """GET /broadcast/list – displays calculated cost for each broadcast."""
    region = _create_region("Region 1", rating=1.5)
    org = _create_organisation("Org 1")
    broadcast = _create_broadcast(
        org, region, smi_rating=5.0, district_population=20000
    )

    rv = client.get("/broadcast/list")
    assert rv.status_code == 200
    cost = calculate_cost(broadcast)
    assert str(cost).encode() in rv.data or f"{cost:.1f}".encode() in rv.data


def test_broadcast_list_multiple_broadcasts(client):
    """GET /broadcast/list – shows multiple broadcasts from different orgs/regions."""
    region1 = _create_region("Region 1")
    region2 = _create_region("Region 2")
    org1 = _create_organisation("Org 1")
    org2 = _create_organisation("Org 2")

    bc1 = _create_broadcast(org1, region1, smi_name="SMI-1", district_name="Dist-1")
    bc2 = _create_broadcast(org2, region2, smi_name="SMI-2", district_name="Dist-2")

    rv = client.get("/broadcast/list")
    assert rv.status_code == 200
    assert b"SMI-1" in rv.data
    assert b"SMI-2" in rv.data
    assert b"Dist-1" in rv.data
    assert b"Dist-2" in rv.data


# -------- Broadcast Create Tests -------- #
def test_broadcast_create_get_form(client):
    """GET /broadcast/create – shows the form to create a new broadcast."""
    region = _create_region()
    org = _create_organisation()

    rv = client.get("/broadcast/create")
    assert rv.status_code == 200
    assert "Создать трансляцию" in rv.data.decode("utf-8")


def test_broadcast_create_post_minimal(client):
    """POST /broadcast/create – creates a broadcast with minimal required fields."""
    region = _create_region("Тестовый регион")
    org = _create_organisation("Тестовая организация")

    data = {
        "org_id": org.id,
        "smi_name": "Новый СМИ",
        "smi_rating": "5.0",
        "district_name": "Новый район",
        "district_population": "8000",
        "region_id": region.id,
        "frequency": "",
        "power": "",
    }

    rv = client.post("/broadcast/create", data=data, follow_redirects=True)
    assert rv.status_code == 200
    assert "Все трансляции" in rv.data.decode("utf-8")

    # Verify broadcast is in database
    broadcast = Broadcast.query.filter_by(smi_name="Новый СМИ").first()
    assert broadcast is not None
    assert broadcast.smi_name == "Новый СМИ"
    assert broadcast.smi_rating == 5.0
    assert broadcast.district_name == "Новый район"
    assert broadcast.district_population == 8000
    assert broadcast.org_id == org.id
    assert broadcast.region_id == region.id


def test_broadcast_create_post_full(client):
    """POST /broadcast/create – creates a broadcast with all fields."""
    region = _create_region("Test Region")
    org = _create_organisation("Test Org")

    data = {
        "org_id": org.id,
        "smi_name": "Full SMI",
        "smi_rating": "7.5",
        "smi_male_proportion": "0.45",
        "district_name": "Full District",
        "district_population": "15000",
        "region_id": region.id,
        "frequency": "10.5",
        "power": "2.5",
    }

    rv = client.post("/broadcast/create", data=data, follow_redirects=True)
    assert rv.status_code == 200

    broadcast = Broadcast.query.filter_by(smi_name="Full SMI").first()
    assert broadcast is not None
    assert broadcast.smi_rating == 7.5
    assert broadcast.smi_male_proportion == 0.45
    assert broadcast.district_population == 15000
    assert broadcast.frequency == "10.5"
    assert broadcast.power == 2.5


def test_broadcast_create_invalid_numeric_rating(client):
    """POST /broadcast/create – handles invalid smi_rating gracefully."""
    region = _create_region()
    org = _create_organisation()

    data = {
        "org_id": org.id,
        "smi_name": "Test SMI",
        "smi_rating": "not_a_number",
        "district_name": "Test District",
        "district_population": "5000",
        "region_id": region.id,
    }

    rv = client.post("/broadcast/create", data=data, follow_redirects=True)
    assert rv.status_code == 200

    # Broadcast should still be created, but smi_rating should be None
    broadcast = Broadcast.query.filter_by(smi_name="Test SMI").first()
    assert broadcast is not None
    assert broadcast.smi_rating is None


def test_broadcast_create_invalid_population(client):
    """POST /broadcast/create – handles invalid district_population gracefully."""
    region = _create_region()
    org = _create_organisation()

    data = {
        "org_id": org.id,
        "smi_name": "Test SMI",
        "smi_rating": "5.0",
        "district_name": "Test District",
        "district_population": "invalid",
        "region_id": region.id,
    }

    rv = client.post("/broadcast/create", data=data, follow_redirects=True)
    assert rv.status_code == 200

    broadcast = Broadcast.query.filter_by(smi_name="Test SMI").first()
    assert broadcast is not None
    assert broadcast.district_population is None


# -------- Broadcast Update Tests -------- #
def test_broadcast_update_get_form(client):
    """GET /broadcast/<id>/update – shows the form to edit a broadcast."""
    region = _create_region()
    org = _create_organisation()
    broadcast = _create_broadcast(org, region)

    rv = client.get(f"/broadcast/{broadcast.id}/update")
    assert rv.status_code == 200
    assert "Редактировать трансляцию" in rv.data.decode("utf-8")
    # Form should contain current values
    assert broadcast.smi_name.encode() in rv.data
    assert broadcast.district_name.encode() in rv.data


def test_broadcast_update_post(client):
    """POST /broadcast/<id>/update – updates an existing broadcast."""
    region = _create_region("Region 1")
    org = _create_organisation("Org 1")
    broadcast = _create_broadcast(org, region, smi_name="Old SMI")

    data = {
        "org_id": org.id,
        "smi_name": "Updated SMI",
        "smi_rating": "8.0",
        "smi_male_proportion": "0.5",
        "district_name": "Updated District",
        "district_population": "12000",
        "region_id": region.id,
        "frequency": "11.0",
        "power": "3.0",
    }

    rv = client.post(f"/broadcast/{broadcast.id}/update", data=data, follow_redirects=True)
    assert rv.status_code == 200
    assert "Все трансляции" in rv.data.decode("utf-8")

    # Verify update in database
    updated = Broadcast.query.get(broadcast.id)
    assert updated.smi_name == "Updated SMI"
    assert updated.smi_rating == 8.0
    assert updated.smi_male_proportion == 0.5
    assert updated.district_name == "Updated District"
    assert updated.district_population == 12000
    assert updated.frequency == "11.0"
    assert updated.power == 3.0


def test_broadcast_update_partial_fields(client):
    """POST /broadcast/<id>/update – updates only some fields."""
    region = _create_region()
    org = _create_organisation()
    broadcast = _create_broadcast(
        org, region, smi_name="Original", frequency="9.0", power=1.0
    )

    data = {
        "org_id": org.id,
        "smi_name": "Modified",
        "smi_rating": "",
        "district_name": "Original District",
        "district_population": "5000",
        "region_id": region.id,
        "frequency": "9.0",
        "power": "",
    }

    rv = client.post(f"/broadcast/{broadcast.id}/update", data=data, follow_redirects=True)
    assert rv.status_code == 200

    updated = Broadcast.query.get(broadcast.id)
    assert updated.smi_name == "Modified"
    assert updated.smi_rating is None  # Empty field
    assert updated.power is None  # Empty field


def test_broadcast_update_nonexistent_broadcast(client):
    """GET/POST /broadcast/999/update – returns 404 for nonexistent broadcast."""
    rv = client.get("/broadcast/999/update")
    assert rv.status_code == 404

    rv = client.post("/broadcast/999/update", data={})
    assert rv.status_code == 404


def test_broadcast_update_changes_region(client):
    """POST /broadcast/<id>/update – changes the region for a broadcast."""
    region1 = _create_region("Region 1", rating=1.0)
    region2 = _create_region("Region 2", rating=2.0)
    org = _create_organisation()
    broadcast = _create_broadcast(org, region1)

    assert broadcast.region_id == region1.id

    data = {
        "org_id": org.id,
        "smi_name": broadcast.smi_name,
        "smi_rating": broadcast.smi_rating,
        "district_name": broadcast.district_name,
        "district_population": broadcast.district_population,
        "region_id": region2.id,
    }

    rv = client.post(f"/broadcast/{broadcast.id}/update", data=data, follow_redirects=True)
    assert rv.status_code == 200

    updated = Broadcast.query.get(broadcast.id)
    assert updated.region_id == region2.id


# -------- Broadcast Delete Tests -------- #
def test_broadcast_delete(client):
    """POST /broadcast/<id>/delete – deletes a broadcast."""
    region = _create_region()
    org = _create_organisation()
    broadcast = _create_broadcast(org, region)
    broadcast_id = broadcast.id

    rv = client.post(f"/broadcast/{broadcast_id}/delete", follow_redirects=True)
    assert rv.status_code == 200
    assert "Все трансляции" in rv.data.decode("utf-8")

    # Verify deletion
    assert Broadcast.query.get(broadcast_id) is None


def test_broadcast_delete_nonexistent(client):
    """POST /broadcast/999/delete – returns 404 for nonexistent broadcast."""
    rv = client.post("/broadcast/999/delete")
    assert rv.status_code == 404


def test_broadcast_delete_multiple_broadcasts(client):
    """POST /broadcast/<id>/delete – deletes only the specified broadcast."""
    region = _create_region()
    org = _create_organisation()
    bc1 = _create_broadcast(org, region, smi_name="SMI-1")
    bc2 = _create_broadcast(org, region, smi_name="SMI-2")

    rv = client.post(f"/broadcast/{bc1.id}/delete", follow_redirects=True)
    assert rv.status_code == 200

    # First broadcast should be deleted, second should remain
    assert Broadcast.query.get(bc1.id) is None
    assert Broadcast.query.get(bc2.id) is not None


# -------- Integration Tests -------- #
def test_broadcast_full_workflow(client):
    """Test complete workflow: create, list, update, delete."""
    region = _create_region("Integration Region")
    org = _create_organisation("Integration Org")

    # Create
    create_data = {
        "org_id": org.id,
        "smi_name": "Integration SMI",
        "smi_rating": "6.0",
        "district_name": "Integration District",
        "district_population": "7500",
        "region_id": region.id,
        "frequency": "10.0",
        "power": "1.5",
    }
    rv = client.post("/broadcast/create", data=create_data, follow_redirects=True)
    assert rv.status_code == 200

    broadcast = Broadcast.query.filter_by(smi_name="Integration SMI").first()
    assert broadcast is not None
    bc_id = broadcast.id

    # List
    rv = client.get("/broadcast/list")
    assert rv.status_code == 200
    assert b"Integration SMI" in rv.data

    # Update
    update_data = {
        "org_id": org.id,
        "smi_name": "Updated Integration SMI",
        "smi_rating": "7.0",
        "district_name": "Integration District",
        "district_population": "7500",
        "region_id": region.id,
        "frequency": "10.5",
        "power": "2.0",
    }
    rv = client.post(f"/broadcast/{bc_id}/update", data=update_data, follow_redirects=True)
    assert rv.status_code == 200

    updated = Broadcast.query.get(bc_id)
    assert updated.smi_name == "Updated Integration SMI"
    assert updated.smi_rating == 7.0

    # Delete
    rv = client.post(f"/broadcast/{bc_id}/delete", follow_redirects=True)
    assert rv.status_code == 200
    assert Broadcast.query.get(bc_id) is None
