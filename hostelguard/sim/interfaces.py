"""
hostelguard/sim/interfaces.py
Abstract base classes (interfaces) for every major component.

Each interface has exactly one insecure implementation (built in Phase 2) and
one secure implementation (built in Phases 3-5).  The profile factory in
integration/profiles.py assembles a System from either set of implementations.

No business logic lives here — only method signatures and docstrings.
"""

import abc
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from hostelguard.sim.messages import MessageEnvelope


# ---------------------------------------------------------------------------
# Attack result record
# ---------------------------------------------------------------------------

@dataclass
class AttackResult:
    """Record returned by every attack after it runs.

    Fields
    ------
    name      : human-readable attack name
    mode      : "insecure" or "secure"
    succeeded : True if the attack achieved its goal
    detail    : one-sentence explanation of what happened
    metrics   : arbitrary key-value data (packet counts, timing, etc.)
    """
    name: str
    mode: str
    succeeded: bool
    detail: str
    metrics: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Device interface
# ---------------------------------------------------------------------------

class DeviceBase(abc.ABC):
    """A simulated IoT device that can publish telemetry and receive commands."""

    @abc.abstractmethod
    def publish_telemetry(self) -> MessageEnvelope:
        """Create and return one telemetry message envelope.

        The caller (or the system) is responsible for putting it on the wire.
        """

    @abc.abstractmethod
    def receive_command(self, envelope: MessageEnvelope) -> None:
        """Process an incoming command envelope directed at this device."""

    @property
    @abc.abstractmethod
    def device_id(self) -> str:
        """Return the unique device identifier."""


# ---------------------------------------------------------------------------
# Broker interface
# ---------------------------------------------------------------------------

class BrokerBase(abc.ABC):
    """Message broker: routes messages between devices and the cloud."""

    @abc.abstractmethod
    def connect(self, client_id: str, role: str, token: Optional[str] = None) -> None:
        """Register a client with the broker.

        In insecure mode token is ignored.  In secure mode a valid JWT is
        required.
        """

    @abc.abstractmethod
    def publish(self, envelope: MessageEnvelope) -> None:
        """Accept a message from a client and route it to subscribers."""

    @abc.abstractmethod
    def subscribe(self, client_id: str, topic: str) -> None:
        """Subscribe client_id to messages on topic."""

    @abc.abstractmethod
    def disconnect(self, client_id: str) -> None:
        """Unregister a client from the broker."""


# ---------------------------------------------------------------------------
# Cloud service interface
# ---------------------------------------------------------------------------

class CloudServiceBase(abc.ABC):
    """Cloud back-end: stores telemetry, handles login, answers queries."""

    @abc.abstractmethod
    def ingest(self, envelope: MessageEnvelope) -> None:
        """Store one telemetry message in the cloud database."""

    @abc.abstractmethod
    def login(self, username: str, password: str) -> str:
        """Authenticate a user and return a session token (JWT)."""

    @abc.abstractmethod
    def query(self, token: str, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return records matching query_params for a logged-in user."""

    @abc.abstractmethod
    def admin(self, token: str, action: str, params: Dict[str, Any]) -> Any:
        """Perform an administrative action (device registration, etc.)."""


# ---------------------------------------------------------------------------
# Attack interface
# ---------------------------------------------------------------------------

class AttackBase(abc.ABC):
    """Base for all simulated attacks."""

    @abc.abstractmethod
    def run(self, system: "SystemContainer") -> AttackResult:
        """Execute the attack against the given system and return a result."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Return the attack's human-readable name."""


# ---------------------------------------------------------------------------
# System container
# ---------------------------------------------------------------------------

@dataclass
class SystemContainer:
    """Holds all components that make up one running simulation.

    The profile factory builds this for a given mode.  Attack and integration
    code receives the whole container so it can reach any component without
    global state.
    """
    # Injected dependencies
    wire: Any          # Wire instance
    broker: BrokerBase
    devices: List[DeviceBase]
    cloud: CloudServiceBase
    clock: Any         # Clock or FakeClock
    mode: str          # "insecure" or "secure"
    # Optional: filled in by later phases
    registry: Optional[Any] = None    # DeviceRegistry (Phase 3)
    keystore: Optional[Any] = None    # KeyStore (Phase 3)
    db: Optional[Any] = None          # Database (shared)
