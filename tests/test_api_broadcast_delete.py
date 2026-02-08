# tests/test_api_broadcast_delete.py
import pytest
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adcalc import create_app
from adcalc.models import db, Organisation, Region, Broadcast


@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'COST_PER_PERSON': 5
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


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


# -------- API Delete Tests -------- #
def test_api_broadcasts_delete_single(client):
    """POST /api/broadcasts/delete – delete a single broadcast by ID"""
    region = _create_region("Region 1")
    org = _create_organisation("Org 1")
    broadcast = _create_broadcast(org, region, smi_name="SMI 1")
    
    broadcast_id = broadcast.id
    
    # Verify broadcast exists before deletion
    assert Broadcast.query.get(broadcast_id) is not None
    
    # Send DELETE request
    rv = client.post(
        '/api/broadcasts/delete',
        data=json.dumps({'ids': [broadcast_id]}),
        content_type='application/json'
    )
    
    # Check response
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['success'] is True
    assert data['deleted'] == 1
    
    # Verify broadcast was deleted
    assert Broadcast.query.get(broadcast_id) is None


def test_api_broadcasts_delete_multiple(client):
    """POST /api/broadcasts/delete – delete multiple broadcasts by IDs"""
    region = _create_region("Region 1")
    org = _create_organisation("Org 1")
    
    broadcast1 = _create_broadcast(org, region, smi_name="SMI 1", district_name="District 1")
    broadcast2 = _create_broadcast(org, region, smi_name="SMI 2", district_name="District 2")
    broadcast3 = _create_broadcast(org, region, smi_name="SMI 3", district_name="District 3")
    
    id1, id2, id3 = broadcast1.id, broadcast2.id, broadcast3.id
    
    # Verify all broadcasts exist
    assert Broadcast.query.get(id1) is not None
    assert Broadcast.query.get(id2) is not None
    assert Broadcast.query.get(id3) is not None
    
    # Delete broadcasts 1 and 2
    rv = client.post(
        '/api/broadcasts/delete',
        data=json.dumps({'ids': [id1, id2]}),
        content_type='application/json'
    )
    
    # Check response
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['success'] is True
    assert data['deleted'] == 2
    
    # Verify correct broadcasts were deleted
    assert Broadcast.query.get(id1) is None
    assert Broadcast.query.get(id2) is None
    assert Broadcast.query.get(id3) is not None


def test_api_broadcasts_delete_empty_ids(client):
    """POST /api/broadcasts/delete – reject empty ids list"""
    rv = client.post(
        '/api/broadcasts/delete',
        data=json.dumps({'ids': []}),
        content_type='application/json'
    )
    
    assert rv.status_code == 400
    data = json.loads(rv.data)
    assert 'error' in data
    assert data['error'] == 'ids must be a non-empty list'


def test_api_broadcasts_delete_missing_ids(client):
    """POST /api/broadcasts/delete – reject request without ids field"""
    rv = client.post(
        '/api/broadcasts/delete',
        data=json.dumps({}),
        content_type='application/json'
    )
    
    assert rv.status_code == 400
    data = json.loads(rv.data)
    assert 'error' in data
    assert data['error'] == 'Missing ids field'


def test_api_broadcasts_delete_invalid_json(client):
    """POST /api/broadcasts/delete – handle invalid JSON gracefully"""
    rv = client.post(
        '/api/broadcasts/delete',
        data='invalid json',
        content_type='application/json'
    )
    
    assert rv.status_code == 400


def test_api_broadcasts_delete_nonexistent_ids(client):
    """POST /api/broadcasts/delete – gracefully handle non-existent IDs"""
    region = _create_region("Region 1")
    org = _create_organisation("Org 1")
    broadcast = _create_broadcast(org, region, smi_name="SMI 1")
    
    # Try to delete non-existent broadcast (with valid and invalid IDs)
    rv = client.post(
        '/api/broadcasts/delete',
        data=json.dumps({'ids': [9999, 8888]}),
        content_type='application/json'
    )
    
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['success'] is True
    assert data['deleted'] == 0  # No broadcasts were deleted


def test_api_broadcasts_delete_mixed_valid_invalid_ids(client):
    """POST /api/broadcasts/delete – delete valid IDs, ignore non-existent ones"""
    region = _create_region("Region 1")
    org = _create_organisation("Org 1")
    broadcast = _create_broadcast(org, region, smi_name="SMI 1")
    broadcast_id = broadcast.id
    
    # Delete with valid ID and non-existent ID
    rv = client.post(
        '/api/broadcasts/delete',
        data=json.dumps({'ids': [broadcast_id, 9999]}),
        content_type='application/json'
    )
    
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['success'] is True
    assert data['deleted'] == 1  # Only valid ID was deleted
    
    # Verify broadcast was deleted
    assert Broadcast.query.get(broadcast_id) is None


def test_api_broadcasts_delete_ids_not_list(client):
    """POST /api/broadcasts/delete – reject ids that is not a list"""
    rv = client.post(
        '/api/broadcasts/delete',
        data=json.dumps({'ids': 'not-a-list'}),
        content_type='application/json'
    )
    
    assert rv.status_code == 400
    data = json.loads(rv.data)
    assert 'error' in data
    assert data['error'] == 'ids must be a non-empty list'


def test_api_broadcasts_delete_large_batch(client):
    """POST /api/broadcasts/delete – delete large batch of broadcasts"""
    region = _create_region("Region 1")
    org = _create_organisation("Org 1")
    
    # Create 50 broadcasts
    broadcasts = []
    for i in range(50):
        broadcast = _create_broadcast(
            org, region, 
            smi_name=f"SMI {i}", 
            district_name=f"District {i}"
        )
        broadcasts.append(broadcast)
    
    # Get all IDs
    ids = [b.id for b in broadcasts]
    
    # Delete all
    rv = client.post(
        '/api/broadcasts/delete',
        data=json.dumps({'ids': ids}),
        content_type='application/json'
    )
    
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['success'] is True
    assert data['deleted'] == 50
    
    # Verify all were deleted
    assert Broadcast.query.count() == 0
