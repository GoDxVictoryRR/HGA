"""
hostelguard/attacks/security_trees.py
Produces an attack tree and a fault tree for the HostelGuard threat model.

Attack tree  : models how an attacker can compromise the system.
Fault tree   : models how a system failure can occur from component faults.

Both are drawn with matplotlib (networkx for layout) and saved to outputs/.
"""

import logging
import pathlib

logger = logging.getLogger(__name__)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx


def _draw_tree(
    G: nx.DiGraph,
    root: str,
    node_colors: dict,
    title: str,
    output_path: str,
) -> None:
    """Draw a directed tree using a hierarchical layout and save it."""
    # Use our pure-Python hierarchical layout (no graphviz dependency)
    pos = _hierarchy_pos(G, root)

    fig, ax = plt.subplots(figsize=(14, 8))
    node_list = list(G.nodes())
    colors = [node_colors.get(n, "#93c5fd") for n in node_list]

    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=colors,
                           node_size=2000, node_shape="s", alpha=0.9)
    nx.draw_networkx_edges(G, pos, ax=ax, arrows=True,
                           arrowstyle="-|>", arrowsize=15,
                           edge_color="#475569", width=1.5)

    # Wrap long labels
    labels = {n: "\n".join(n[i:i+18] for i in range(0, len(n), 18)) for n in node_list}
    nx.draw_networkx_labels(G, pos, labels=labels, ax=ax, font_size=7, font_color="black")

    ax.set_title(title, fontsize=14, fontweight="bold", pad=20)
    ax.axis("off")

    legend_patches = [
        mpatches.Patch(color="#ef4444", label="Goal / Top event"),
        mpatches.Patch(color="#f97316", label="OR gate / intermediate"),
        mpatches.Patch(color="#93c5fd", label="Basic attack / leaf"),
        mpatches.Patch(color="#86efac", label="AND gate / defence bypassed"),
    ]
    ax.legend(handles=legend_patches, loc="lower left", fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, dpi=100, bbox_inches="tight")
    plt.close()
    logger.info("Tree saved to %s", output_path)


def _hierarchy_pos(G, root, width=1.0, vert_gap=0.3, vert_loc=0.0, xcenter=0.5):
    """Compute hierarchical positions for a tree rooted at root."""
    pos = {}
    _recurse(G, root, left=0.0, right=width, vert_loc=vert_loc,
             vert_gap=vert_gap, xcenter=xcenter, pos=pos, parent=None)
    return pos


def _recurse(G, node, left, right, vert_loc, vert_gap, xcenter, pos, parent):
    pos[node] = ((left + right) / 2, vert_loc)
    children = list(G.successors(node))
    if children:
        dx = (right - left) / len(children)
        nextx = left
        for child in children:
            _recurse(G, child, nextx, nextx + dx, vert_loc - vert_gap,
                     vert_gap, nextx + dx / 2, pos, node)
            nextx += dx


def produce_attack_tree(output_path: str) -> None:
    """Draw the HostelGuard attack tree and save it."""
    G = nx.DiGraph()

    # Root goal
    root = "Compromise\nSmart Hostel"
    G.add_node(root)

    # Level 1: main attack paths (OR)
    l1 = [
        "Gain Unauthorised\nCloud Access",
        "Control\nPhysical Devices",
        "Intercept/Modify\nCommunications",
        "Disrupt\nSystem Availability",
    ]
    for n in l1:
        G.add_edge(root, n)

    # Cloud access subtree
    G.add_edge("Gain Unauthorised\nCloud Access", "Brute Force\nPassword")
    G.add_edge("Gain Unauthorised\nCloud Access", "Steal\nSession Token")
    G.add_edge("Gain Unauthorised\nCloud Access", "SQL\nInjection")

    # Physical device subtree
    G.add_edge("Control\nPhysical Devices", "Spoof\nWarden Command")
    G.add_edge("Control\nPhysical Devices", "Replay\nValid Command")
    G.add_edge("Spoof\nWarden Command", "Forge Device ID")
    G.add_edge("Spoof\nWarden Command", "No Signature\nCheck")

    # Communications subtree
    G.add_edge("Intercept/Modify\nCommunications", "Passive\nSniffing")
    G.add_edge("Intercept/Modify\nCommunications", "Active\nTampering")
    G.add_edge("Passive\nSniffing", "Plaintext\nPayloads")
    G.add_edge("Active\nTampering", "No MAC\nCheck")

    # Availability subtree
    G.add_edge("Disrupt\nSystem Availability", "Message\nFlooding (DoS)")
    G.add_edge("Disrupt\nSystem Availability", "Exhaust\nDB Storage")

    colors = {
        root: "#ef4444",
        "Gain Unauthorised\nCloud Access": "#f97316",
        "Control\nPhysical Devices": "#f97316",
        "Intercept/Modify\nCommunications": "#f97316",
        "Disrupt\nSystem Availability": "#f97316",
    }

    _draw_tree(G, root, colors, "HostelGuard Attack Tree", output_path)


