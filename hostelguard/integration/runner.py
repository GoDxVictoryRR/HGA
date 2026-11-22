"""
hostelguard/integration/runner.py
Normal-traffic demo runner used by main.py.

Runs a short simulation: each device publishes a few telemetry messages,
the broker routes them, and the cloud stores them.  Prints a summary table
to stdout using ASCII only.
"""

import logging

from hostelguard import config
from hostelguard.sim.interfaces import SystemContainer

logger = logging.getLogger(__name__)


def _get_device_token(system: SystemContainer, device_id: str) -> str:
    """Generate a JWT for a device in secure mode.

    In secure mode devices need a valid JWT to connect to the broker.
    We sign one using the system keystore's JWT secret directly (bypassing
    the cloud login which is for human users).
    """
    import jwt as _jwt
    from hostelguard import config as _cfg

    secret = system.keystore.get_jwt_secret()
    payload = {
        "sub": device_id,
        "role": _cfg.ROLE_DEVICE,
        "iat": int(system.clock.now()),
        "exp": int(system.clock.now()) + _cfg.TOKEN_LIFETIME_SECONDS,
    }
    return _jwt.encode(payload, secret, algorithm=_cfg.JWT_ALGORITHM)


def run_normal_traffic(system: SystemContainer) -> None:
    """Let all devices publish telemetry; log and print results.

    In insecure mode devices connect without tokens.
    In secure mode a JWT is issued for each device so the broker accepts them.
    """
    print(f"\n--- Normal Traffic Demo ({system.mode.upper()} mode) ---")

    # Connect all devices to the broker
    for device in system.devices:
        if system.mode == "secure" and system.keystore is not None:
            token = _get_device_token(system, device.device_id)
        else:
            token = None
        try:
            system.broker.connect(device.device_id, config.ROLE_DEVICE, token=token)
        except Exception as exc:
            logger.error("Could not connect device %s: %s", device.device_id, exc)

    # Each device publishes SIM_MESSAGES_PER_DEVICE messages
    total = 0
    errors = 0
    for device in system.devices:
        for _ in range(config.SIM_MESSAGES_PER_DEVICE):
            try:
                envelope = device.publish_telemetry()
                system.broker.publish(envelope)
                # Cloud stores the message
                system.cloud.ingest(envelope)
                total += 1
            except Exception as exc:
                logger.error("Error publishing from %s: %s", device.device_id, exc)
                errors += 1

    print(f"  Published {total} messages from {len(system.devices)} devices.")
    if errors:
        print(f"  Errors: {errors}")
    print(f"  Transcript length: {len(system.wire.transcript)} messages on wire.")
    print(f"  Mode: {system.mode}")
    print("--- End of normal traffic demo ---\n")
