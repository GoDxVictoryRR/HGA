"""
hostelguard/config.py
Central configuration for the HostelGuard simulation.

All tunable numbers, device definitions, role names and file paths live here.
No other module uses magic numbers; they always import from this file.
"""

import pathlib

# ---------------------------------------------------------------------------
# Project root and output paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = pathlib.Path(__file__).parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
DOCS_DIR = PROJECT_ROOT / "docs"

# Ensure output directory exists when this module is imported
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

DB_FILE = OUTPUTS_DIR / "hostelguard.db"
KEYSTORE_FILE = OUTPUTS_DIR / "keystore.json"
RESULTS_INSECURE_FILE = OUTPUTS_DIR / "results_insecure.json"
RESULTS_SECURE_FILE = OUTPUTS_DIR / "results_secure.json"

# ---------------------------------------------------------------------------
# Device fleet (8 devices, 4 types)
# ---------------------------------------------------------------------------
# Each device: id, type, location
DEVICES = [
    {"id": "rfid_main_gate",    "type": "rfid_door_lock",    "location": "main_gate"},
    {"id": "rfid_warden_room",  "type": "rfid_door_lock",    "location": "warden_room"},
    {"id": "temp_room_101",     "type": "temperature_sensor","location": "room_101"},
    {"id": "temp_mess_hall",    "type": "temperature_sensor","location": "mess_hall"},
    {"id": "energy_floor1",     "type": "energy_meter",      "location": "floor_1"},
    {"id": "energy_floor2",     "type": "energy_meter",      "location": "floor_2"},
    {"id": "motion_corridor",   "type": "motion_sensor",     "location": "corridor"},
    {"id": "motion_stairwell",  "type": "motion_sensor",     "location": "stairwell"},
]

# ---------------------------------------------------------------------------
# Role names
# ---------------------------------------------------------------------------
ROLE_WARDEN = "warden"
ROLE_TECHNICIAN = "technician"
ROLE_STUDENT = "student"
ROLE_DEVICE = "device"
ALL_ROLES = [ROLE_WARDEN, ROLE_TECHNICIAN, ROLE_STUDENT, ROLE_DEVICE]

# ---------------------------------------------------------------------------
# Topic naming scheme: <device_type>/<device_id>/<kind>
# kind is "telemetry" for sensor data or "command" for control messages
# ---------------------------------------------------------------------------
def make_topic(device_id: str, kind: str) -> str:
    """Return the canonical topic string for a device and message kind."""
    return f"{device_id}/{kind}"

TOPIC_TELEMETRY = "telemetry"
TOPIC_COMMAND = "command"

# ---------------------------------------------------------------------------
# Security / crypto settings
# ---------------------------------------------------------------------------
# AES-GCM nonce size in bytes
AES_NONCE_SIZE = 12
# AES-GCM tag size in bytes (GCM default, not configurable in cryptography lib)
AES_TAG_SIZE = 16
# AES key size in bytes (256-bit)
AES_KEY_SIZE = 32

# HMAC digest algorithm name (used with hashlib)
HMAC_DIGEST = "sha256"

# ECDSA curve name (used with cryptography library)
ECDSA_CURVE = "secp256r1"

# JWT algorithm
JWT_ALGORITHM = "HS256"

# Token lifetime in seconds
TOKEN_LIFETIME_SECONDS = 3600  # 1 hour

# Replay window: messages older than this many seconds are rejected
REPLAY_WINDOW_SECONDS = 30

# Message counter: how many counters to remember for replay detection
REPLAY_COUNTER_WINDOW = 1000

# ---------------------------------------------------------------------------
# bcrypt settings
# ---------------------------------------------------------------------------
BCRYPT_COST_NORMAL = 12   # production cost (slow, secure)
BCRYPT_COST_TEST = 4      # fast cost used only in tests

# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------
# Maximum messages per device per second in normal mode
RATE_LIMIT_MAX_PER_SECOND = 10
# If a device exceeds this count in one second, it is flagged
RATE_LIMIT_BURST = 20
# Lockout duration in seconds after too many failed auth attempts
LOCKOUT_DURATION_SECONDS = 60
# Number of failed attempts before lockout
LOCKOUT_THRESHOLD = 5

# ---------------------------------------------------------------------------
# Privacy settings
# ---------------------------------------------------------------------------
# Differential privacy epsilon (lower = more private)
PRIVACY_EPSILON = 1.0
# Minimum group size for k-anonymity
PRIVACY_MIN_GROUP_SIZE = 3

# ---------------------------------------------------------------------------
# Simulation / reproducibility
# ---------------------------------------------------------------------------
# Seed for the simulation random number generator (sensor noise, traffic)
# Crypto material always uses os.urandom, never this seed.
SIM_RANDOM_SEED = 42

# Normal traffic simulation: how many messages each device sends per demo run
SIM_MESSAGES_PER_DEVICE = 5

# ---------------------------------------------------------------------------
# Attack budgets (limits for simulated attacks, kept small and educational)
# ---------------------------------------------------------------------------
# Brute-force attack: maximum number of password guesses
ATTACK_BRUTE_FORCE_GUESSES = 20
# Flood attack: number of messages injected
ATTACK_FLOOD_SIZE = 50
# Replay attack: how many stored messages to replay
ATTACK_REPLAY_COUNT = 3
# Sniff attack: how many messages to capture
ATTACK_SNIFF_COUNT = 5
