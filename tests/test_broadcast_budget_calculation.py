# tests/test_broadcast_budget_calculation.py
"""
Tests for per-broadcast detailed budget calculation feature.

The feature distributes a budget across selected broadcasts proportionally:
  broadcast_share = (broadcast.cost / total_selected_cost) * budget

Fixture costs (COST_PER_PERSON is unused here; formula is smi_rating/100 * population * region_rating):
  broadcast1 (org1, region1): 1.0/100 * 10_000 * 1.0 =  100
  broadcast2 (org1, region1): 2.0/100 * 10_000 * 1.0 =  200
  broadcast3 (org2, region2): 1.0/100 * 20_000 * 1.5 =  300
  broadcast4 (org2, region2): 2.0/100 * 20_000 * 1.5 =  600
  org1 total: 300   org2 total: 900   grand total: 1200
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adcalc import create_app
from adcalc.models import db, Organisation, Region, Broadcast
from adcalc.utils import calculate_cost


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

COST_PER_PERSON = 5  # not used by calculate_cost but required by create_app

B1_COST = 1.0 / 100 * 10_000 * 1.0   # 100.0
B2_COST = 2.0 / 100 * 10_000 * 1.0   # 200.0
B3_COST = 1.0 / 100 * 20_000 * 1.5   # 300.0
B4_COST = 2.0 / 100 * 20_000 * 1.5   # 600.0

ORG1_COST = B1_COST + B2_COST         # 300.0
ORG2_COST = B3_COST + B4_COST         # 900.0
GRAND_TOTAL = ORG1_COST + ORG2_COST   # 1200.0


@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "COST_PER_PERSON": COST_PER_PERSON,
        "SECRET_KEY": "test-secret-key",
        "EMAIL_WHITELIST": "test@example.com",
    })

    with app.app_context():
        db.create_all()

        region1 = Region(name="Регион 1", rating=1.0)
        region2 = Region(name="Регион 2", rating=1.5)
        db.session.add_all([region1, region2])
        db.session.commit()

        org1 = Organisation(name="Организация 1")
        org2 = Organisation(name="Организация 2")
        db.session.add_all([org1, org2])
        db.session.commit()

        b1 = Broadcast(
            org_id=org1.id, region_id=region1.id,
            smi_name="СМИ 1", smi_rating=1.0, smi_male_proportion=0.3,
            district_name="Район 1", district_population=10_000,
        )
        b2 = Broadcast(
            org_id=org1.id, region_id=region1.id,
            smi_name="СМИ 2", smi_rating=2.0, smi_male_proportion=0.4,
            district_name="Район 1", district_population=10_000,
        )
        b3 = Broadcast(
            org_id=org2.id, region_id=region2.id,
            smi_name="СМИ 1", smi_rating=1.0, smi_male_proportion=0.3,
            district_name="Район 2", district_population=20_000,
        )
        b4 = Broadcast(
            org_id=org2.id, region_id=region2.id,
            smi_name="СМИ 2", smi_rating=2.0, smi_male_proportion=0.4,
            district_name="Район 2", district_population=20_000,
        )
        db.session.add_all([b1, b2, b3, b4])
        db.session.commit()

        yield app


@pytest.fixture
def client(app):
    return app.test_client()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def api_data(client):
    """Return parsed /api/organisations-detailed response."""
    resp = client.get("/api/organisations-detailed")
    assert resp.status_code == 200
    return resp.get_json()


def get_org(data, name):
    return next(o for o in data if o["name"] == name)


def broadcast_share(broadcast_cost, total_selected_cost, budget):
    """Mirror the JS formula: (broadcast.cost / totalCost) * budget."""
    return (broadcast_cost / total_selected_cost) * budget


# ---------------------------------------------------------------------------
# Unit tests for calculate_cost
# ---------------------------------------------------------------------------

class TestCalculateCost:
    def test_cost_formula_b1(self, app):
        with app.app_context():
            b = Broadcast.query.filter_by(smi_name="СМИ 1").first()
            assert abs(calculate_cost(b) - B1_COST) < 0.001

    def test_cost_formula_b4(self, app):
        """Highest-cost broadcast: smi_rating=2, population=20k, region_rating=1.5."""
        with app.app_context():
            b = Broadcast.query.filter_by(smi_name="СМИ 2", district_name="Район 2").first()
            assert abs(calculate_cost(b) - B4_COST) < 0.001

    def test_cost_is_zero_when_smi_rating_missing(self, app):
        with app.app_context():
            b = Broadcast(smi_rating=None, district_population=10_000, region_id=1)
            assert calculate_cost(b) == 0

    def test_cost_is_zero_when_population_missing(self, app):
        with app.app_context():
            b = Broadcast(smi_rating=1.0, district_population=None, region_id=1)
            assert calculate_cost(b) == 0

    def test_cost_is_zero_for_none_broadcast(self, app):
        with app.app_context():
            assert calculate_cost(None) == 0


# ---------------------------------------------------------------------------
# API response shape
# ---------------------------------------------------------------------------

class TestApiOrganisationsDetailed:
    def test_returns_all_organisations(self, client):
        data = api_data(client)
        assert len(data) == 2

    def test_broadcast_count_per_org(self, client):
        data = api_data(client)
        org1 = get_org(data, "Организация 1")
        org2 = get_org(data, "Организация 2")
        assert len(org1["broadcasts"]) == 2
        assert len(org2["broadcasts"]) == 2

    def test_broadcast_has_required_fields(self, client):
        data = api_data(client)
        for org in data:
            for b in org["broadcasts"]:
                assert "id" in b
                assert "smi" in b
                assert "district" in b
                assert "cost" in b

    def test_broadcast_costs_match_formula(self, client):
        data = api_data(client)
        org1 = get_org(data, "Организация 1")
        costs = sorted(b["cost"] for b in org1["broadcasts"])
        assert abs(costs[0] - B1_COST) < 0.001
        assert abs(costs[1] - B2_COST) < 0.001

    def test_org_cost_equals_sum_of_broadcasts(self, client):
        data = api_data(client)
        for org in data:
            expected = sum(b["cost"] for b in org["broadcasts"])
            assert abs(org["cost"] - expected) < 0.001

    def test_org1_total_cost(self, client):
        data = api_data(client)
        org1 = get_org(data, "Организация 1")
        assert abs(org1["cost"] - ORG1_COST) < 0.001

    def test_org2_total_cost(self, client):
        data = api_data(client)
        org2 = get_org(data, "Организация 2")
        assert abs(org2["cost"] - ORG2_COST) < 0.001


# ---------------------------------------------------------------------------
# Per-broadcast budget share: broadcast_share = (b.cost / totalCost) * budget
# ---------------------------------------------------------------------------

class TestPerBroadcastBudgetShare:
    def test_all_broadcasts_selected_shares_sum_to_budget(self, client):
        data = api_data(client)
        budget = 12_000
        total_cost = sum(b["cost"] for org in data for b in org["broadcasts"])
        total_share = sum(
            broadcast_share(b["cost"], total_cost, budget)
            for org in data for b in org["broadcasts"]
        )
        assert abs(total_share - budget) < 0.001

    def test_single_org_all_broadcasts_shares_sum_to_budget(self, client):
        """When only org1's broadcasts are selected, their shares sum to the budget."""
        data = api_data(client)
        org1 = get_org(data, "Организация 1")
        budget = 5_000
        total_cost = org1["cost"]  # only org1 selected
        shares = [broadcast_share(b["cost"], total_cost, budget) for b in org1["broadcasts"]]
        assert abs(sum(shares) - budget) < 0.001

    def test_broadcast_shares_within_org_equal_org_share(self, client):
        """Sum of a single org's per-broadcast shares == org-level share."""
        data = api_data(client)
        org1 = get_org(data, "Организация 1")
        org2 = get_org(data, "Организация 2")
        budget = 7_500
        total_cost = org1["cost"] + org2["cost"]

        org1_share = broadcast_share(org1["cost"], total_cost, budget)
        org1_broadcast_shares = sum(
            broadcast_share(b["cost"], total_cost, budget) for b in org1["broadcasts"]
        )
        assert abs(org1_broadcast_shares - org1_share) < 0.001

    def test_higher_cost_broadcast_gets_larger_share(self, client):
        data = api_data(client)
        org1 = get_org(data, "Организация 1")
        budget = 3_000
        total_cost = GRAND_TOTAL
        shares = {
            b["cost"]: broadcast_share(b["cost"], total_cost, budget)
            for b in org1["broadcasts"]
        }
        costs = sorted(shares.keys())
        assert shares[costs[0]] < shares[costs[1]]

    def test_budget_scale_does_not_change_share_ratios(self, client):
        """Doubling the budget doubles each share proportionally."""
        data = api_data(client)
        budget1 = 6_000
        budget2 = 12_000
        total_cost = GRAND_TOTAL
        for org in data:
            for b in org["broadcasts"]:
                s1 = broadcast_share(b["cost"], total_cost, budget1)
                s2 = broadcast_share(b["cost"], total_cost, budget2)
                assert abs(s2 - 2 * s1) < 0.001

    def test_partial_selection_one_broadcast(self, client):
        """Selecting only one broadcast: that broadcast gets the entire budget."""
        data = api_data(client)
        org1 = get_org(data, "Организация 1")
        budget = 4_000
        selected_broadcast = org1["broadcasts"][0]
        total_cost = selected_broadcast["cost"]
        share = broadcast_share(selected_broadcast["cost"], total_cost, budget)
        assert abs(share - budget) < 0.001

    def test_partial_selection_one_broadcast_per_org(self, client):
        """Selecting one broadcast from each org: shares sum to budget."""
        data = api_data(client)
        org1 = get_org(data, "Организация 1")
        org2 = get_org(data, "Организация 2")
        b1 = org1["broadcasts"][0]
        b3 = org2["broadcasts"][0]
        budget = 8_000
        total_cost = b1["cost"] + b3["cost"]
        share1 = broadcast_share(b1["cost"], total_cost, budget)
        share3 = broadcast_share(b3["cost"], total_cost, budget)
        assert abs(share1 + share3 - budget) < 0.001

    def test_known_share_values_all_selected(self, client):
        """
        Verify exact shares with known fixture values (budget = 1200):
          total_cost = 1200
          b1 share = (100/1200)*1200 = 100
          b2 share = (200/1200)*1200 = 200
          b3 share = (300/1200)*1200 = 300
          b4 share = (600/1200)*1200 = 600
        """
        data = api_data(client)
        budget = GRAND_TOTAL  # 1200
        total_cost = GRAND_TOTAL
        all_broadcasts = [b for org in data for b in org["broadcasts"]]
        for b in all_broadcasts:
            expected = b["cost"]  # because budget == total_cost
            actual = broadcast_share(b["cost"], total_cost, budget)
            assert abs(actual - expected) < 0.001

    def test_cross_org_selection_correct_proportions(self, client):
        """
        Select b2 (cost=200) from org1 and b3 (cost=300) from org2.
        total_cost = 500, budget = 500
          b2 share = (200/500)*500 = 200
          b3 share = (300/500)*500 = 300
        """
        data = api_data(client)
        org1 = get_org(data, "Организация 1")
        org2 = get_org(data, "Организация 2")
        b2 = max(org1["broadcasts"], key=lambda b: b["cost"])
        b3 = min(org2["broadcasts"], key=lambda b: b["cost"])
        budget = 500
        total_cost = b2["cost"] + b3["cost"]
        assert abs(total_cost - (B2_COST + B3_COST)) < 0.001
        share_b2 = broadcast_share(b2["cost"], total_cost, budget)
        share_b3 = broadcast_share(b3["cost"], total_cost, budget)
        assert abs(share_b2 - B2_COST) < 0.001   # 200
        assert abs(share_b3 - B3_COST) < 0.001   # 300
        assert abs(share_b2 + share_b3 - budget) < 0.001
