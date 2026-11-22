"""
hostelguard/sim/wire.py
Simulated network wire for the HostelGuard project.

The wire carries messages as bytes between devices and the broker.  It records
a transcript of every message so the demo and attack modules can inspect
traffic.

An Attacker object can be attached to the wire.  The attacker has four
abilities that are used by the attack modules:
  - sniff     : read the transcript (passive, no modification)
  - tamper    : modify or drop a message currently in flight
  - inject    : push a new crafted message onto the wire (spoof / flood)
  - replay    : re-inject a previously captured message

None of these abilities open real sockets or touch the host network.
"""

import logging
from typing import Callable, List, Optional

from hostelguard.sim.messages import MessageEnvelope

logger = logging.getLogger(__name__)


class Attacker:
    """Represents an adversary attached to the wire.

    The wire calls on_message() for every message that passes through.
    The attacker may:
      - return None to drop the message
      - return a modified envelope to tamper with it
      - call wire.inject() to send additional messages (spoof / flood)

    The transcript of all messages seen by the attacker is stored in
    self.captured so attack modules can replay them later.
    """

    def __init__(self) -> None:
        # List of envelopes captured by this attacker (sniff ability)
        self.captured: List[MessageEnvelope] = []
        # Optional callback: receives the envelope, returns envelope or None
        self._tamper_fn: Optional[Callable[[MessageEnvelope], Optional[MessageEnvelope]]] = None

    def set_tamper_fn(
        self,
        fn: Callable[[MessageEnvelope], Optional[MessageEnvelope]],
    ) -> None:
        """Register a function that may modify or drop messages in flight.

        fn(envelope) -> envelope | None
          Return None to drop the message.
          Return a (possibly modified) envelope to let it through.
        """
        self._tamper_fn = fn

    def on_message(
        self,
        envelope: MessageEnvelope,
        wire: "Wire",
    ) -> Optional[MessageEnvelope]:
        """Called by the wire for each message.  Returns the final envelope."""
        # Always record for the sniff ability
        self.captured.append(envelope.copy())
        if self._tamper_fn is not None:
            result = self._tamper_fn(envelope)
            return result
        return envelope


class Wire:
    """Simulated network.  Messages travel as MessageEnvelope objects.

    Subscribers register callbacks for a topic prefix.  When a message is
    published, the wire records it, runs it through any attached attacker,
    then delivers it to all matching subscribers.
    """

    def __init__(self) -> None:
        # Full ordered list of all messages that passed through (or were injected)
        self.transcript: List[MessageEnvelope] = []
        # topic -> list of callback functions
        self._subscribers: dict = {}
        # Optional attacker; None means no adversary
        self._attacker: Optional[Attacker] = None

    def attach_attacker(self, attacker: Attacker) -> None:
        """Attach an adversary that can observe and modify traffic."""
        self._attacker = attacker
        logger.warning("Attacker attached to wire")

    def detach_attacker(self) -> None:
        """Remove the attacker."""
        self._attacker = None

    def subscribe(self, topic: str, callback: Callable[[MessageEnvelope], None]) -> None:
        """Register callback to receive messages published to topic."""
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(callback)

    def publish(self, envelope: MessageEnvelope) -> bool:
        """Put a message on the wire.

        Returns True if the message was delivered (not dropped by the attacker).
        """
        # Record raw message
        self.transcript.append(envelope.copy())

        # Run through attacker if one is attached
        final_envelope = envelope
        if self._attacker is not None:
            final_envelope = self._attacker.on_message(envelope, self)
            if final_envelope is None:
                logger.debug("Attacker dropped message from %s", envelope.device_id)
                return False

        # Deliver to subscribers
        self._deliver(final_envelope)
        return True

    def inject(self, envelope: MessageEnvelope) -> None:
        """Directly inject a message, bypassing normal attacker processing.

        Used by the attacker to spoof, replay, or flood the wire.
        The injected message is recorded in the transcript.
        """
        self.transcript.append(envelope.copy())
        self._deliver(envelope)
        logger.debug("Injected message: topic=%s device=%s", envelope.topic, envelope.device_id)

    def _deliver(self, envelope: MessageEnvelope) -> None:
        """Deliver an envelope to all matching subscribers."""
        delivered = False
        for topic, callbacks in self._subscribers.items():
            if envelope.topic == topic or envelope.topic.startswith(topic):
                for cb in callbacks:
                    cb(envelope)
                delivered = True
        if not delivered:
            logger.debug("No subscriber for topic %s", envelope.topic)

    def clear_transcript(self) -> None:
        """Clear the message log (called between test runs)."""
        self.transcript.clear()
        if self._attacker is not None:
            self._attacker.captured.clear()
