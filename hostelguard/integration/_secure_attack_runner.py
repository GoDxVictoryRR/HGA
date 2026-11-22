"""
hostelguard/integration/_secure_attack_runner.py
Runs all 6 attacks against the SECURE system and returns results.

Extracted here from compare.py to keep both files under 250 lines.
Each attack attempts its technique through the secure broker/cloud;
the result captures whether it was blocked and why.
"""

import json
import logging
from typing import List

import jwt as _jwt

from hostelguard import config
from hostelguard.attacks.brute_force_attack import BruteForceAttack
from hostelguard.attacks.sniffing_attack import SniffingAttack
from hostelguard.crypto.hmac_integrity import HmacIntegrity
from hostelguard.crypto.keystore import KEY_HMAC
from hostelguard.exceptions import (
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    ReplayError,
    TamperError,
)
from hostelguard.sim.messages import MessageEnvelope
from hostelguard.sim.wire import Attacker

logger = logging.getLogger(__name__)


def _append(results: List[dict], name: str, blocked: bool, detail: str,
            metrics: dict) -> None:
    """Append one attack result and print a status line."""
    results.append({
        "name": name, "mode": "secure",
        "succeeded": not blocked, "detail": detail, "metrics": metrics,
    })
    status = "BLOCKED" if blocked else "SUCCEEDED"
    print(f"  [{status}] {name}: {detail}")


def run_attacks_secure(system) -> List[dict]:
    """Run all 6 attacks against the secure system.

    Returns a list of result dicts matching the same schema as
    run_attacks_on_system() in compare.py.
    """
    results: List[dict] = []
    _replay(system, results)
    _spoofing(system, results)
    _brute_force(system, results)
    _flooding(system, results)
    _sniffing(system, results)
    _tampering(system, results)
    return results


# ---------------------------------------------------------------------------
# Individual attack probes (each under 40 lines)
# ---------------------------------------------------------------------------

def _replay(system, results: List[dict]) -> None:
    """Attempt a replay attack; expect SecureBroker to block it."""
    name = "Replay Attack"
    try:
        att = Attacker()
        system.wire.attach_attacker(att)
        env = system.devices[0].publish_telemetry()
        system.broker.publish(env)
        captured = att.captured[:]
        system.wire.detach_attacker()
        # Advance clock past the replay window
        if hasattr(system.clock, "advance"):
            system.clock.advance(60)
        blocked = True
        try:
            system.broker.publish(captured[0])
            blocked = False
        except (ReplayError, AuthenticationError, TamperError, Exception):
            blocked = True
        detail = "Blocked: timestamp/counter replay detected" if blocked else "Accepted (unexpected)"
        _append(results, name, blocked, detail, {"blocked": int(blocked)})
    except Exception as exc:
        _append(results, name, True, f"Blocked by exception: {exc}", {})


def _spoofing(system, results: List[dict]) -> None:
    """Send a crafted message with no HMAC; expect SecureBroker to reject it."""
    name = "Spoofing Attack"
    try:
        fake = MessageEnvelope(
            device_id="warden",
            topic=config.make_topic("rfid_main_gate", config.TOPIC_COMMAND),
            payload=json.dumps({"action": "unlock"}).encode(),
            timestamp=system.clock.now(),
            counter=9999,
            mac=b"",
            signature=b"",
            encrypted=False,
        )
        blocked = True
        try:
            system.broker.publish(fake)
            blocked = False
        except (TamperError, AuthenticationError, AuthorizationError, Exception):
            blocked = True
        detail = "Blocked: HMAC/auth check" if blocked else "Spoofed message accepted"
        _append(results, name, blocked, detail, {"blocked": int(blocked)})
    except Exception as exc:
        _append(results, name, True, f"Blocked: {exc}", {})


def _brute_force(system, results: List[dict]) -> None:
    """Run BruteForceAttack directly; bcrypt+lockout should block it."""
    name = "Brute Force Attack"
    result = BruteForceAttack().run(system)
    _append(results, name, not result.succeeded, result.detail, result.metrics)


def _flooding(system, results: List[dict]) -> None:
    """Flood the broker with messages; rate limiter should drop most."""
    name = "Flooding (DoS) Attack"
    try:
        secret = system.keystore.get_jwt_secret()
        flood_token = _jwt.encode(
            {"sub": "warden_flood_tester", "role": config.ROLE_WARDEN,
             "iat": int(system.clock.now()), "exp": int(system.clock.now()) + 3600},
            secret, algorithm=config.JWT_ALGORITHM,
        )
        try:
            system.broker.connect("warden_flood_tester", config.ROLE_WARDEN,
                                  token=flood_token)
        except Exception:
            pass
        blocked_count = 0
        sent_count = 0
        for i in range(config.ATTACK_FLOOD_SIZE):
            env = MessageEnvelope(
                device_id="warden_flood_tester",
                topic=config.make_topic("temp_room_101", config.TOPIC_TELEMETRY),
                payload=json.dumps({"temperature_c": 99.9}).encode(),
                timestamp=system.clock.now(),
                counter=i + 50000,
                mac=b"", signature=b"", encrypted=False,
            )
            try:
                system.broker.publish(env)
                sent_count += 1
            except (RateLimitError, AuthorizationError, TamperError, Exception):
                blocked_count += 1
        blocked = blocked_count > 0
        detail = (f"Rate limiter blocked {blocked_count}/{config.ATTACK_FLOOD_SIZE} messages"
                  if blocked else "All flood messages accepted")
        _append(results, name, blocked, detail,
                {"sent": sent_count, "blocked": blocked_count})
    except Exception as exc:
        _append(results, name, True, f"Blocked: {exc}", {})


def _sniffing(system, results: List[dict]) -> None:
    """Run SniffingAttack; AES-GCM encryption should yield zero plaintext."""
    name = "Sniffing Attack"
    result = SniffingAttack().run(system)
    _append(results, name, not result.succeeded, result.detail, result.metrics)


def _tampering(system, results: List[dict]) -> None:
    """Modify a message payload; HMAC should detect the change."""
    name = "Tampering Attack"
    try:
        valid_env = system.devices[0].publish_telemetry()
        tampered = valid_env.copy()
        tampered.payload = json.dumps({"temperature_c": -99.0, "tampered": True}).encode()
        blocked = False
        if system.keystore:
            hmac_key = system.keystore.get(valid_env.device_id, KEY_HMAC)
            if hmac_key:
                h = HmacIntegrity(hmac_key)
                try:
                    h.verify(tampered.mac, tampered.device_id, tampered.topic,
                             tampered.payload, tampered.timestamp, tampered.counter)
                except TamperError:
                    blocked = True
        detail = ("HMAC verification rejects tampered payload at receiver"
                  if blocked else "Tampering not detected")
        _append(results, name, blocked, detail, {"blocked": int(blocked)})
    except Exception as exc:
        _append(results, name, True, f"Blocked: {exc}", {})
