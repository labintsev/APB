# tests/test_models.py
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adcalc.models import db, Organisation, Smi, Region, District, Broadcast


def test_organisation_model():
    """Test Organisation model"""
    org = Organisation(name="Тестовая организация")
    assert org.name == "Тестовая организация"
    assert str(org) == "Тестовая организация"


def test_smi_model():
    """Test Smi model"""
    smi = Smi(name="Тестовое СМИ", rating=1.0)
    assert smi.name == "Тестовое СМИ"
    assert smi.rating == 1.0
    assert str(smi) == "Тестовое СМИ"


def test_region_model():
    """Test Region model"""
    region = Region(name="Тестовый регион", rating=1.0)
    assert region.name == "Тестовый регион"
    assert region.rating == 1.0
    assert str(region) == "Тестовый регион"


def test_district_model():
    """Test District model"""
    district = District(name="Тестовый район", population=10000)
    assert district.name == "Тестовый район"
    assert district.population == 10000
    assert str(district) == "Тестовый район"


def test_broadcast_model():
    """Test Broadcast model"""
    broadcast = Broadcast(
        region=Region(name="Тестовый регион", rating=1.0),
        district=District(name="Тестовый район", population=10000),
        smi=Smi(name="Тестовое СМИ", rating=1.0),
        org=Organisation(name="Тестовая организация")
    )
    assert broadcast is not None
    assert str(broadcast) == "Тестовая организация, Тестовый район, Тестовое СМИ"