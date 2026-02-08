# tests/test_broadcast_excel_upload.py
import pytest
import sys
import os
import json
from io import BytesIO

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


# -------- Excel Upload Tests -------- #
def test_broadcast_upload_excel_success(client):
    """POST /broadcast/upload_excel – successfully upload broadcasts from Excel"""
    # Create required organisations and regions
    org = _create_organisation("Test Org")
    region = _create_region("Test Region", rating=1.0)
    
    # Create minimal Excel file content using pandas
    import pandas as pd
    df = pd.DataFrame({
        'org_id': [org.id],
        'smi_name': ['Test SMI'],
        'smi_rating': [10.0],
        'smi_male_proportion': [0.3],
        'district_name': ['Test District'],
        'district_population': [5000],
        'region_id': [region.id],
        'frequency': ['9.5'],
        'power': [1.0]
    })
    
    # Write to bytes
    from io import BytesIO
    excel_file = BytesIO()
    df.to_excel(excel_file, index=False)
    excel_file.seek(0)
    
    # Upload file
    rv = client.post(
        '/broadcast/upload_excel',
        data={'excel_file': (excel_file, 'test.xlsx')},
        content_type='multipart/form-data'
    )
    
    # Should redirect to broadcast list
    assert rv.status_code == 302
    
    # Verify broadcast was created
    broadcasts = Broadcast.query.all()
    assert len(broadcasts) == 1
    assert broadcasts[0].smi_name == 'Test SMI'
    assert broadcasts[0].district_name == 'Test District'
    assert broadcasts[0].smi_rating == 10.0
    assert broadcasts[0].district_population == 5000


def test_broadcast_upload_excel_multiple_rows(client):
    """POST /broadcast/upload_excel – upload multiple broadcasts from Excel"""
    # Create required data
    org1 = _create_organisation("Org 1")
    org2 = _create_organisation("Org 2")
    region1 = _create_region("Region 1", rating=1.0)
    region2 = _create_region("Region 2", rating=1.5)
    
    # Create Excel file with multiple rows
    import pandas as pd
    df = pd.DataFrame({
        'org_id': [org1.id, org2.id, org1.id],
        'smi_name': ['SMI 1', 'SMI 2', 'SMI 3'],
        'smi_rating': [10.0, 15.0, 8.0],
        'smi_male_proportion': [0.3, 0.4, 0.2],
        'district_name': ['District 1', 'District 2', 'District 1'],
        'district_population': [5000, 7000, 5000],
        'region_id': [region1.id, region2.id, region1.id],
        'frequency': ['9.5', '104.5', '10.0'],
        'power': [1.0, 2.0, 1.5]
    })
    
    from io import BytesIO
    excel_file = BytesIO()
    df.to_excel(excel_file, index=False)
    excel_file.seek(0)
    
    rv = client.post(
        '/broadcast/upload_excel',
        data={'excel_file': (excel_file, 'test.xlsx')},
        content_type='multipart/form-data'
    )
    
    assert rv.status_code == 302
    
    # Verify all broadcasts were created
    broadcasts = Broadcast.query.all()
    assert len(broadcasts) == 3
    assert broadcasts[0].smi_name == 'SMI 1'
    assert broadcasts[1].smi_name == 'SMI 2'
    assert broadcasts[2].smi_name == 'SMI 3'
    assert broadcasts[1].district_population == 7000


def test_broadcast_upload_excel_no_file(client):
    """POST /broadcast/upload_excel – handle missing file gracefully"""
    rv = client.post(
        '/broadcast/upload_excel',
        data={},
        content_type='multipart/form-data'
    )
    
    # Should redirect back to list
    assert rv.status_code == 302
    
    # No broadcasts should be created
    assert Broadcast.query.count() == 0


def test_broadcast_upload_excel_empty_file(client):
    """POST /broadcast/upload_excel – handle empty Excel file"""
    from io import BytesIO
    import pandas as pd
    
    # Create empty DataFrame
    df = pd.DataFrame()
    excel_file = BytesIO()
    df.to_excel(excel_file, index=False)
    excel_file.seek(0)
    
    rv = client.post(
        '/broadcast/upload_excel',
        data={'excel_file': (excel_file, 'empty.xlsx')},
        content_type='multipart/form-data'
    )
    
    # Should still redirect
    assert rv.status_code == 302
    
    # No broadcasts should be created
    assert Broadcast.query.count() == 0


def test_broadcast_upload_excel_invalid_org_id(client):
    """POST /broadcast/upload_excel – handle invalid organisation ID"""
    region = _create_region("Test Region")
    
    import pandas as pd
    df = pd.DataFrame({
        'org_id': [9999],  # Non-existent org
        'smi_name': ['Test SMI'],
        'smi_rating': [10.0],
        'smi_male_proportion': [0.3],
        'district_name': ['Test District'],
        'district_population': [5000],
        'region_id': [region.id],
        'frequency': ['9.5'],
        'power': [1.0]
    })
    
    from io import BytesIO
    excel_file = BytesIO()
    df.to_excel(excel_file, index=False)
    excel_file.seek(0)
    
    rv = client.post(
        '/broadcast/upload_excel',
        data={'excel_file': (excel_file, 'test.xlsx')},
        content_type='multipart/form-data'
    )
    
    # Should still redirect (error is handled silently)
    assert rv.status_code == 302
    
    # No broadcasts should be created
    assert Broadcast.query.count() == 0


