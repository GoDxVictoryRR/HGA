"""
tests/conftest.py
Shared pytest fixtures for the HostelGuard test suite.
Provides fake clock, temporary database, keystore, fast bcrypt,
and system builders for both insecure and secure modes.
"""

import pytest
import random
from hostelguard.clock import FakeClock
from hostelguard.db import Database
from hostelguard import config
from hostelguard.access.registry import DeviceRegistry
from hostelguard.crypto.keystore import KeyStore
from hostelguard.integration.profiles import build_insecure_system, build_secure_system


@pytest.fixture(autouse=True)
def fast_bcrypt_fixture():
    """Ensure fast bcrypt cost is used across all tests for speed."""
    DeviceRegistry._bcrypt_cost = config.BCRYPT_COST_TEST
    yield
    DeviceRegistry._bcrypt_cost = config.BCRYPT_COST_NORMAL


@pytest.fixture(autouse=True)
def seed_random():
    """Seed python random for repeatable tests."""
    random.seed(config.SIM_RANDOM_SEED)
    yield


@pytest.fixture
def fake_clock():
    """Return a controllable fake clock."""
    return FakeClock(start=1000000.0)


@pytest.fixture
def temp_db(tmp_path):
    """Return a fresh temporary SQLite database."""
    db_path = tmp_path / "test_hostelguard.db"
    db = Database(db_path)
    yield db
    db.close()


@pytest.fixture
def temp_keystore(tmp_path):
    """Return a fresh temporary KeyStore."""
    ks_path = tmp_path / "test_keystore.json"
    return KeyStore(ks_path)


@pytest.fixture
def insecure_sys(tmp_path, fake_clock):
    """Return a clean insecure system container."""
    db = Database(tmp_path / "insecure_test.db")
    system = build_insecure_system(clock=fake_clock, db=db)
    yield system
    db.close()


@pytest.fixture
def secure_sys(tmp_path, fake_clock):
    """Return a clean secure system container."""
    db = Database(tmp_path / "secure_test.db")
    system = build_secure_system(clock=fake_clock, db=db)
    yield system
    db.close()
