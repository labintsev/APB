"""
tests.test_smi_views.py
Test the views related to SMIs.
"""
import pytest
import sys
import os
from unittest.mock import patch

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adcalc import create_app
from adcalc.models import db, Organisation, Smi, Region, District, Broadcast


@pytest.fixture
def app():
    """Create a Flask app configured for testing."""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the Flask app."""
    return app.test_client()


@pytest.fixture
def create_smi():
    """Convenience fixture to add a Smi to the DB."""
    def _create(name='Test SMI', rating='5', male=50):
        smi = Smi(name=name, rating=rating, male=male)
        db.session.add(smi)
        db.session.commit()
        return smi
    return _create


def test_smi_list_empty(client):
    """GET /smi/list returns an empty list when no SMIs exist."""
    resp = client.get('/smi/list')
    assert resp.status_code == 200
    assert b'No SMIs found' not in resp.data  # Adjust based on your template


def test_smi_list_with_entries(client, create_smi):
    """SMIs created in the DB appear in the list view."""
    smi1 = create_smi(name='SMI One')
    smi2 = create_smi(name='SMI Two')
    resp = client.get('/smi/list')
    assert resp.status_code == 200
    assert smi1.name.encode() in resp.data
    assert smi2.name.encode() in resp.data


def test_smi_create(client):
    """POST /smi/create adds a new SMI and redirects to the list."""
    data = {'name': 'New SMI', 'rating': 4, 'male': 50}
    resp = client.post('/smi/create', data=data, follow_redirects=True)
    assert resp.status_code == 200
    assert b'New SMI' in resp.data
    # Verify persistence
    smi = Smi.query.filter_by(name='New SMI').first()
    assert smi is not None
    assert smi.rating == 4
    assert smi.male == 50


def test_smi_update(client, create_smi):
    """POST /smi/<id>/update changes the SMI and redirects to the list."""
    smi = create_smi(name='Old Name', rating='1', male=50)
    data = {'name': 'Updated Name', 'rating': 5, 'male': 50}
    resp = client.post(f'/smi/{smi.id}/update', data=data, follow_redirects=True)
    assert resp.status_code == 200
    assert b'Updated Name' in resp.data
    # Verify changes persisted
    smi = Smi.query.get(smi.id)
    assert smi.name == 'Updated Name'
    assert smi.rating == 5
    assert smi.male == 50


def test_smi_delete(client, create_smi):
    """POST /smi/<id>/delete removes the SMI and redirects to the list."""
    smi = create_smi(name='To Be Deleted')
    resp = client.post(f'/smi/{smi.id}/delete', follow_redirects=True)
    assert resp.status_code == 200
    # SMI should no longer be in the database
    assert Smi.query.get(smi.id) is None
    # List view should not show the deleted SMI
    assert b'To Be Deleted' not in resp.data