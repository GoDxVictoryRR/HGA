"""
hostelguard/sim/insecure_broker.py
Intentionally insecure MQTT-style broker.

*** THIS MODULE IS INTENTIONALLY INSECURE AND FOR SIMULATION ONLY ***
*** Do not use this code in any real system. ***

The insecure broker:
- Accepts any client without authentication.
- Does no authorization check on topics.
- Routes messages to all matching subscribers with no validation.
- Stores every message in a simple in-memory log.
"""

import logging
from typing import Dict, List, Optional

from hostelguard.sim.interfaces import BrokerBase
from hostelguard.sim.messages import MessageEnvelope
from hostelguard.sim.wire import Wire

logger = logging.getLogger(__name__)


class InsecureBroker(BrokerBase):
    """MQTT-style broker with no authentication or authorization."""

    def __init__(self, wire: Wire) -> None:
        self._wire = wire
        # Set of connected client IDs (no credentials checked)
        self._clients: Dict[str, str] = {}  # client_id -> role
        # topic -> list of (client_id, callback)
        self._subscriptions: Dict[str, List[tuple]] = {}
        # In-memory log of all ingested messages
        self.message_log: List[MessageEnvelope] = []

    def connect(self, client_id: str, role: str, token: Optional[str] = None) -> None:
        """Accept any connection without checking credentials."""
        self._clients[client_id] = role
        logger.info("Broker: client %s connected as %s (no auth check)", client_id, role)

    def publish(self, envelope: MessageEnvelope) -> None:
        """Accept and route the message with no validation."""
        self.message_log.append(envelope.copy())
        self._wire.publish(envelope)
        logger.debug("Broker routed: %s -> %s", envelope.device_id, envelope.topic)

    def subscribe(self, client_id: str, topic: str) -> None:
        """Subscribe client to topic with no authorization check."""
        if topic not in self._subscriptions:
            self._subscriptions[topic] = []
        self._subscriptions[topic].append(client_id)
        # Register on the wire so messages reach the subscriber
        logger.debug("Broker: %s subscribed to %s (no authz check)", client_id, topic)

    def disconnect(self, client_id: str) -> None:
        """Remove a client."""
        self._clients.pop(client_id, None)
        logger.info("Broker: client %s disconnected", client_id)
