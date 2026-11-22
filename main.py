"""
main.py
HostelGuard (SecureIoT-Sim) entry point.

Usage
-----
python main.py --mode insecure          # run insecure demo
python main.py --mode secure            # run secure demo
python main.py --mode compare           # run before/after comparison
python main.py --mode secure --serve    # run secure demo + start dashboard

Exit codes: 0 = success, 1 = error, 2 = argument error.
"""

import argparse
import logging
import sys

# Configure logging before importing anything else so all modules use it
logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("hostelguard.main")


def _run_insecure() -> int:
    """Run the insecure mode demonstration."""
    from hostelguard.integration.profiles import build_insecure_system
    from hostelguard.integration.runner import run_normal_traffic

    print("\n=== HostelGuard: INSECURE mode ===")
    system = build_insecure_system()
    run_normal_traffic(system)

    # Also produce security trees and requirements table on first run
    _produce_docs()

    system.db.close()
    return 0


def _run_secure() -> int:
    """Run the secure mode demonstration."""
    try:
        from hostelguard.integration.profiles import build_secure_system
    except Exception as exc:
        print(f"ERROR: Secure mode components not ready: {exc}", file=sys.stderr)
        return 1

    from hostelguard.integration.runner import run_normal_traffic

    print("\n=== HostelGuard: SECURE mode ===")
    system = build_secure_system()
    run_normal_traffic(system)
    system.db.close()
    return 0


def _run_compare() -> int:
    """Run the full before/after comparison."""
    from hostelguard.integration.compare import run_full_comparison
    run_full_comparison()
    return 0


def _run_serve() -> int:
    """Run the secure mode and start the Flask dashboard."""
    try:
        from hostelguard.integration.profiles import build_secure_system
    except Exception as exc:
        print(f"ERROR: Secure mode not ready: {exc}", file=sys.stderr)
        return 1

    from hostelguard.integration.runner import run_normal_traffic
    from hostelguard.cloud.dashboard import run_dashboard

    print("\n=== HostelGuard: SECURE mode + dashboard ===")
    system = build_secure_system()
    run_normal_traffic(system)

    # Seed demo audit events (both normal and security alert)
    try:
        system.cloud.login("intruder_bot", "admin123")
    except Exception:
        pass
    try:
        token = system.cloud.login("warden", "warden123")
        system.cloud.admin(token, "list_users", {})
    except Exception:
        pass

    try:
        run_dashboard(system)
    finally:
        system.db.close()
    return 0


def _produce_docs() -> None:
    """Generate security trees, requirements table, architecture diagram and case study."""
    from hostelguard import config
    from hostelguard.attacks.security_trees import (
        produce_attack_tree, produce_fault_tree, produce_security_requirements_table
    )
    from hostelguard.cloud.architecture_diagram import generate_architecture_diagram
    from hostelguard.cloud.case_study import write_case_study
    from hostelguard.crypto.cipher_comparison import run_comparison
    from hostelguard.privacy.techniques import produce_privacy_graph

    print("\nGenerating documentation outputs...")
    tasks = [
        ("architecture.png", lambda: generate_architecture_diagram(str(config.OUTPUTS_DIR / "architecture.png"))),
        ("attack_tree.png", lambda: produce_attack_tree(str(config.OUTPUTS_DIR / "attack_tree.png"))),
        ("fault_tree.png", lambda: produce_fault_tree(str(config.OUTPUTS_DIR / "fault_tree.png"))),
        ("security_requirements.md", lambda: produce_security_requirements_table(str(config.DOCS_DIR / "security_requirements.md"))),
        ("cipher_comparison.png", lambda: run_comparison(str(config.OUTPUTS_DIR / "cipher_comparison.png"))),
        ("privacy_comparison.png", lambda: produce_privacy_graph([], str(config.OUTPUTS_DIR / "privacy_comparison.png"))),
        ("mirai_case_study.md", lambda: write_case_study(config.DOCS_DIR / "mirai_case_study.md")),
    ]
    for filename, fn in tasks:
        try:
            fn()
            print(f"  {filename}")
        except Exception as exc:
            logger.warning("%s generation failed: %s", filename, exc)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="HostelGuard (SecureIoT-Sim) - IoT Security Demonstration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py --mode insecure\n"
            "  python main.py --mode secure\n"
            "  python main.py --mode compare\n"
            "  python main.py --mode secure --serve\n"
        ),
    )
    parser.add_argument(
        "--mode",
        choices=["insecure", "secure", "compare"],
        required=True,
        help="Operating mode",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start the web dashboard (secure mode only)",
    )

    args = parser.parse_args()

    if args.serve and args.mode != "secure":
        print("ERROR: --serve requires --mode secure", file=sys.stderr)
        return 2

    if args.serve:
        return _run_serve()
    elif args.mode == "insecure":
        return _run_insecure()
    elif args.mode == "secure":
        return _run_secure()
    elif args.mode == "compare":
        return _run_compare()
    else:
        print(f"ERROR: Unknown mode: {args.mode}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
