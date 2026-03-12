# tests/test_broadcast_download.py
import pytest
import sys
import os
from io import BytesIO

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adcalc import create_app
from adcalc.models import db, Organisation, Region, Broadcast, User


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
    """Authenticated test client"""
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()

    test_client = app.test_client()
    with test_client:
        test_client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpass'
        })
    return test_client


# ---------- Export tests ----------

def test_broadcast_download_excel_empty(client):
    """GET /broadcast/download_excel should return an empty spreadsheet when no data exists"""
    rv = client.get('/broadcast/download_excel')
    assert rv.status_code == 200
    # read returned bytes as Excel
    import pandas as pd
    df = pd.read_excel(BytesIO(rv.data), sheet_name='table')
    assert df.empty


def test_broadcast_download_excel_with_data(client):
    """Spreadsheet should contain all existing broadcasts with the expected columns"""
    # prepare organisations, region, and broadcast
    with client.application.app_context():
        org = Organisation(name='Org1')
        db.session.add(org)
        reg = Region(name='Reg1', rating=1.2)
        db.session.add(reg)
        db.session.commit()
        b = Broadcast(
            org_id=org.id,
            region_id=reg.id,
            smi_name='SMI',
            smi_rating=5.0,
            smi_male_proportion=0.2,
            district_name='Dist',
            district_population=1000,
            frequency='9.5',
            power=1.0
        )
        db.session.add(b)
        db.session.commit()

    rv = client.get('/broadcast/download_excel')
    assert rv.status_code == 200
    import pandas as pd
    df = pd.read_excel(BytesIO(rv.data), sheet_name='table')
    expected_cols = [
        'org_id', 'org_name', 'region_id', 'smi_name', 'smi_rating',
        'smi_male_proportion', 'district_name', 'district_population',
        'frequency', 'power'
    ]
    assert list(df.columns) == expected_cols
    assert len(df) == 1
    assert df.loc[0, 'org_id'] == org.id
    assert df.loc[0, 'org_name'] == org.name
    assert df.loc[0, 'region_id'] == reg.id
    assert df.loc[0, 'smi_name'] == 'SMI'
    assert df.loc[0, 'district_population'] == 1000
