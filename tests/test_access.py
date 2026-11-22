"""
tests/test_access.py
Tests for Module 3: registry, RBAC, secure broker, secure cloud.
"""

import pytest

from hostelguard import config
from hostelguard.clock import FakeClock
from hostelguard.crypto.keystore import KeyStore
from hostelguard.db import Database
from hostelguard.exceptions import (
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    RegistrationError,
)
from hostelguard.access import rbac
from hostelguard.access.registry import DeviceRegistry


@pytest.fixture
def db(tmp_path):
    d = Database(tmp_path / "test.db")
    yield d
    d.close()


@pytest.fixture
def keystore(tmp_path):
    return KeyStore(tmp_path / "ks.json")


@pytest.fixture
def registry(db, keystore):
    # Use fast bcrypt for tests
    DeviceRegistry._bcrypt_cost = config.BCRYPT_COST_TEST
    return DeviceRegistry(db, keystore)


# ---------------------------------------------------------------------------
# DeviceRegistry
# ---------------------------------------------------------------------------

def test_registry_default_users_exist(registry):
    users = registry.list_users()
    names = [u["username"] for u in users]
    assert "warden" in names


def test_registry_authenticate_warden(registry):
    role = registry.authenticate_user("warden", "warden123")
    assert role == config.ROLE_WARDEN


def test_registry_wrong_password_raises(registry):
    with pytest.raises(AuthenticationError):
        registry.authenticate_user("warden", "wrongpassword")


def test_registry_revoke_user_blocks_login(registry):
    registry.revoke_user("tech1")
    with pytest.raises(AuthenticationError):
        registry.authenticate_user("tech1", "tech1pass")


def test_registry_register_and_revoke_device(registry):
    registry.register_device("test_device", "motion_sensor", "lobby")
    assert registry.is_device_registered("test_device")
    registry.revoke_device("test_device")
    assert not registry.is_device_registered("test_device")


def test_registry_duplicate_registration_raises(registry):
    with pytest.raises(RegistrationError):
        registry.register_device("rfid_main_gate", "rfid_door_lock", "gate")


def test_registry_bcrypt_hash_not_plaintext(registry, db):
    row = db.fetchone(
        "SELECT password_hash FROM registered_users WHERE username = 'warden'"
    )
    assert row is not None
    # bcrypt hashes start with $2b$
    assert row["password_hash"].startswith("$2b$")


# ---------------------------------------------------------------------------
# RBAC
# ---------------------------------------------------------------------------

def test_rbac_warden_can_publish_anything():
    assert rbac.can_publish(config.ROLE_WARDEN, "warden", "rfid_main_gate/command")
    assert rbac.can_publish(config.ROLE_WARDEN, "warden", "temp_room_101/telemetry")


def test_rbac_device_can_only_publish_own_telemetry():
    assert rbac.can_publish(config.ROLE_DEVICE, "rfid_main_gate", "rfid_main_gate/telemetry")
    assert not rbac.can_publish(config.ROLE_DEVICE, "rfid_main_gate", "rfid_warden_room/telemetry")
    assert not rbac.can_publish(config.ROLE_DEVICE, "rfid_main_gate", "rfid_main_gate/command")


def test_rbac_student_cannot_publish():
    assert not rbac.can_publish(config.ROLE_STUDENT, "student1", "temp_room_101/telemetry")


def test_rbac_student_can_subscribe_temperature_only():
    assert rbac.can_subscribe(config.ROLE_STUDENT, "student1", "temp_room_101/telemetry")
    assert not rbac.can_subscribe(config.ROLE_STUDENT, "student1", "rfid_main_gate/telemetry")


def test_rbac_warden_can_send_commands():
    assert rbac.can_send_command(config.ROLE_WARDEN, "rfid_main_gate", "unlock")


def test_rbac_technician_cannot_unlock():
    assert not rbac.can_send_command(config.ROLE_TECHNICIAN, "rfid_main_gate", "unlock")


