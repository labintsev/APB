# tests/test_district_views.py
import pytest
from flask import url_for
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Application factory & models
from adcalc import create_app
from adcalc.models import db, Region, District


@pytest.fixture
def app():
    """Create a Flask app configured for testing."""
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        }
    )
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def create_region():
    """Create a single region and commit it."""
    def _create(name="Test Region"):
        region = Region(name=name)
        db.session.add(region)
        db.session.commit()
        return region

    return _create


@pytest.fixture
def create_district(create_region):
    """Create a district that belongs to the provided region."""
    def _create(name="Test District", population=1000, region=None):
        if region is None:
            region = create_region()
        district = District(name=name, population=population, region_id=region.id)
        db.session.add(district)
        db.session.commit()
        return district

    return _create


# --------------------------------------------------------------------------- #
#   LIST VIEW
# --------------------------------------------------------------------------- #
def test_district_list_empty(client):
    """GET /district/list returns an empty table when no districts exist."""
    resp = client.get("/district/list")
    assert resp.status_code == 200
    # The template shows a message when no districts
    assert "Районов вещания в базе данных не найдено" in resp.data.decode("utf-8")


def test_district_list_with_entries(client, create_district):
    """All districts in the DB appear in the list view."""
    d1 = create_district(name="Alpha")
    d2 = create_district(name="Beta", population=2500)
    resp = client.get("/district/list")
    assert resp.status_code == 200
    assert b"Alpha" in resp.data
    assert b"Beta" in resp.data
    # Population is rendered with “тыс. чел.” suffix
    assert "2500 тыс." in resp.data.decode("utf-8")


# --------------------------------------------------------------------------- #
#   CREATE VIEW
# --------------------------------------------------------------------------- #
def test_district_create(client, create_region):
    """POST /district/create adds a new district and redirects to list."""
    region = create_region(name="Creation Region")
    data = {
        "name": "New District",
        "population": "4500",
        "region_id": str(region.id),
    }
    resp = client.post("/district/create", data=data, follow_redirects=True)
    assert resp.status_code == 200
    assert b"New District" in resp.data
    # Verify persistence
    district = District.query.filter_by(name="New District").first()
    assert district is not None
    assert district.population == 4500
    assert district.region_id == region.id


# --------------------------------------------------------------------------- #
#   UPDATE VIEW
# --------------------------------------------------------------------------- #
def test_district_update(client, create_district, create_region):
    """POST /district/<id>/update changes district data and redirects to list."""
    old_region = create_region(name="Old Region")
    district = create_district(name="Old Name", population=1000, region=old_region)

    new_region = create_region(name="New Region")
    data = {
        "name": "Updated Name",
        "population": "2000",
        "region_id": str(new_region.id),
    }
    resp = client.post(
        f"/district/{district.id}/update", data=data, follow_redirects=True
    )
    assert resp.status_code == 200
    assert b"Updated Name" in resp.data
    assert b"2000" in resp.data
    assert new_region.name.encode() in resp.data

    # Verify database state
    district = District.query.get(district.id)
    assert district.name == "Updated Name"
    assert district.population == 2000
    assert district.region_id == new_region.id


# --------------------------------------------------------------------------- #
#   DELETE VIEW
# --------------------------------------------------------------------------- #
def test_district_delete(client, create_district):
    """POST /district/<id>/delete removes the district and redirects to list."""
    district = create_district(name="To Be Deleted")
    resp = client.post(f"/district/{district.id}/delete", follow_redirects=True)
    assert resp.status_code == 200
    # District should no longer be in the database
    assert District.query.get(district.id) is None
    # List view should not show the deleted district
    assert b"To Be Deleted" not in resp.data