"""
tests/test_scaffold.py
Phase 1 gate tests: config, clock, database, envelope round-trip, wire.
"""

import pytest

from hostelguard import config
from hostelguard.clock import Clock, FakeClock
from hostelguard.db import Database
from hostelguard.sim.messages import MessageEnvelope
from hostelguard.sim.wire import Wire, Attacker


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def test_config_has_eight_devices():
    assert len(config.DEVICES) == 8


def test_config_devices_have_required_fields():
    for d in config.DEVICES:
        assert "id" in d
        assert "type" in d
        assert "location" in d


def test_config_device_types_cover_four_types():
    types = {d["type"] for d in config.DEVICES}
    assert len(types) == 4


def test_config_roles_defined():
    assert config.ROLE_WARDEN == "warden"
    assert config.ROLE_TECHNICIAN == "technician"
    assert config.ROLE_STUDENT == "student"
    assert config.ROLE_DEVICE == "device"


def test_config_make_topic():
    topic = config.make_topic("rfid_main_gate", "telemetry")
    assert topic == "rfid_main_gate/telemetry"


# ---------------------------------------------------------------------------
# Clock
# ---------------------------------------------------------------------------

def test_real_clock_returns_float():
    clock = Clock()
    t = clock.now()
    assert isinstance(t, float)
    assert t > 0


def test_fake_clock_starts_at_given_value():
    fc = FakeClock(start=1_000_000.0)
    assert fc.now() == 1_000_000.0


def test_fake_clock_advance():
    fc = FakeClock(start=0.0)
    fc.advance(30)
    assert fc.now() == 30.0


def test_fake_clock_set():
    fc = FakeClock()
    fc.set(999.0)
    assert fc.now() == 999.0


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def test_database_creates_file(tmp_path):
    db_path = tmp_path / "test.db"
    db = Database(db_path)
    assert db_path.exists()
    db.close()


def test_database_execute_and_fetchall(tmp_path):
    db = Database(tmp_path / "test.db")
    db.execute("CREATE TABLE t (val TEXT)")
    db.execute("INSERT INTO t VALUES (?)", ("hello",))
    rows = db.fetchall("SELECT val FROM t")
    assert len(rows) == 1
    assert rows[0]["val"] == "hello"
    db.close()


def test_database_reset_clears_data(tmp_path):
    db = Database(tmp_path / "test.db")
    db.execute("CREATE TABLE t (val TEXT)")
    db.execute("INSERT INTO t VALUES (?)", ("hello",))
    db.reset()
    db.execute("CREATE TABLE t (val TEXT)")
    rows = db.fetchall("SELECT val FROM t")
    assert len(rows) == 0
    db.close()


def test_database_parameterized_no_injection(tmp_path):
    """Parameterised query must not allow SQL injection."""
    db = Database(tmp_path / "test.db")
    db.execute("CREATE TABLE users (name TEXT)")
    db.execute("INSERT INTO users VALUES (?)", ("Alice",))
    # Attempt injection via parameter — should be treated as literal string
    rows = db.fetchall(
        "SELECT name FROM users WHERE name = ?",
        ("Alice' OR '1'='1",),
    )
    assert len(rows) == 0  # No rows, injection did not work
    db.close()


# ---------------------------------------------------------------------------
# MessageEnvelope round-trip
# ---------------------------------------------------------------------------

def test_envelope_round_trip():
    env = MessageEnvelope(
        device_id="rfid_main_gate",
        topic="rfid_main_gate/telemetry",
        payload=b'{"status":"locked"}',
        timestamp=12345.678,
        counter=42,
        nonce=b"\x01\x02\x03",
        mac=b"\xAA\xBB",
        signature=b"\xCC\xDD\xEE",
        encrypted=False,
    )
    data = env.to_bytes()
    restored = MessageEnvelope.from_bytes(data)
    assert restored.device_id == env.device_id
    assert restored.topic == env.topic
    assert restored.payload == env.payload
    assert restored.timestamp == pytest.approx(env.timestamp)
    assert restored.counter == env.counter
    assert restored.nonce == env.nonce
    assert restored.mac == env.mac
    assert restored.signature == env.signature
    assert restored.encrypted == env.encrypted


def test_envelope_copy_is_independent():
    env = MessageEnvelope(
        device_id="d1", topic="d1/telemetry", payload=b"data",
        timestamp=1.0, counter=1,
    )
    copy = env.copy()
    copy.payload = b"changed"
    assert env.payload == b"data"


# ---------------------------------------------------------------------------
# Wire
# ---------------------------------------------------------------------------

def test_wire_records_transcript():
    wire = Wire()
    env = MessageEnvelope("d1", "d1/telemetry", b"test", 1.0)
    wire.publish(env)
    assert len(wire.transcript) == 1


def test_wire_delivers_to_subscriber():
    wire = Wire()
    received = []
    wire.subscribe("d1/telemetry", lambda e: received.append(e))
    env = MessageEnvelope("d1", "d1/telemetry", b"test", 1.0)
    wire.publish(env)
    assert len(received) == 1


def test_wire_attacker_can_drop_message():
    wire = Wire()
    received = []
    wire.subscribe("d1/telemetry", lambda e: received.append(e))

    attacker = Attacker()
    attacker.set_tamper_fn(lambda e: None)  # drop all
    wire.attach_attacker(attacker)

    env = MessageEnvelope("d1", "d1/telemetry", b"test", 1.0)
    delivered = wire.publish(env)
    assert not delivered
    assert len(received) == 0


def test_wire_attacker_can_modify_payload():
    wire = Wire()
    received = []
    wire.subscribe("d1/telemetry", lambda e: received.append(e))

    def _tamper(env):
        mod = env.copy()
        mod.payload = b"tampered"
        return mod

    attacker = Attacker()
    attacker.set_tamper_fn(_tamper)
    wire.attach_attacker(attacker)

    env = MessageEnvelope("d1", "d1/telemetry", b"original", 1.0)
    wire.publish(env)
    assert received[0].payload == b"tampered"


def test_wire_attacker_captures_messages():
    wire = Wire()
    attacker = Attacker()
    wire.attach_attacker(attacker)
    env = MessageEnvelope("d1", "d1/telemetry", b"secret", 1.0)
    wire.publish(env)
    assert len(attacker.captured) == 1
    assert attacker.captured[0].payload == b"secret"


def test_wire_inject():
    wire = Wire()
    received = []
    wire.subscribe("d1/telemetry", lambda e: received.append(e))
    env = MessageEnvelope("attacker", "d1/telemetry", b"injected", 1.0)
    wire.inject(env)
    assert len(received) == 1
    assert received[0].payload == b"injected"


def test_wire_clear_transcript():
    wire = Wire()
    env = MessageEnvelope("d1", "d1/telemetry", b"test", 1.0)
    wire.publish(env)
    wire.clear_transcript()
    assert len(wire.transcript) == 0
