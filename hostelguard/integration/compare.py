"""
hostelguard/integration/compare.py
Before/after comparison: runs all 6 attacks against both modes and
produces a results table and bar chart.

Output files
------------
outputs/results_insecure.json  - raw results for insecure mode
outputs/results_secure.json    - raw results for secure mode
outputs/comparison_chart.png   - side-by-side bar chart
"""

import json
import logging
import pathlib
from typing import List

logger = logging.getLogger(__name__)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _get_all_attacks():
    """Import and return instances of all six attack classes."""
    from hostelguard.attacks.replay_attack import ReplayAttack
    from hostelguard.attacks.spoofing_attack import SpoofingAttack
    from hostelguard.attacks.brute_force_attack import BruteForceAttack
    from hostelguard.attacks.flooding_attack import FloodingAttack
    from hostelguard.attacks.sniffing_attack import SniffingAttack
    from hostelguard.attacks.tampering_attack import TamperingAttack
    return [
        ReplayAttack(),
        SpoofingAttack(),
        BruteForceAttack(),
        FloodingAttack(),
        SniffingAttack(),
        TamperingAttack(),
    ]


def run_attacks_on_system(system, label: str) -> List[dict]:
    """Run all attacks against system; return list of result dicts.

    For the secure system, attacks are run against the actual security
    controls (broker.publish, cloud.login, etc.) rather than bypassing
    them via wire.inject, so the results show real blocking.
    """
    if label == "secure":
        return _run_attacks_secure(system)
    attacks = _get_all_attacks()
    results = []
    for attack in attacks:
        try:
            result = attack.run(system)
            results.append({
                "name": result.name,
                "mode": label,
                "succeeded": result.succeeded,
                "detail": result.detail,
                "metrics": result.metrics,
            })
            status = "SUCCEEDED" if result.succeeded else "BLOCKED"
            print(f"  [{status}] {result.name}: {result.detail}")
        except Exception as exc:
            logger.error("Attack %s raised exception: %s", attack.name, exc)
            results.append({
                "name": attack.name,
                "mode": label,
                "succeeded": False,
                "detail": f"Exception: {exc}",
                "metrics": {},
            })
    return results


def _run_attacks_secure(system):
    """Delegate to the dedicated secure-mode attack runner module."""
    from hostelguard.integration._secure_attack_runner import run_attacks_secure
    return run_attacks_secure(system)


def save_results(results: List[dict], path: pathlib.Path) -> None:
    """Write results to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    logger.info("Results saved to %s", path)


def print_comparison_table(insecure_results: List[dict], secure_results: List[dict]) -> None:
    """Print an ASCII before/after comparison table."""
    secure_map = {r["name"]: r for r in secure_results}
    print("\n" + "=" * 72)
    print("  BEFORE / AFTER SECURITY COMPARISON")
    print("=" * 72)
    header = f"{'Attack':<30} {'Insecure':^12} {'Secure':^12} {'Improvement':^14}"
    print(header)
    print("-" * 72)
    for ins in insecure_results:
        name = ins["name"]
        sec = secure_map.get(name, {})
        ins_status = "SUCCEEDED" if ins["succeeded"] else "BLOCKED"
        sec_status = "SUCCEEDED" if sec.get("succeeded") else "BLOCKED"
        improvement = "FIXED" if (ins["succeeded"] and not sec.get("succeeded")) else (
            "REMAINS" if ins["succeeded"] else "N/A"
        )
        print(f"  {name:<28} {ins_status:^12} {sec_status:^12} {improvement:^14}")
    print("=" * 72 + "\n")


def _annotate_bars(ax, bars, vals: List[int], color: str) -> None:
    """Add YES/NO text above each bar in a grouped bar chart."""
    for bar, val in zip(bars, vals):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.05,
            "YES" if val else "NO",
            ha="center", va="bottom", fontsize=8, color=color, fontweight="bold",
        )


def produce_comparison_chart(
    insecure_results: List[dict],
    secure_results: List[dict],
    output_path: str,
) -> None:
    """Produce a grouped bar chart showing attack success rates."""
    names = [r["name"] for r in insecure_results]
    short_names = [n.replace(" Attack", "").replace(" (DoS)", "") for n in names]
    ins_vals = [1 if r["succeeded"] else 0 for r in insecure_results]
    sec_map = {r["name"]: r for r in secure_results}
    sec_vals = [1 if sec_map.get(n, {}).get("succeeded") else 0 for n in names]

    x = range(len(names))
    width = 0.35
    fig, ax = plt.subplots(figsize=(12, 6))
    bars1 = ax.bar([i - width / 2 for i in x], ins_vals, width,
                   label="Insecure", color="#dc2626", alpha=0.85)
    bars2 = ax.bar([i + width / 2 for i in x], sec_vals, width,
                   label="Secure", color="#16a34a", alpha=0.85)

    ax.set_ylabel("Attack Succeeded (1) / Blocked (0)")
    ax.set_title(
        "HostelGuard: Before vs After Security Hardening\n"
        "(1 = attack succeeded, 0 = attack blocked)",
        fontsize=13, fontweight="bold",
    )
    ax.set_xticks(list(x))
    ax.set_xticklabels(short_names, rotation=20, ha="right")
    ax.set_ylim(0, 1.4)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["Blocked", "Succeeded"])
    ax.legend(loc="upper right")
    ax.grid(True, axis="y", alpha=0.3)

    _annotate_bars(ax, bars1, ins_vals, "#dc2626")
    _annotate_bars(ax, bars2, sec_vals, "#16a34a")

    plt.tight_layout()
    plt.savefig(output_path, dpi=100, bbox_inches="tight")
    plt.close()
    logger.info("Comparison chart saved to %s", output_path)


def run_full_comparison() -> None:
    """Run the complete before/after demonstration."""
    from hostelguard import config
    from hostelguard.integration.profiles import build_insecure_system, build_secure_system
    from hostelguard.integration.runner import run_normal_traffic

    print("\n" + "=" * 60)
    print("  HOSTELGUARD FULL SECURITY COMPARISON")
    print("=" * 60)

    # --- Insecure mode ---
    print("\n[1/4] Building INSECURE system...")
    insecure_system = build_insecure_system()
    run_normal_traffic(insecure_system)

    print("\n[2/4] Running attacks against INSECURE system...")
    insecure_results = run_attacks_on_system(insecure_system, "insecure")
    save_results(insecure_results, config.RESULTS_INSECURE_FILE)
    insecure_system.db.close()

    # --- Secure mode ---
    print("\n[3/4] Building SECURE system...")
    secure_system = build_secure_system()
    run_normal_traffic(secure_system)

    print("\n[4/4] Running attacks against SECURE system...")
    secure_results = run_attacks_on_system(secure_system, "secure")
    save_results(secure_results, config.RESULTS_SECURE_FILE)
    secure_system.db.close()

    # --- Print and chart ---
    print_comparison_table(insecure_results, secure_results)
    produce_comparison_chart(
        insecure_results, secure_results,
        str(config.OUTPUTS_DIR / "comparison_chart.png"),
    )
    print(f"Chart saved to: {config.OUTPUTS_DIR / 'comparison_chart.png'}")
    print(f"Results saved to: {config.OUTPUTS_DIR}")
