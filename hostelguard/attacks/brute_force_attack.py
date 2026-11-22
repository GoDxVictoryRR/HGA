"""
hostelguard/attacks/brute_force_attack.py
Simulated brute-force password attack against the cloud login.

The attacker tries a list of common passwords against a known username.
Against the insecure cloud service, passwords are stored and compared in
plaintext, and there is no lockout, so the attack eventually succeeds.

This module is educational only and operates entirely in-process.
"""

import logging

from hostelguard.sim.interfaces import AttackBase, AttackResult, SystemContainer
from hostelguard import config

logger = logging.getLogger(__name__)

# A short list of common passwords to try (kept minimal and educational)
COMMON_PASSWORDS = [
    "password", "123456", "admin", "hostel", "warden",
    "warden123",   # the actual insecure password
    "12345678", "qwerty", "letmein", "welcome",
    "pass", "test", "iot", "secure", "hostelguard",
    "student", "tech1pass", "stu1pass", "root", "default",
]


class BruteForceAttack(AttackBase):
    """Try a list of passwords against the cloud login endpoint."""

    @property
    def name(self) -> str:
        return "Brute Force Attack"

    def run(self, system: SystemContainer) -> AttackResult:
        """Attempt to log in as 'warden' using a password list."""
        target_user = "warden"
        attempts = 0
        cracked_password = None

        for password in COMMON_PASSWORDS[:config.ATTACK_BRUTE_FORCE_GUESSES]:
            attempts += 1
            try:
                system.cloud.login(target_user, password)
                cracked_password = password
                logger.warning(
                    "Brute force: cracked %s with password '%s' after %d attempts",
                    target_user, password, attempts,
                )
                break
            except Exception:
                # Login failed — try the next password
                pass

        succeeded = cracked_password is not None
        return AttackResult(
            name=self.name,
            mode=system.mode,
            succeeded=succeeded,
            detail=(
                f"Password '{cracked_password}' found after {attempts} attempts (no lockout)"
                if succeeded
                else f"Failed after {attempts} attempts"
            ),
            metrics={
                "attempts": attempts,
                "cracked": int(succeeded),
                "password": cracked_password or "",
            },
        )
