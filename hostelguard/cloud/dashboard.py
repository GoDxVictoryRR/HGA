"""
hostelguard/cloud/dashboard.py
Modular, explainable Flask dashboard for the HostelGuard cloud service.

Serves an interactive security console at http://127.0.0.1:5000/ showing:
- Real-time system posture, mode and active defenses
- Architectural pipeline workflow explainer
- Active mitigation status for all 6 simulated attacks
- Decrypted IoT sensor telemetry with device category badges
- Tamper-evident forensic audit trail with security alert flags

The server binds to 127.0.0.1 ONLY (never 0.0.0.0).
Start it with: python main.py --mode secure --serve
"""

import datetime
import logging
from typing import Any

from hostelguard.cloud.template import DASHBOARD_HTML_TEMPLATE

logger = logging.getLogger(__name__)


def _format_device_type(device_id: str) -> str:
    """Return colored type tag HTML based on device prefix."""
    if "rfid" in device_id:
        return '<span class="type-tag type-rfid">RFID LOCK</span>'
    elif "temp" in device_id:
        return '<span class="type-tag type-temp">TEMPERATURE</span>'
    elif "energy" in device_id:
        return '<span class="type-tag type-energy">ENERGY METER</span>'
    elif "motion" in device_id:
        return '<span class="type-tag type-motion">MOTION SENSOR</span>'
    return '<span class="type-tag">DEVICE</span>'


def _render_telemetry_rows(telemetry: Any, fmt_time_fn) -> str:
    """Format telemetry records into styled HTML table rows."""
    if not isinstance(telemetry, list) or not telemetry:
        return "<tr><td colspan='4' style='text-align:center; padding:20px; color:#64748b;'>No telemetry yet</td></tr>"
    rows = []
    for row in telemetry[:20]:
        dev_id = str(row.get("device_id", ""))
        topic = str(row.get("topic", ""))
        payload = str(row.get("payload_plaintext", row.get("payload", "")))
        ts = fmt_time_fn(row.get("timestamp", ""))
        type_tag = _format_device_type(dev_id)
        rows.append(
            f"<tr>"
            f"<td>{type_tag}<span class='device-chip'>{dev_id}</span></td>"
            f"<td><span style='color:#64748b; font-family:monospace;'>{topic}</span></td>"
            f"<td><span class='payload-box'>{payload[:95]}</span></td>"
            f"<td><span style='color:#475569; font-weight:500;'>{ts}</span></td>"
            f"</tr>"
        )
    return "".join(rows)


def _render_audit_rows(audit: Any, fmt_time_fn) -> str:
    """Format audit entries into styled HTML table rows."""
    if not isinstance(audit, list) or not audit:
        return "<tr><td colspan='5' style='text-align:center; padding:20px; color:#64748b;'>No audit log entries</td></tr>"
    rows = []
    for entry in audit[:20]:
        is_alert = bool(entry.get("alert"))
        badge = (
            '<span class="pill pill-alert">ALERT</span>'
            if is_alert else '<span class="pill pill-ok">OK</span>'
        )
        ts = fmt_time_fn(entry.get("timestamp", ""))
        actor = str(entry.get("actor", ""))
        action = str(entry.get("action", ""))
        detail = str(entry.get("detail", ""))
        rows.append(
            f"<tr>"
            f"<td><span style='color:#475569; font-weight:500;'>{ts}</span></td>"
            f"<td><strong>{actor}</strong></td>"
            f"<td><span class='pill pill-action'>{action}</span></td>"
            f"<td><span style='color:#334155;'>{detail}</span></td>"
            f"<td style='text-align:center;'>{badge}</td>"
            f"</tr>"
        )
    return "".join(rows)


def create_dashboard_app(system: Any) -> "object":
    """Create and return the Flask dashboard application."""
    try:
        from flask import Flask
    except ImportError as exc:
        raise RuntimeError("Flask is required for the dashboard: pip install Flask") from exc

    app = Flask(__name__)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

    @app.route("/")
    def index():
        """Render the main security dashboard console."""
        from flask import make_response

        def _fmt_time(ts):
            try:
                return datetime.datetime.fromtimestamp(
                    float(ts), datetime.timezone.utc
                ).strftime("%H:%M:%S")
            except Exception:
                return str(ts)

        telemetry = []
        audit = []
        try:
            token = system.cloud.login("warden", "warden123")
            telemetry = system.cloud.query(token, {})
            audit_res = system.cloud.admin(token, "get_audit_log", {})
            if isinstance(audit_res, list):
                audit = audit_res
        except Exception as exc:
            logger.warning("Dashboard: error fetching cloud data: %s", exc)

        trows = _render_telemetry_rows(telemetry, _fmt_time)
        arows = _render_audit_rows(audit, _fmt_time)

        html = (
            DASHBOARD_HTML_TEMPLATE
            .replace("{{MODE}}", str(system.mode).lower())
            .replace("{{DEVICE_COUNT}}", str(len(system.devices)))
            .replace("{{TELEMETRY_ROWS}}", trows)
            .replace("{{AUDIT_ROWS}}", arows)
        )
        resp = make_response(html)
        resp.content_type = "text/html; charset=utf-8"
        return resp

    @app.route("/api/status")
    def api_status():
        """JSON status endpoint for quick health checks."""
        from flask import jsonify
        return jsonify({
            "mode": system.mode,
            "device_count": len(system.devices),
            "transcript_length": len(system.wire.transcript),
            "status": "ok",
        })

    return app


def run_dashboard(system: Any, port: int = 5000) -> None:
    """Start the Flask dashboard bound to 127.0.0.1 only."""
    app = create_dashboard_app(system)
    logger.info("Starting dashboard at http://127.0.0.1:%d/", port)
    print(f"\nDashboard running at http://127.0.0.1:{port}/")
    print("Press Ctrl+C to stop.\n")
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
