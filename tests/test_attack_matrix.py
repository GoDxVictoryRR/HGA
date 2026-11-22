"""
tests/test_attack_matrix.py
Full 6-attack matrix verification against both insecure and secure modes.
"""

from hostelguard.attacks.replay_attack import ReplayAttack
from hostelguard.attacks.spoofing_attack import SpoofingAttack
from hostelguard.attacks.brute_force_attack import BruteForceAttack
from hostelguard.attacks.flooding_attack import FloodingAttack
from hostelguard.attacks.sniffing_attack import SniffingAttack
from hostelguard.attacks.tampering_attack import TamperingAttack
from hostelguard.integration._secure_attack_runner import run_attacks_secure


def test_insecure_attack_matrix(insecure_sys):
    """All 6 attacks must SUCCEED on the insecure system."""
    attacks = [
        ReplayAttack(),
        SpoofingAttack(),
        BruteForceAttack(),
        FloodingAttack(),
        SniffingAttack(),
        TamperingAttack(),
    ]
    for attack in attacks:
        res = attack.run(insecure_sys)
        assert res.succeeded, f"Attack {attack.name} failed on insecure: {res.detail}"


def test_secure_attack_matrix(secure_sys):
    """All 6 attacks must be BLOCKED on the secure system."""
    from hostelguard.integration.runner import run_normal_traffic
    run_normal_traffic(secure_sys)
    results = run_attacks_secure(secure_sys)
    assert len(results) == 6
    for res in results:
        assert not res["succeeded"], (
            f"Attack {res['name']} unexpectedly succeeded on secure system: {res['detail']}"
        )