def test_rbac_check_publish_raises_for_student():
    with pytest.raises(AuthorizationError):
        rbac.check_publish(config.ROLE_STUDENT, "student1", "rfid_main_gate/command")


def test_rbac_check_admin_raises_for_student():
    with pytest.raises(AuthorizationError):
        rbac.check_admin(config.ROLE_STUDENT)


# ---------------------------------------------------------------------------
# SecureBroker
# ---------------------------------------------------------------------------

@pytest.fixture
def secure_system(tmp_path):
    from hostelguard.integration.profiles import build_secure_system
    DeviceRegistry._bcrypt_cost = config.BCRYPT_COST_TEST
    db = Database(tmp_path / "test.db")
    clock = FakeClock()
    system = build_secure_system(clock=clock, db=db)
    yield system
    db.close()


def test_secure_broker_requires_token(secure_system):
    broker = secure_system.broker
    with pytest.raises(AuthenticationError):
        broker.connect("rfid_main_gate", config.ROLE_DEVICE, token=None)


def test_secure_broker_accepts_valid_token(secure_system):
    cloud = secure_system.cloud
    # Login as warden to get a token
    token = cloud.login("warden", "warden123")
    # Warden connects to broker — should not raise
    secure_system.broker.connect("warden", config.ROLE_WARDEN, token=token)


def test_secure_broker_rejects_rate_limit(secure_system):
    """Flooding should trigger rate limit."""
    from hostelguard.sim.messages import MessageEnvelope

    cloud = secure_system.cloud
    token = cloud.login("warden", "warden123")
    secure_system.broker.connect("warden", config.ROLE_WARDEN, token=token)

    # Push messages beyond the burst limit
    with pytest.raises(RateLimitError):
        for i in range(config.RATE_LIMIT_BURST + 5):
            env = MessageEnvelope(
                device_id="warden",
                topic="rfid_main_gate/command",
                payload=b"cmd",
                timestamp=secure_system.clock.now(),
                counter=i + 1000,
                mac=b"",
            )
            secure_system.broker.publish(env)


# ---------------------------------------------------------------------------
# SecureCloudService
# ---------------------------------------------------------------------------

def test_secure_cloud_login_returns_jwt(secure_system):
    token = secure_system.cloud.login("warden", "warden123")
    # JWT has 3 parts separated by dots
    assert token.count(".") == 2


def test_secure_cloud_bad_password_raises(secure_system):
    with pytest.raises(AuthenticationError):
        secure_system.cloud.login("warden", "wrongpassword")


def test_secure_cloud_lockout_after_failures(secure_system):
    """Account should be locked after LOCKOUT_THRESHOLD bad attempts."""
    for _ in range(config.LOCKOUT_THRESHOLD):
        try:
            secure_system.cloud.login("warden", "badpass")
        except AuthenticationError:
            pass
    with pytest.raises(AuthenticationError, match="locked"):
        secure_system.cloud.login("warden", "warden123")


def test_secure_cloud_query_requires_valid_token(secure_system):
    with pytest.raises(AuthenticationError):
        secure_system.cloud.query("not_a_real_token", {})


def test_secure_cloud_student_cannot_query_rfid(secure_system):
    token = secure_system.cloud.login("student1", "stu1pass")
    with pytest.raises(AuthorizationError):
        secure_system.cloud.query(token, {"device_id": "rfid_main_gate"})


def test_secure_cloud_admin_requires_warden(secure_system):
    tech_token = secure_system.cloud.login("tech1", "tech1pass")
    with pytest.raises(AuthorizationError):
        secure_system.cloud.admin(tech_token, "list_users", {})


def test_secure_cloud_warden_can_get_audit_log(secure_system):
    token = secure_system.cloud.login("warden", "warden123")
    log = secure_system.cloud.admin(token, "get_audit_log", {})
    assert isinstance(log, list)
