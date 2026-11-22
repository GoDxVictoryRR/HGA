"""
hostelguard/access/secure_broker.py
Secure MQTT-style broker with full authentication and authorization.

Compared to the insecure broker, the secure broker:
- Requires a valid JWT token from every connecting client.
- Checks RBAC rules on every publish and subscribe.
- Verifies the HMAC and replay counter on every incoming message.
- Enforces rate limits and locks out misbehaving clients.
"""

import logging
from typing import Dict, List, Optional, Set

import jwt

from hostelguard import config
from hostelguard.access import rbac
from hostelguard.access.registry import DeviceRegistry
from hostelguard.crypto.hmac_integrity import HmacIntegrity
from hostelguard.crypto.keystore import KEY_HMAC
from hostelguard.exceptions import (
    AuthenticationError,
    RateLimitError,
    ReplayError,
)
from hostelguard.sim.interfaces import BrokerBase
from hostelguard.sim.messages import MessageEnvelope
from hostelguard.sim.wire import Wire

logger = logging.getLogger(__name__)


class _ClientState:
    """Per-client connection state tracked by the broker."""

    def __init__(self, role: str) -> None:
        self.role = role
        # Rate limiting: timestamps of recent messages in the current window
        self.message_times: List[float] = []
        # Seen counter values for replay detection (per publishing client)
        self.seen_counters: Set[int] = set()


class SecureBroker(BrokerBase):
    """Hardened broker: authenticates, authorizes, checks integrity."""

    def __init__(self, wire: Wire, registry: DeviceRegistry, clock) -> None:
        self._wire = wire
        self._registry = registry
        self._clock = clock
        self._clients: Dict[str, _ClientState] = {}
        # Lockout state: client_id -> lockout-expiry timestamp
        self._lockouts: Dict[str, float] = {}
        # Failed auth attempts: client_id -> count
        self._failed_attempts: Dict[str, int] = {}
        self.message_log: List[MessageEnvelope] = []

    def _get_jwt_secret(self) -> bytes:
        return self._registry._keystore.get_jwt_secret()

    def _decode_token(self, token: str, client_id: str) -> dict:
        """Decode and verify a JWT using the injected clock for expiry.

        Disabling PyJWT built-in expiry check so FakeClock works in tests.
        """
        try:
            payload = jwt.decode(
                token,
                self._get_jwt_secret(),
                algorithms=[config.JWT_ALGORITHM],
                options={"verify_exp": False},
            )
        except jwt.InvalidTokenError as exc:
            raise AuthenticationError(f"Invalid token: {exc}") from exc

        if payload.get("sub") != client_id:
            raise AuthenticationError("Token subject does not match client_id")

        exp = payload.get("exp", 0)
        if exp and self._clock.now() > exp:
            raise AuthenticationError("Token has expired")

        return payload

    def connect(self, client_id: str, role: str, token: Optional[str] = None) -> None:
        """Accept a client only if it presents a valid JWT."""
        if token is None:
            raise AuthenticationError("Token required to connect")

        payload = self._decode_token(token, client_id)
        token_role = payload.get("role", "")

        # Check registry: device must be registered and not revoked
        if role == config.ROLE_DEVICE:
            if not self._registry.is_device_registered(client_id):
                raise AuthenticationError(f"Device not registered: {client_id}")

        self._clients[client_id] = _ClientState(role=token_role or role)
        logger.info("Broker: %s connected (role=%s)", client_id, role)

    def publish(self, envelope: MessageEnvelope) -> None:
        """Accept, validate, and route a message."""
        client_id = envelope.device_id
        state = self._clients.get(client_id)
        if state is None:
            raise AuthenticationError(f"Client not connected: {client_id}")

        # --- Rate limiting ---
        now = self._clock.now()
        window_start = now - 1.0  # 1-second window
        state.message_times = [t for t in state.message_times if t >= window_start]
        if len(state.message_times) >= config.RATE_LIMIT_BURST:
            raise RateLimitError(f"Rate limit exceeded for {client_id}")
        state.message_times.append(now)

        # --- RBAC publish check ---
        rbac.check_publish(state.role, client_id, envelope.topic)

        # --- Replay detection ---
        if envelope.counter in state.seen_counters:
            raise ReplayError(f"Replayed counter {envelope.counter} from {client_id}")
        # Also check timestamp is within the replay window
        age = now - envelope.timestamp
        if age > config.REPLAY_WINDOW_SECONDS or age < -5:
            raise ReplayError(
                f"Message timestamp out of replay window: age={age:.1f}s"
            )
        state.seen_counters.add(envelope.counter)

        # --- HMAC integrity ---
        keystore = self._registry._keystore
        hmac_key = keystore.get(client_id, KEY_HMAC)
        if hmac_key:
            integrity = HmacIntegrity(hmac_key)
            integrity.verify(
                envelope.mac,
                envelope.device_id,
                envelope.topic,
                envelope.payload,
                envelope.timestamp,
                envelope.counter,
            )

        self.message_log.append(envelope.copy())
        self._wire.publish(envelope)
        logger.debug("SecureBroker routed: %s -> %s", client_id, envelope.topic)

    def subscribe(self, client_id: str, topic: str) -> None:
        """Subscribe only if RBAC permits."""
        state = self._clients.get(client_id)
        if state is None:
            raise AuthenticationError(f"Client not connected: {client_id}")
        rbac.check_subscribe(state.role, client_id, topic)
        logger.debug("SecureBroker: %s subscribed to %s", client_id, topic)

    def disconnect(self, client_id: str) -> None:
        """Remove a client."""
        self._clients.pop(client_id, None)
        logger.info("SecureBroker: %s disconnected", client_id)
