"""
hostelguard/cloud/architecture_diagram.py
Generates the system architecture diagram (outputs/architecture.png).

Shows simulated devices, wire, broker/gateway, cloud API, database,
dashboard, key store, and where each security defense sits (labeled by module).
Uses pure matplotlib with non-interactive Agg backend.
"""

import logging
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

logger = logging.getLogger(__name__)


def _draw_box(ax, x, y, w, h, title, subtitle, color, border_color="#1e293b"):
    """Draw a styled rounded bounding box with title and description."""
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.03",
        facecolor=color, edgecolor=border_color, linewidth=1.5, alpha=0.95
    )
    ax.add_patch(box)
    ax.text(x + w / 2, y + h - 0.05, title, ha="center", va="top",
            fontsize=10, fontweight="bold", color="#0f172a")
    ax.text(x + w / 2, y + h / 2 - 0.02, subtitle, ha="center", va="center",
            fontsize=8, color="#334155")


def _draw_arrow(ax, x1, y1, x2, y2, label=""):
    """Draw a connecting arrow with optional label between components."""
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="->", color="#475569", lw=1.8, shrinkA=5, shrinkB=5)
    )
    if label:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.02, label,
                ha="center", va="bottom", fontsize=7.5, color="#0f172a",
                backgroundcolor="#ffffff", bbox=dict(boxstyle="square,pad=0.1", fc="white", ec="none"))


def generate_architecture_diagram(output_path: str) -> None:
    """Generate outputs/architecture.png showing components and security layers."""
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Title
    ax.text(0.5, 0.96, "HostelGuard (SecureIoT-Sim) - System Architecture & Defenses",
            ha="center", va="center", fontsize=15, fontweight="bold", color="#0f172a")
    ax.text(0.5, 0.92, "Layered Defense Model Across Simulated IoT Stack",
            ha="center", va="center", fontsize=10, color="#64748b")

    # 1. Devices (Left)
    _draw_box(ax, 0.03, 0.52, 0.22, 0.32,
              "IoT Devices (8 units)\n[4 Types: Lock, Temp, Energy, Motion]",
              "• M1: Insecure raw baseline\n• M2: AES-256-GCM encryption\n• M2: ECDSA P-256 signatures\n• M2: Monotonic counter",
              "#dbeafe", "#2563eb")

    # 2. Key Store (Bottom Left)
    _draw_box(ax, 0.03, 0.12, 0.22, 0.28,
              "Key Store (keystore.json)\n[Module 2: Cryptography]",
              "• AES-GCM 256-bit keys\n• HMAC-SHA256 secrets\n• ECDSA private/public pairs\n• JWT secret management",
              "#fef3c7", "#d97706")

    # 3. Virtual Wire (Middle Left)
    _draw_box(ax, 0.32, 0.56, 0.16, 0.24,
              "Virtual Wire Bus\n[In-Memory Pub/Sub]",
              "• Transports byte envelopes\n• Attacker Tap Hook\n• Sniff / Tamper / Inject\n• Transcript logging",
              "#f1f5f9", "#64748b")

    # 4. Message Broker & Gateway (Center)
    _draw_box(ax, 0.54, 0.50, 0.20, 0.36,
              "Secure Broker / Gateway\n[Modules 2 & 3]",
              "• M2: HMAC integrity check\n• M2: Replay counter window\n• M3: JWT token validation\n• M3: RBAC topic permissions\n• M3: Token-bucket rate limiter",
              "#dcfce7", "#16a34a")

    # 5. Access Control & Privacy Engine (Bottom Center)
    _draw_box(ax, 0.32, 0.12, 0.38, 0.28,
              "Access & Privacy Engine\n[Module 3: Access Control & Privacy]",
              "• Device Registry: bcrypt(cost=12) password hash\n• Brute-force lockout (5 attempts)\n• Role-Based Access Control matrix\n• Data Minimisation, Differential Privacy (Laplace), K-Anonymity",
              "#ede9fe", "#7c3aed")

    # 6. Cloud Service & Audit Log (Upper Right)
    _draw_box(ax, 0.78, 0.52, 0.19, 0.32,
              "Cloud API & Storage\n[Module 4: Cloud Security]",
              "• Flask REST endpoints\n• JWT role verification\n• AES-GCM encrypted storage\n• Tamper-evident audit log\n• Alerting on violations",
              "#ffedd5", "#ea580c")

    # 7. Web Dashboard (Bottom Right)
    _draw_box(ax, 0.78, 0.12, 0.19, 0.28,
              "Dashboard & DB\n[Module 4: Visualization]",
              "• Bound to 127.0.0.1 (safe)\n• Live telemetry & alerts\n• SQLite (parameterized WAL)\n• Real-time system status",
              "#fee2e2", "#dc2626")

    # Arrows
    _draw_arrow(ax, 0.25, 0.68, 0.32, 0.68, "Envelopes")
    _draw_arrow(ax, 0.48, 0.68, 0.54, 0.68, "Publish")
    _draw_arrow(ax, 0.74, 0.68, 0.78, 0.68, "Ingest")
    _draw_arrow(ax, 0.88, 0.52, 0.88, 0.40, "Store / Read")
    _draw_arrow(ax, 0.14, 0.40, 0.14, 0.52, "Keys / Nonces")
    _draw_arrow(ax, 0.25, 0.26, 0.32, 0.26, "Auth Creds")
    _draw_arrow(ax, 0.54, 0.40, 0.54, 0.50, "RBAC / Policy")

    plt.tight_layout()
    pathlib.Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close()
    logger.info("Architecture diagram saved to %s", output_path)
