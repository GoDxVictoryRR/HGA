"""
hostelguard/integration/profiles.py
Profile factory: builds a SystemContainer for a given mode.

Mode "insecure": assembles all intentionally-insecure components.
Mode "secure":   assembles the hardened components from Phases 3-5.

No business logic lives here; this file only wires components together.
"""

import logging

from hostelguard import config
from hostelguard.clock import Clock
from hostelguard.db import Database
from hostelguard.exceptions import NotImplementedYet
from hostelguard.sim.interfaces import SystemContainer
from hostelguard.sim.insecure_broker import InsecureBroker
from hostelguard.sim.insecure_cloud import InsecureCloudService
from hostelguard.sim.insecure_device import InsecureDevice
from hostelguard.sim.wire import Wire

logger = logging.getLogger(__name__)


def build_insecure_system(clock: Clock = None, db: Database = None) -> SystemContainer:
    """Build and return a fully insecure SystemContainer."""
    if clock is None:
        clock = Clock()
    if db is None:
        db = Database(config.DB_FILE)
        db.reset()

    wire = Wire()
    broker = InsecureBroker(wire)
    cloud = InsecureCloudService(db)

    devices = [
        InsecureDevice(
            device_id=d["id"],
            device_type=d["type"],
            location=d["location"],
            clock=clock,
        )
        for d in config.DEVICES
    ]

    logger.info("Built insecure system with %d devices", len(devices))
    return SystemContainer(
        wire=wire,
        broker=broker,
        devices=devices,
        cloud=cloud,
        clock=clock,
        mode="insecure",
        db=db,
    )


def _import_secure_components():
    """Import all secure-mode modules; raises NotImplementedYet if any are missing."""
    try:
        from hostelguard.crypto.keystore import KeyStore
        from hostelguard.access.registry import DeviceRegistry
        from hostelguard.access.secure_broker import SecureBroker
        from hostelguard.access.secure_cloud import SecureCloudService
        from hostelguard.sim.secure_device import SecureDevice
        return KeyStore, DeviceRegistry, SecureBroker, SecureCloudService, SecureDevice
    except ImportError as exc:
        raise NotImplementedYet(f"Secure components not yet implemented: {exc}") from exc


def _build_secure_devices(device_cfgs, keystore, clock, SecureDevice) -> list:
    """Instantiate a SecureDevice for every device in the config."""
    return [
        SecureDevice(
            device_id=d["id"],
            device_type=d["type"],
            location=d["location"],
            clock=clock,
            keystore=keystore,
        )
        for d in device_cfgs
    ]


def build_secure_system(clock: Clock = None, db: Database = None) -> SystemContainer:
    """Build and return a fully secure SystemContainer."""
    KeyStore, DeviceRegistry, SecureBroker, SecureCloudService, SecureDevice = (
        _import_secure_components()
    )
    if clock is None:
        clock = Clock()
    if db is None:
        db = Database(config.DB_FILE)
        db.reset()

    keystore = KeyStore(config.KEYSTORE_FILE)
    wire = Wire()
    registry = DeviceRegistry(db, keystore)
    broker = SecureBroker(wire, registry, clock)
    cloud = SecureCloudService(db, keystore, clock)
    devices = _build_secure_devices(config.DEVICES, keystore, clock, SecureDevice)

    logger.info("Built secure system with %d devices", len(devices))
    return SystemContainer(
        wire=wire, broker=broker, devices=devices, cloud=cloud,
        clock=clock, mode="secure", registry=registry,
        keystore=keystore, db=db,
    )


def build_system(mode: str, clock: Clock = None, db: Database = None) -> SystemContainer:
    """Entry point: build a system for the given mode string."""
    if mode == "insecure":
        return build_insecure_system(clock=clock, db=db)
    elif mode == "secure":
        return build_secure_system(clock=clock, db=db)
    else:
        raise ValueError(f"Unknown mode: {mode!r}. Use 'insecure' or 'secure'.")
