"""
tests/test_attacks.py
Tests for Module 1: insecure baseline, all six attacks succeed.
"""

import pytest

from hostelguard.clock import FakeClock
from hostelguard.integration.profiles import build_insecure_system
from hostelguard.attacks.replay_attack import ReplayAttack
from hostelguard.attacks.spoofing_attack import SpoofingAttack
from hostelguard.attacks.brute_force_attack import BruteForceAttack
from hostelguard.attacks.flooding_attack import FloodingAttack
from hostelguard.attacks.sniffing_attack import SniffingAttack
from hostelguard.attacks.tampering_attack import TamperingAttack


@pytest.fixture
def insecure_system(tmp_path):
    """Build a fresh insecure system backed by a temp database."""
    from hostelguard.db import Database
    db = Database(tmp_path / "test.db")
    clock = FakeClock()
    system = build_insecure_system(clock=clock, db=db)
    yield system
    db.close()


def test_replay_attack_succeeds(insecure_system):
    result = ReplayAttack().run(insecure_system)
    assert result.succeeded, f"Expected replay to succeed in insecure mode: {result.detail}"
    assert result.mode == "insecure"


def test_spoofing_attack_succeeds(insecure_system):
    result = SpoofingAttack().run(insecure_system)
    assert result.succeeded, f"Expected spoofing to succeed in insecure mode: {result.detail}"


def test_brute_force_attack_succeeds(insecure_system):
    result = BruteForceAttack().run(insecure_system)
    assert result.succeeded, f"Expected brute force to succeed in insecure mode: {result.detail}"
    assert result.metrics.get("cracked") == 1


def test_flooding_attack_succeeds(insecure_system):
    result = FloodingAttack().run(insecure_system)
    assert result.succeeded, f"Expected flooding to succeed in insecure mode: {result.detail}"
    from hostelguard import config
    assert result.metrics.get("injected") == config.ATTACK_FLOOD_SIZE


def test_sniffing_attack_succeeds(insecure_system):
    result = SniffingAttack().run(insecure_system)
    assert result.succeeded, f"Expected sniffing to succeed in insecure mode: {result.detail}"
    assert result.metrics.get("readable", 0) > 0


def test_tampering_attack_succeeds(insecure_system):
    result = TamperingAttack().run(insecure_system)
    assert result.succeeded, f"Expected tampering to succeed in insecure mode: {result.detail}"


def test_all_six_attacks_succeed(insecure_system):
    """Gate test: all six attacks must succeed against insecure system."""
    attacks = [
        ReplayAttack(),
        SpoofingAttack(),
        BruteForceAttack(),
        FloodingAttack(),
        SniffingAttack(),
        TamperingAttack(),
    ]
    for attack in attacks:
        result = attack.run(insecure_system)
        assert result.succeeded, (
            f"Attack '{attack.name}' did not succeed in insecure mode: {result.detail}"
        )