def test_broadcast_upload_excel_invalid_region_id(client):
    """POST /broadcast/upload_excel – handle invalid region ID"""
    org = _create_organisation("Test Org")
    
    import pandas as pd
    df = pd.DataFrame({
        'org_id': [org.id],
        'smi_name': ['Test SMI'],
        'smi_rating': [10.0],
        'smi_male_proportion': [0.3],
        'district_name': ['Test District'],
        'district_population': [5000],
        'region_id': [9999],  # Non-existent region
        'frequency': ['9.5'],
        'power': [1.0]
    })
    
    from io import BytesIO
    excel_file = BytesIO()
    df.to_excel(excel_file, index=False)
    excel_file.seek(0)
    
    rv = client.post(
        '/broadcast/upload_excel',
        data={'excel_file': (excel_file, 'test.xlsx')},
        content_type='multipart/form-data'
    )
    
    assert rv.status_code == 302
    
    # No broadcasts should be created
    assert Broadcast.query.count() == 0


def test_broadcast_upload_excel_with_nulls(client):
    """POST /broadcast/upload_excel – handle NULL/empty values in optional fields"""
    org = _create_organisation("Test Org")
    region = _create_region("Test Region")
    
    import pandas as pd
    df = pd.DataFrame({
        'org_id': [org.id],
        'smi_name': [None],  # NULL
        'smi_rating': [None],  # NULL
        'smi_male_proportion': [None],  # NULL
        'district_name': ['Test District'],
        'district_population': [None],  # NULL
        'region_id': [region.id],
        'frequency': ['9.5'],
        'power': [None]  # NULL
    })
    
    from io import BytesIO
    excel_file = BytesIO()
    df.to_excel(excel_file, index=False)
    excel_file.seek(0)
    
    rv = client.post(
        '/broadcast/upload_excel',
        data={'excel_file': (excel_file, 'test.xlsx')},
        content_type='multipart/form-data'
    )
    
    assert rv.status_code == 302
    
    # Broadcast should be created with NULL values
    broadcasts = Broadcast.query.all()
    assert len(broadcasts) == 1
    assert broadcasts[0].smi_name is None
    assert broadcasts[0].smi_rating is None
    assert broadcasts[0].district_population is None


def test_broadcast_upload_excel_preserves_numeric_types(client):
    """POST /broadcast/upload_excel – preserve numeric types correctly"""
    org = _create_organisation("Test Org")
    region = _create_region("Test Region")
    
    import pandas as pd
    df = pd.DataFrame({
        'org_id': [org.id],
        'smi_name': ['Test SMI'],
        'smi_rating': [10.5],  # Float
        'smi_male_proportion': [0.45],  # Float
        'district_name': ['Test District'],
        'district_population': [5000],  # Integer
        'region_id': [region.id],
        'frequency': ['9.5'],
        'power': [1.5]  # Float
    })
    
    from io import BytesIO
    excel_file = BytesIO()
    df.to_excel(excel_file, index=False)
    excel_file.seek(0)
    
    rv = client.post(
        '/broadcast/upload_excel',
        data={'excel_file': (excel_file, 'test.xlsx')},
        content_type='multipart/form-data'
    )
    
    assert rv.status_code == 302
    
    broadcasts = Broadcast.query.all()
    assert len(broadcasts) == 1
    assert broadcasts[0].smi_rating == 10.5
    assert broadcasts[0].smi_male_proportion == 0.45
    assert broadcasts[0].district_population == 5000
    assert broadcasts[0].power == 1.5


def test_broadcast_upload_excel_duplicate_data(client):
    """POST /broadcast/upload_excel – handle duplicate rows correctly"""
    org = _create_organisation("Test Org")
    region = _create_region("Test Region")
    
    import pandas as pd
    df = pd.DataFrame({
        'org_id': [org.id, org.id],  # Same org twice
        'smi_name': ['Same SMI', 'Same SMI'],
        'smi_rating': [10.0, 10.0],
        'smi_male_proportion': [0.3, 0.3],
        'district_name': ['Same District', 'Same District'],
        'district_population': [5000, 5000],
        'region_id': [region.id, region.id],
        'frequency': ['9.5', '9.5'],
        'power': [1.0, 1.0]
    })
    
    from io import BytesIO
    excel_file = BytesIO()
    df.to_excel(excel_file, index=False)
    excel_file.seek(0)
    
    rv = client.post(
        '/broadcast/upload_excel',
        data={'excel_file': (excel_file, 'test.xlsx')},
        content_type='multipart/form-data'
    )
    
    assert rv.status_code == 302
    
    # Both duplicates should be created
    broadcasts = Broadcast.query.all()
    assert len(broadcasts) == 2
    assert broadcasts[0].smi_name == 'Same SMI'
    assert broadcasts[1].smi_name == 'Same SMI'


def test_broadcast_upload_excel_large_file(client):
    """POST /broadcast/upload_excel – handle large Excel file (100 rows)"""
    org = _create_organisation("Test Org")
    region = _create_region("Test Region")
    
    import pandas as pd
    rows = []
    for i in range(100):
        rows.append({
            'org_id': org.id,
            'smi_name': f'SMI {i}',
            'smi_rating': 10.0 + i * 0.1,
            'smi_male_proportion': 0.3 + i * 0.001,
            'district_name': f'District {i}',
            'district_population': 5000 + i * 100,
            'region_id': region.id,
            'frequency': f'{9.5 + i * 0.01}',
            'power': 1.0 + i * 0.01
        })
    
    df = pd.DataFrame(rows)
    
    from io import BytesIO
    excel_file = BytesIO()
    df.to_excel(excel_file, index=False)
    excel_file.seek(0)
    
    rv = client.post(
        '/broadcast/upload_excel',
        data={'excel_file': (excel_file, 'test.xlsx')},
        content_type='multipart/form-data'
    )
    
    assert rv.status_code == 302
    
    # All 100 broadcasts should be created
    broadcasts = Broadcast.query.all()
    assert len(broadcasts) == 100
    assert broadcasts[0].smi_name == 'SMI 0'
    assert broadcasts[99].smi_name == 'SMI 99'
