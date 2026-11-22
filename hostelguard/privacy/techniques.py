"""
hostelguard/privacy/techniques.py
Three privacy-preserving techniques applied to telemetry data.

1. Data Minimisation   – strip PII fields before storing/sharing.
2. Differential Privacy – add calibrated Laplace noise to numeric readings.
3. K-Anonymity         – suppress records that belong to groups smaller
                         than k so individual devices cannot be singled out.

Produces before/after graphs saved to outputs/privacy_comparison.png.
"""

import logging
import random
import math
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Non-interactive matplotlib backend for headless / Windows environments
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ---------------------------------------------------------------------------
# 1. Data Minimisation
# ---------------------------------------------------------------------------

# Fields that identify an individual device (remove before sharing)
_PII_FIELDS = {"device_id", "location", "mac_address", "serial"}


def minimise(record: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of record with PII fields removed."""
    return {k: v for k, v in record.items() if k not in _PII_FIELDS}


# ---------------------------------------------------------------------------
# 2. Differential Privacy (Laplace mechanism)
# ---------------------------------------------------------------------------

def _laplace_noise(sensitivity: float, epsilon: float) -> float:
    """Sample noise from the Laplace distribution.

    sensitivity : global sensitivity of the query (max change one record
                  can cause in the output)
    epsilon     : privacy budget (lower = more private)
    """
    scale = sensitivity / epsilon
    # Use the standard library random module with the simulation seed.
    # This is NOT a secret; it is intentionally reproducible noise.
    u = random.uniform(-0.5, 0.5)
    if u >= 0:
        return -scale * math.log(1 - 2 * u)
    else:
        return scale * math.log(1 + 2 * u)


def add_dp_noise(
    value: float,
    sensitivity: float = 5.0,
    epsilon: float = None,
) -> float:
    """Add Laplace noise to a numeric value for differential privacy."""
    from hostelguard import config
    if epsilon is None:
        epsilon = config.PRIVACY_EPSILON
    noise = _laplace_noise(sensitivity, epsilon)
    return round(value + noise, 2)


def apply_dp_to_records(
    records: List[Dict[str, Any]],
    numeric_fields: List[str],
    sensitivity: float = 5.0,
) -> List[Dict[str, Any]]:
    """Return a new list of records with DP noise on numeric fields."""
    result = []
    for rec in records:
        noisy = dict(rec)
        for field in numeric_fields:
            if field in noisy and isinstance(noisy[field], (int, float)):
                noisy[field] = add_dp_noise(float(noisy[field]), sensitivity)
        result.append(noisy)
    return result


# ---------------------------------------------------------------------------
# 3. K-Anonymity
# ---------------------------------------------------------------------------

def apply_k_anonymity(
    records: List[Dict[str, Any]],
    quasi_identifiers: List[str],
    k: int = None,
) -> List[Dict[str, Any]]:
    """Suppress records whose quasi-identifier group has fewer than k members.

    Records that cannot be generalised into a group of at least k are
    replaced with a suppressed marker so they cannot identify an individual.
    """
    from hostelguard import config
    if k is None:
        k = config.PRIVACY_MIN_GROUP_SIZE

    # Count group sizes based on quasi-identifier values
    groups: Dict[tuple, List[int]] = {}
    for idx, rec in enumerate(records):
        key = tuple(str(rec.get(qi, "?")) for qi in quasi_identifiers)
        groups.setdefault(key, []).append(idx)

    result = []
    for idx, rec in enumerate(records):
        key = tuple(str(rec.get(qi, "?")) for qi in quasi_identifiers)
        if len(groups[key]) >= k:
            result.append(dict(rec))
        else:
            # Suppress: replace quasi-identifier values with '*'
            suppressed = dict(rec)
            for qi in quasi_identifiers:
                suppressed[qi] = "*"
            suppressed["_suppressed"] = True
            result.append(suppressed)
    return result


# ---------------------------------------------------------------------------
# Comparison graph
# ---------------------------------------------------------------------------

def _extract_temps(raw_records: List[Dict[str, Any]]) -> List[float]:
    """Pull temperature_c values from records; synthesise demo data if none."""
    temps = [
        r.get("temperature_c", r.get("payload", {}).get("temperature_c", 0))
        for r in raw_records
        if "temperature_c" in r or isinstance(r.get("payload"), dict)
    ]
    if not temps:
        import random as _rnd
        _rnd.seed(42)
        temps = [round(_rnd.uniform(22, 32), 2) for _ in range(20)]
    return temps


def _plot_dp_panel(ax, temps_raw: List[float], temps_dp: List[float]) -> None:
    """Draw the differential-privacy before/after line chart on ax."""
    x = list(range(len(temps_raw)))
    ax.plot(x, temps_raw, "o-", label="Original", color="#2563eb")
    ax.plot(x, temps_dp, "s--", label="DP Noised", color="#dc2626")
    ax.set_xlabel("Reading index")
    ax.set_ylabel("Temperature (C)")
    ax.set_title(f"Differential Privacy (epsilon={1.0})")
    ax.legend()
    ax.grid(True, alpha=0.3)


def _plot_kanon_panel(ax) -> None:
    """Draw the k-anonymity kept/suppressed bar chart on ax."""
    demo_records = [
        {"device_type": "temperature_sensor", "location": "room_101"},
        {"device_type": "temperature_sensor", "location": "room_101"},
        {"device_type": "temperature_sensor", "location": "room_101"},
        {"device_type": "rfid_door_lock",    "location": "main_gate"},
        {"device_type": "energy_meter",      "location": "floor_1"},
        {"device_type": "motion_sensor",     "location": "corridor"},
        {"device_type": "motion_sensor",     "location": "corridor"},
        {"device_type": "motion_sensor",     "location": "corridor"},
    ]
    result = apply_k_anonymity(demo_records, ["device_type"], k=3)
    kept = sum(1 for r in result if not r.get("_suppressed"))
    suppressed = sum(1 for r in result if r.get("_suppressed"))
    ax.bar(["Kept", "Suppressed"], [kept, suppressed],
           color=["#2563eb", "#dc2626"], width=0.4)
    ax.set_title(f"K-Anonymity (k=3): {kept} kept, {suppressed} suppressed")
    ax.set_ylabel("Record count")
    for i, v in enumerate([kept, suppressed]):
        ax.text(i, v + 0.1, str(v), ha="center", fontweight="bold")


def produce_privacy_graph(
    raw_records: List[Dict[str, Any]],
    output_path: str,
) -> None:
    """Generate a before/after privacy comparison chart.

    Shows original vs DP-noised temperature readings, and k-anonymity
    group suppression counts.
    """
    temps_raw = _extract_temps(raw_records)
    temps_dp = [add_dp_noise(t) for t in temps_raw]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle("Privacy Techniques: Before vs After", fontsize=14, fontweight="bold")
    _plot_dp_panel(ax1, temps_raw, temps_dp)
    _plot_kanon_panel(ax2)
    plt.tight_layout()
    plt.savefig(output_path, dpi=100, bbox_inches="tight")
    plt.close()
    logger.info("Privacy comparison graph saved to %s", output_path)
