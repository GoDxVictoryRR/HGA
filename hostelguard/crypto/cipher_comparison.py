"""
hostelguard/crypto/cipher_comparison.py
Compare AES-GCM vs a simple XOR 'cipher' to demonstrate why proper
encryption matters.

Produces a bar chart saved to outputs/cipher_comparison.png.

XOR with a fixed key is intentionally weak (educational contrast only).
"""

import logging
import os
import time

logger = logging.getLogger(__name__)

# Use non-interactive matplotlib backend for headless / Windows environments
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _xor_cipher(key: bytes, data: bytes) -> bytes:
    """XOR each byte of data with the repeating key.  Weak, for contrast."""
    key_len = len(key)
    return bytes(b ^ key[i % key_len] for i, b in enumerate(data))


def _time_cipher(encrypt_fn, plaintext: bytes, iterations: int) -> float:
    """Return mean time per encrypt call in milliseconds."""
    t0 = time.perf_counter()
    for _ in range(iterations):
        encrypt_fn(plaintext)
    return (time.perf_counter() - t0) / iterations * 1000


def _build_properties(aes_time: float, xor_time: float) -> dict:
    """Return security property summary dict for both ciphers."""
    return {
        "AES-256-GCM": {
            "time_ms": round(aes_time, 4),
            "confidentiality": "Yes",
            "integrity": "Yes (authenticated)",
            "replay_protection": "Via nonce uniqueness",
            "key_size_bits": 256,
        },
        "XOR (weak)": {
            "time_ms": round(xor_time, 4),
            "confidentiality": "No (trivially broken)",
            "integrity": "No",
            "replay_protection": "No",
            "key_size_bits": 256,
        },
    }


def _plot_comparison(output_path: str, aes_time: float, xor_time: float) -> None:
    """Render and save the two-panel comparison chart."""
    ciphers = ["AES-256-GCM", "XOR (weak)"]
    times = [aes_time, xor_time]
    colors = ["#2563eb", "#dc2626"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
    fig.suptitle("Cipher Comparison: AES-256-GCM vs XOR", fontsize=14, fontweight="bold")

    bars = ax1.bar(ciphers, times, color=colors, width=0.4)
    ax1.set_ylabel("Time per operation (ms)")
    ax1.set_title("Encryption Speed")
    for bar, t in zip(bars, times):
        ax1.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 0.0001,
                 f"{t:.4f} ms", ha="center", va="bottom", fontsize=9)

    ax2.axis("off")
    table_data = [
        ["Property", "AES-256-GCM", "XOR (weak)"],
        ["Confidentiality", "Yes", "No"],
        ["Integrity", "Yes", "No"],
        ["Authentication", "Yes (AEAD)", "No"],
        ["Nonce needed", "Yes", "No"],
        ["Secure", "YES", "NO"],
    ]
    tbl = ax2.table(cellText=table_data[1:], colLabels=table_data[0],
                    cellLoc="center", loc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1.2, 1.5)
    for col in range(3):
        tbl[0, col].set_facecolor("#1e3a5f")
        tbl[0, col].set_text_props(color="white", fontweight="bold")
    ax2.set_title("Security Properties")

    plt.tight_layout()
    plt.savefig(output_path, dpi=100, bbox_inches="tight")
    plt.close()
    logger.info("Cipher comparison chart saved to %s", output_path)


def run_comparison(output_path: str, iterations: int = 500) -> dict:
    """Benchmark AES-256-GCM vs XOR cipher; save chart; return property notes."""
    from hostelguard.crypto.aes_gcm import AesGcmCipher

    plaintext = os.urandom(256)
    aes_key = AesGcmCipher.generate_key()
    cipher = AesGcmCipher(aes_key)
    aes_time = _time_cipher(lambda pt: cipher.encrypt(pt), plaintext, iterations)

    xor_key = os.urandom(32)
    xor_time = _time_cipher(lambda pt: _xor_cipher(xor_key, pt), plaintext, iterations)

    _plot_comparison(output_path, aes_time, xor_time)
    return _build_properties(aes_time, xor_time)