def produce_fault_tree(output_path: str) -> None:
    """Draw the HostelGuard fault tree and save it."""
    G = nx.DiGraph()

    root = "System Security\nFailure (Top)"
    G.add_node(root)

    l1 = [
        "Authentication\nFailure (OR)",
        "Integrity\nFailure (OR)",
        "Confidentiality\nFailure (OR)",
        "Availability\nFailure (OR)",
    ]
    for n in l1:
        G.add_edge(root, n)

    G.add_edge("Authentication\nFailure (OR)", "Weak\nPassword Storage")
    G.add_edge("Authentication\nFailure (OR)", "No Account\nLockout")
    G.add_edge("Authentication\nFailure (OR)", "Token Not\nExpired")

    G.add_edge("Integrity\nFailure (OR)", "No Message\nMAC")
    G.add_edge("Integrity\nFailure (OR)", "No Digital\nSignature")
    G.add_edge("Integrity\nFailure (OR)", "No Replay\nCounter")

    G.add_edge("Confidentiality\nFailure (OR)", "Plaintext\nPayload on Wire")
    G.add_edge("Confidentiality\nFailure (OR)", "Plaintext\nDB Storage")

    G.add_edge("Availability\nFailure (OR)", "No Rate\nLimiter")
    G.add_edge("Availability\nFailure (OR)", "Single Point\nof Failure Broker")

    colors = {
        root: "#ef4444",
        "Authentication\nFailure (OR)": "#f97316",
        "Integrity\nFailure (OR)": "#f97316",
        "Confidentiality\nFailure (OR)": "#f97316",
        "Availability\nFailure (OR)": "#f97316",
    }

    _draw_tree(G, root, colors, "HostelGuard Fault Tree", output_path)


def produce_security_requirements_table(output_path: str) -> None:
    """Write a security requirements table as a markdown file."""
    text = """# Security Requirements Table

| ID  | Requirement                            | Category        | Module | Attack Mitigated          |
|-----|----------------------------------------|-----------------|--------|---------------------------|
| SR1 | All passwords stored as bcrypt hashes  | Authentication  | M3     | Brute Force               |
| SR2 | Account lockout after 5 failed attempts| Authentication  | M3     | Brute Force               |
| SR3 | JWT tokens with 1-hour expiry          | Authentication  | M3/M4  | Token theft               |
| SR4 | RBAC enforced on all broker operations | Authorization   | M3     | Privilege escalation      |
| SR5 | RBAC enforced on all cloud queries     | Authorization   | M3     | Unauthorised data access  |
| SR6 | AES-256-GCM payload encryption         | Confidentiality | M2     | Sniffing                  |
| SR7 | HMAC-SHA256 message authentication     | Integrity       | M2     | Tampering                 |
| SR8 | ECDSA digital signatures per device    | Integrity       | M2     | Spoofing                  |
| SR9 | Monotonic counter + timestamp window   | Replay prevent. | M2     | Replay attack             |
| SR10| Rate limit: max 10 msg/s per device    | Availability    | M3     | Flooding / DoS            |
| SR11| Encrypted telemetry storage in DB      | Confidentiality | M4     | Data breach               |
| SR12| Tamper-evident audit log               | Accountability  | M4     | Repudiation               |
| SR13| Alerts on suspicious login activity    | Detection       | M4     | Insider threat            |
| SR14| Device registration and revocation     | Access control  | M3     | Rogue device              |
| SR15| Dashboard bound to 127.0.0.1 only      | Network security| M4     | Remote exploitation       |
"""
    pathlib.Path(output_path).write_text(text, encoding="utf-8")
    logger.info("Security requirements table written to %s", output_path)
