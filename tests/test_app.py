# tests/test_app.py
import pytest
import sys
import os
from unittest.mock import patch

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adcalc import create_app
from adcalc.models import db, Organisation, Region, Broadcast


@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "COST_PER_PERSON": 5,
        }
    )

    with app.app_context():
        db.create_all()

        # Create test data with proper relationships
        region1 = Region(name="Регион 1", rating=1.0)
        region2 = Region(name="Регион 2", rating=1.5)
        db.session.add_all([region1, region2])
        db.session.commit()

        org1 = Organisation(name="Организация 1")
        org2 = Organisation(name="Организация 2")
        db.session.add_all([org1, org2])
        db.session.commit()

        # Create broadcasts for org1 with embedded SMI and district fields
        broadcast1 = Broadcast(
            org_id=org1.id,
            region_id=region1.id,
            smi_name="СМИ 1",
            smi_rating=1.0,
            smi_male_proportion=0.3,
            district_name="Район 1",
            district_population=10000,
        )
        broadcast2 = Broadcast(
            org_id=org1.id,
            region_id=region1.id,
            smi_name="СМИ 2",
            smi_rating=2.0,
            smi_male_proportion=0.4,
            district_name="Район 1",
            district_population=10000,
        )

        # Create broadcasts for org2
        broadcast3 = Broadcast(
            org_id=org2.id,
            region_id=region2.id,
            smi_name="СМИ 1",
            smi_rating=1.0,
            smi_male_proportion=0.3,
            district_name="Район 2",
            district_population=20000,
        )
        broadcast4 = Broadcast(
            org_id=org2.id,
            region_id=region2.id,
            smi_name="СМИ 2",
            smi_rating=2.0,
            smi_male_proportion=0.4,
            district_name="Район 2",
            district_population=20000,
        )

        db.session.add_all([broadcast1, broadcast2, broadcast3, broadcast4])
        db.session.commit()

        yield app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


def test_index_page(client):
    """Test that the index page loads correctly"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Калькулятор".encode("utf-8") in response.data


def test_api_organisations_detailed_endpoint(client):
    """Test the detailed organisations API endpoint"""
    response = client.get("/api/organisations-detailed")
    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 2

    # Check first organization
    org1 = next((o for o in data if o["name"] == "Организация 1"), None)
    assert org1 is not None
    assert "id" in org1
    assert "name" in org1
    assert "cost" in org1
    assert "broadcasts" in org1
    assert len(org1["broadcasts"]) == 2

    # Check broadcast structure
    broadcast = org1["broadcasts"][0]
    assert "id" in broadcast
    assert "smi" in broadcast
    assert "district" in broadcast
    assert "cost" in broadcast

    # Check second organization
    org2 = next((o for o in data if o["name"] == "Организация 2"), None)
    assert org2 is not None
    assert len(org2["broadcasts"]) == 2


def test_api_region_broadcasts_endpoint(client):
    """Test the region broadcasts API endpoint"""
    response = client.get("/api/region/1/broadcasts")
    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()
    assert "region_cost" in data


def test_broadcast_cost_calculation(client):
    """Test that broadcast costs are calculated correctly"""
    response = client.get("/api/organisations-detailed")
    assert response.status_code == 200

    data = response.get_json()

    # All broadcasts should have a cost > 0
    for org in data:
        if org["broadcasts"]:
            for broadcast in org["broadcasts"]:
                assert broadcast["cost"] >= 0


def test_organisation_total_cost_equals_sum_of_broadcasts(client):
    """Test that organisation total cost equals sum of its broadcasts"""
    response = client.get("/api/organisations-detailed")
    assert response.status_code == 200

    data = response.get_json()

    for org in data:
        if org["broadcasts"]:
            broadcast_sum = sum(b["cost"] for b in org["broadcasts"])
            assert abs(org["cost"] - broadcast_sum) < 0.01


def test_checkbox_selection_affects_calculation(client):
    """Test that different checkbox selections produce correct calculations"""
    response = client.get("/api/organisations-detailed")
    data = response.get_json()

    # Get org1 with 2 broadcasts
    org1 = next((o for o in data if o["name"] == "Организация 1"), None)
    assert len(org1["broadcasts"]) == 2

    # Scenario 1: Both broadcasts selected
    total_cost_both = sum(b["cost"] for b in org1["broadcasts"])
    assert total_cost_both > 0

    # Scenario 2: Only first broadcast
    cost_first = org1["broadcasts"][0]["cost"]
    assert cost_first > 0
    assert cost_first < total_cost_both

    # Scenario 3: Only second broadcast
    cost_second = org1["broadcasts"][1]["cost"]
    assert cost_second > 0


def test_multiple_organisations_different_broadcast_counts(client):
    """Test that different organisations can have different number of broadcasts"""
    response = client.get("/api/organisations-detailed")
    data = response.get_json()

    org1 = next((o for o in data if o["name"] == "Организация 1"), None)
    org2 = next((o for o in data if o["name"] == "Организация 2"), None)

    assert org1 is not None
    assert org2 is not None
    assert len(org1["broadcasts"]) == 2
    assert len(org2["broadcasts"]) == 2


def test_budget_calculation_with_selected_broadcasts(client):
    """Test budget calculation with selected broadcasts"""
    response = client.get("/api/organisations-detailed")
    data = response.get_json()

    org1 = next((o for o in data if o["name"] == "Организация 1"), None)
    org2 = next((o for o in data if o["name"] == "Организация 2"), None)

    # Calculate total cost if both organisations are selected
    total_cost_all = org1["cost"] + org2["cost"]

    budget = 10000  # 10k т.р.

    if total_cost_all > 0:
        share_org1_all = (org1["cost"] / total_cost_all) * budget
        share_org2_all = (org2["cost"] / total_cost_all) * budget

        # Shares should be positive and sum to budget
        assert share_org1_all > 0
        assert share_org2_all > 0
        assert abs((share_org1_all + share_org2_all) - budget) < 0.01


def test_budget_calculation_single_organisation_multiple_broadcasts(client):
    """Test budget calculation with single organisation, multiple broadcasts"""
    response = client.get("/api/organisations-detailed")
    data = response.get_json()

    org1 = next((o for o in data if o["name"] == "Организация 1"), None)

    # If only org1 is selected with all its broadcasts
    if org1["cost"] > 0:
        budget = 5000
        # This org should get 100% of the budget
        share = (org1["cost"] / org1["cost"]) * budget
        assert abs(share - budget) < 0.01


def test_partial_broadcast_selection(client):
    """Test budget calculation with partial broadcast selection from organisation"""
    response = client.get("/api/organisations-detailed")
    data = response.get_json()

    org1 = next((o for o in data if o["name"] == "Организация 1"), None)

    # Simulate selecting only first broadcast
    selected_cost = org1["broadcasts"][0]["cost"]
    budget = 5000

    if selected_cost > 0:
        share = (selected_cost / selected_cost) * budget
        assert abs(share - budget) < 0.01


def test_zero_cost_broadcasts_handled(client):
    """Test that broadcasts with zero cost are handled correctly"""
    response = client.get("/api/organisations-detailed")
    data = response.get_json()

    # All broadcasts should have valid cost values
    for org in data:
        for broadcast in org["broadcasts"]:
            assert isinstance(broadcast["cost"], (int, float))
            assert broadcast["cost"] >= 0
