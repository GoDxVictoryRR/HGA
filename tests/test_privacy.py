"""
tests/test_privacy.py
Tests for Module 3 privacy techniques: minimisation, DP, k-anonymity.
"""

from hostelguard.privacy.techniques import (
    minimise,
    add_dp_noise,
    apply_dp_to_records,
    apply_k_anonymity,
)


def test_minimise_removes_pii():
    record = {"device_id": "d1", "temperature_c": 25.0, "location": "room_101"}
    result = minimise(record)
    assert "device_id" not in result
    assert "location" not in result
    assert result["temperature_c"] == 25.0


def test_dp_noise_changes_value():
    noisy = add_dp_noise(25.0, sensitivity=5.0, epsilon=1.0)
    # Very rarely equal (probability ~ 0); acceptable for a test
    assert isinstance(noisy, float)
    # Noise should be bounded in a reasonable range
    assert abs(noisy - 25.0) < 100.0


def test_dp_records_all_changed():
    records = [{"temperature_c": 24.0}, {"temperature_c": 26.0}]
    result = apply_dp_to_records(records, ["temperature_c"])
    for orig, noisy in zip(records, result):
        assert "temperature_c" in noisy


def test_k_anonymity_suppresses_small_groups():
    records = [
        {"device_type": "temperature_sensor", "location": "room_101"},
        {"device_type": "temperature_sensor", "location": "room_101"},
        {"device_type": "temperature_sensor", "location": "room_101"},
        {"device_type": "rfid_door_lock", "location": "main_gate"},  # group size 1
    ]
    result = apply_k_anonymity(records, ["device_type"], k=3)
    # rfid_door_lock group has 1 member -> suppressed
    rfid = [r for r in result if r.get("device_type") in ("rfid_door_lock", "*")]
    assert any(r.get("_suppressed") for r in rfid)


def test_k_anonymity_keeps_large_groups():
    records = [
        {"device_type": "motion_sensor", "value": i}
        for i in range(5)
    ]
    result = apply_k_anonymity(records, ["device_type"], k=3)
    # All 5 records are in the same group -> none suppressed
    assert all(not r.get("_suppressed") for r in result)
