# tests/test_views_region.py
import pytest
from adcalc.models import db, Region


def _create_region(name, rating=1.0):
    """Create a test region."""
    region = Region(name=name, rating=rating)
    db.session.add(region)
    db.session.commit()
    return region


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


def test_region_list_view(client):
    """GET /region/list renders the region list page."""
    rv = client.get("/region/list")
    assert rv.status_code == 200
    assert "Средняя цена 1 минуты слушателя в регионе" in rv.data.decode('utf-8')


def test_region_coverage_view(client):
    """GET /region/coverage renders the region coverage page."""
    rv = client.get("/region/coverage")
    assert rv.status_code == 200
    assert "Покрытие регионов" in rv.data.decode('utf-8')


def test_region_update_view(client):
    """POST /region/<int:region_id>/update updates region rating."""
    region = _create_region("Test Region", 1.0)
    
    # Test updating region rating
    rv = client.post(f"/region/{region.id}/update", data={"rating": "2.5"})
    assert rv.status_code == 302  # Redirect after successful update
    
    # Verify the rating was updated
    updated_region = Region.query.get(region.id)
    assert updated_region.rating == 2.5


def test_region_update_view_invalid_region(client):
    """POST /region/<int:region_id>/update with invalid region ID returns 404."""
    rv = client.post("/region/999/update", data={"rating": "2.5"})
    assert rv.status_code == 404


def test_region_update_view_invalid_rating(client):
    """POST /region/<int:region_id>/update with invalid rating."""
    region = _create_region("Test Region", 1.0)
    
    # Test updating with invalid rating (non-numeric)
    rv = client.post(f"/region/{region.id}/update", data={"rating": "invalid"})
    assert rv.status_code == 500  # Server error due to invalid data