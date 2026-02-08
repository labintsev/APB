# tests/test_models.py
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adcalc.models import db, Organisation, Region, Broadcast


def test_organisation_model():
    """Test Organisation model"""
    org = Organisation(name="Тестовая организация")
    assert org.name == "Тестовая организация"
    assert str(org) == "Тестовая организация"


def test_region_model():
    """Test Region model"""
    region = Region(name="Тестовый регион", rating=1.0)
    assert region.name == "Тестовый регион"
    assert region.rating == 1.0
    assert str(region) == "Тестовый регион"


def test_broadcast_model():
    """Test Broadcast model with embedded SMI and District fields"""
    region = Region(name="Тестовый регион", rating=1.0)
    org = Organisation(name="Тестовая организация")
    
    broadcast = Broadcast(
        org=org,
        region=region,
        smi_name="Тестовое СМИ",
        smi_rating=1.0,
        smi_male_proportion=0.3,
        district_name="Тестовый район",
        district_population=10000,
        frequency="10.5",
        power=0.8
    )
    assert broadcast is not None
    assert str(broadcast) == "Тестовая организация, Тестовый район, Тестовое СМИ"
    assert broadcast.smi_rating == 1.0
    assert broadcast.district_population == 10000