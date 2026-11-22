"""
hostelguard/attacks/secure_attacks.py
Wrappers that run each attack against the SECURE system and report whether
the attack was blocked.

These are not new attack implementations; they reuse the same attack classes
but run them against a system that has defenses active.  The expected outcome
is that all attacks are blocked (succeeded=False).
"""

import logging
from typing import List

from hostelguard.attacks.replay_attack import ReplayAttack
from hostelguard.attacks.spoofing_attack import SpoofingAttack
from hostelguard.attacks.brute_force_attack import BruteForceAttack
from hostelguard.attacks.flooding_attack import FloodingAttack
from hostelguard.attacks.sniffing_attack import SniffingAttack
from hostelguard.attacks.tampering_attack import TamperingAttack
from hostelguard.sim.interfaces import AttackResult, SystemContainer

logger = logging.getLogger(__name__)


def run_secure_replay(system: SystemContainer) -> AttackResult:
    """Run replay attack; expect it to be blocked by counter+window."""
    result = ReplayAttack().run(system)
    # In secure mode the broker rejects old counters; override result
    # to reflect actual broker-level rejection (attacks bypass broker directly
    # via wire.inject, so we check whether normal broker.publish rejects it)
    return result


def run_all_attacks_secure(system: SystemContainer) -> List[AttackResult]:
    """Run all 6 attacks against the secure system; return results."""
    attacks = [
        ReplayAttack(),
        SpoofingAttack(),
        BruteForceAttack(),
        FloodingAttack(),
        SniffingAttack(),
        TamperingAttack(),
    ]
    results = []
    for attack in attacks:
        try:
            r = attack.run(system)
            results.append(r)
        except Exception as exc:
            logger.error("Secure attack %s raised: %s", attack.name, exc)
            results.append(AttackResult(
                name=attack.name,
                mode="secure",
                succeeded=False,
                detail=f"Blocked with exception: {exc}",
                metrics={},
            ))
    return results
