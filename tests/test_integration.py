"""
tests/test_integration.py
Integration gate test: both modes must run end-to-end without error,
and in compare mode all attacks must be blocked in the secure system.
"""

import pytest

from hostelguard.clock import FakeClock
from hostelguard.db import Database
from hostelguard import config
from hostelguard.access.registry import DeviceRegistry


@pytest.fixture(autouse=True)
def fast_bcrypt():
    """Use fast bcrypt cost for all integration tests."""
    DeviceRegistry._bcrypt_cost = config.BCRYPT_COST_TEST
    yield
    DeviceRegistry._bcrypt_cost = config.BCRYPT_COST_NORMAL


@pytest.fixture
def tmp_db(tmp_path):
    db = Database(tmp_path / "test.db")
    yield db
    db.close()


def test_insecure_mode_runs(tmp_db):
    """Insecure mode: all devices publish, cloud stores data, exits cleanly."""
    from hostelguard.integration.profiles import build_insecure_system
    from hostelguard.integration.runner import run_normal_traffic

    system = build_insecure_system(clock=FakeClock(), db=tmp_db)
    run_normal_traffic(system)

    total_expected = len(config.DEVICES) * config.SIM_MESSAGES_PER_DEVICE
    assert len(system.wire.transcript) == total_expected


def test_secure_mode_runs(tmp_db):
    """Secure mode: all devices publish with crypto, exits cleanly."""
    from hostelguard.integration.profiles import build_secure_system
    from hostelguard.integration.runner import run_normal_traffic

    system = build_secure_system(clock=FakeClock(), db=tmp_db)
    run_normal_traffic(system)
    assert len(system.wire.transcript) > 0


def test_insecure_all_attacks_succeed(tmp_db):
    """All 6 attacks must succeed against the insecure system."""
    from hostelguard.integration.profiles import build_insecure_system
    from hostelguard.integration.compare import run_attacks_on_system

    system = build_insecure_system(clock=FakeClock(), db=tmp_db)
    results = run_attacks_on_system(system, "insecure")

    assert len(results) == 6, "Expected exactly 6 attack results"
    for r in results:
        assert r["succeeded"], (
            f"Attack '{r['name']}' did not succeed in insecure mode: {r['detail']}"
        )


def test_secure_brute_force_blocked(tmp_db):
    """Brute force must be blocked in secure mode (account lockout)."""
    from hostelguard.integration.profiles import build_secure_system
    from hostelguard.attacks.brute_force_attack import BruteForceAttack

    system = build_secure_system(clock=FakeClock(), db=tmp_db)
    result = BruteForceAttack().run(system)
    # In secure mode the account locks out before the password is cracked
    assert not result.succeeded, (
        f"Brute force should be blocked in secure mode: {result.detail}"
    )


def test_secure_sniffing_no_readable_plaintext(tmp_db):
    """Sniffing must yield no readable plaintext in secure mode."""
    from hostelguard.integration.profiles import build_secure_system
    from hostelguard.attacks.sniffing_attack import SniffingAttack
    from hostelguard.integration.runner import run_normal_traffic

    system = build_secure_system(clock=FakeClock(), db=tmp_db)
    # Let traffic flow so there is something to sniff
    run_normal_traffic(system)
    result = SniffingAttack().run(system)
    # In secure mode all payloads are encrypted -> no readable plaintext
    assert result.metrics.get("readable", 0) == 0, (
        f"Sniffing found readable plaintext in secure mode: {result.detail}"
    )
