# tests/test_app.py
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
    """Create application for testing"""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'COST_PER_PERSON': 5
    })
    
    with app.app_context():
        db.create_all()
        
        # Create test data with proper relationships
        region = Region(name="Тестовый регион", rating=1.0)
        db.session.add(region)
        db.session.commit()
        
        district = District(name="Тестовый район", population=10000, region_id=region.id)
        db.session.add(district)
        db.session.commit()
        
        smi = Smi(name="Тестовое СМИ", rating=1.0)
        db.session.add(smi)
        db.session.commit()
        
        organisation = Organisation(name="Тестовая организация")
        db.session.add(organisation)
        db.session.commit()
        
        broadcast = Broadcast(
            org_id=organisation.id,
            smi_id=smi.id,
            district_id=district.id,
            region_id=region.id
        )
        db.session.add(broadcast)
        db.session.commit()
        
        yield app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


def test_index_page(client):
    """Test that the index page loads correctly"""
    response = client.get('/')
    assert response.status_code == 200
    assert 'Калькулятор'.encode('utf-8') in response.data


def test_api_organisations_endpoint(client):
    """Test the organisations API endpoint"""
    response = client.get('/api/organisations')
    assert response.status_code == 200
    assert response.is_json
    
    data = response.get_json()
    assert isinstance(data, dict)
    assert len(data) > 0


def test_api_region_broadcasts_endpoint(client):
    """Test the region broadcasts API endpoint"""
    response = client.get('/api/region/1/broadcasts')
    assert response.status_code == 200
    assert response.is_json
    
    data = response.get_json()
    assert 'region_cost' in data


def test_budget_calculation(client):
    """Test the budget calculation functionality"""
    # Mock the calculate_cost function to return a known value
    with patch('adcalc.utils.calculate_cost') as mock_calc:
        mock_calc.return_value = 1000.0
        
        # Test form submission
        response = client.get('/', data={'budget': '5000'}, follow_redirects=True)
        assert response.status_code == 200
        
        # Test API endpoint directly
        response = client.get('/api/organisations')
        assert response.status_code == 200
        assert response.is_json
