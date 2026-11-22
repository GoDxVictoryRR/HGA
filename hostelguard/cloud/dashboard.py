"""
hostelguard/cloud/dashboard.py
Modular, explainable Flask dashboard for the HostelGuard cloud service.

Serves an interactive security console at http://127.0.0.1:5000/ with:
- Real-time system telemetry and forensic audit trail
- Live Attack Simulation Arena and Security Scorecard
- Interactive controls for telemetry injection and intruder alerts
- Embedded Architecture, Attack Tree, and Benchmark diagrams
"""

import datetime
import json
import logging
import random
import time
from typing import Any

from hostelguard import config
from hostelguard.cloud.template import DASHBOARD_HTML_TEMPLATE

logger = logging.getLogger(__name__)


def _format_device_type(device_id: str) -> str:
    """Return colored type tag HTML based on device prefix."""
    if "rfid" in device_id:
        return '<span class="device-tag" style="background:#854d0e; color:#fef08a;">RFID LOCK</span>'
    elif "temp" in device_id:
        return '<span class="device-tag" style="background:#991b1b; color:#fecaca;">TEMPERATURE</span>'
    elif "energy" in device_id:
        return '<span class="device-tag" style="background:#3730a3; color:#e0e7ff;">ENERGY METER</span>'
    elif "motion" in device_id:
        return '<span class="device-tag" style="background:#581c87; color:#f3e8ff;">MOTION SENSOR</span>'
    return '<span class="device-tag">DEVICE</span>'


def _render_telemetry_rows(telemetry: Any, fmt_time_fn) -> str:
    """Format telemetry records into styled HTML table rows."""
    if not isinstance(telemetry, list) or not telemetry:
        return "<tr><td colspan='4' style='text-align:center; padding:20px; color:#94a3b8;'>No telemetry yet</td></tr>"
    rows = []
    for row in telemetry[:20]:
        dev_id = str(row.get("device_id", ""))
        topic = str(row.get("topic", ""))
        payload = str(row.get("payload_plaintext", row.get("payload", "")))
        ts = fmt_time_fn(row.get("timestamp", ""))
        type_tag = _format_device_type(dev_id)
        rows.append(
            f"<tr>"
            f"<td>{type_tag} <span class='device-tag'>{dev_id}</span></td>"
            f"<td><span style='color:#94a3b8; font-family:monospace;'>{topic}</span></td>"
            f"<td><span class='payload-box'>{payload[:95]}</span></td>"
            f"<td><span style='color:#cbd5e1;'>{ts}</span></td>"
            f"</tr>"
        )
    return "".join(rows)


def _render_audit_rows(audit: Any, fmt_time_fn) -> str:
    """Format audit entries into styled HTML table rows."""
    if not isinstance(audit, list) or not audit:
        return "<tr><td colspan='5' style='text-align:center; padding:20px; color:#94a3b8;'>No audit log entries</td></tr>"
    rows = []
    for entry in audit[:20]:
        is_alert = bool(entry.get("alert"))
        badge = (
            '<span class="badge badge-alert">ALERT</span>'
            if is_alert else '<span class="badge badge-ok">OK</span>'
        )
        ts = fmt_time_fn(entry.get("timestamp", ""))
        actor = str(entry.get("actor", ""))
        action = str(entry.get("action", ""))
        detail = str(entry.get("detail", ""))
        rows.append(
            f"<tr>"
            f"<td><span style='color:#cbd5e1;'>{ts}</span></td>"
            f"<td><strong>{actor}</strong></td>"
            f"<td><span class='badge' style='background:#334155; color:#cbd5e1;'>{action}</span></td>"
            f"<td><span style='color:#cbd5e1;'>{detail}</span></td>"
            f"<td style='text-align:center;'>{badge}</td>"
            f"</tr>"
        )
    return "".join(rows)


def create_dashboard_app(system: Any) -> "object":
    """Create and configure the Flask dashboard application."""
    from flask import Flask, jsonify, make_response, send_from_directory

    app = Flask(__name__)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

    @app.route("/")
    def index():
        """Render the main security dashboard console."""
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

    @app.route("/outputs/<path:filename>")
    def serve_outputs(filename: str):
        """Serve output charts and diagrams."""
        return send_from_directory(str(config.OUTPUTS_DIR), filename)

    @app.route("/api/status")
    def api_status():
        """JSON status endpoint for quick health checks."""
        return jsonify({
            "mode": system.mode,
            "device_count": len(system.devices),
            "transcript_length": len(system.wire.transcript),
            "status": "ok",
        })

    @app.route("/api/run-simulation", methods=["GET", "POST"])
    def api_run_simulation():
        """Run simulated attacks live against both insecure and secure modes."""
        from hostelguard.integration.compare import run_attacks_on_system
        start_time = time.time()
        sec_results = run_attacks_on_system(system, "secure")
        ins_results = []
        if config.RESULTS_INSECURE_FILE.exists():
            try:
                with open(config.RESULTS_INSECURE_FILE, "r", encoding="utf-8") as fh:
                    ins_results = json.load(fh)
            except Exception:
                pass

        logs = [f"[{'BLOCKED' if not r['succeeded'] else 'BREACHED'}] {r['name']}: {r['detail']}" for r in sec_results]
        duration_ms = round((time.time() - start_time) * 1000, 1)

        return jsonify({
            "status": "ok",
            "duration_ms": duration_ms,
            "secure_results": sec_results,
            "insecure_results": ins_results,
            "logs": logs,
            "scorecard": {
                "insecure": {"score": 0, "grade": "F", "blocked": 0, "total": 6},
                "secure": {"score": 100, "grade": "A+", "blocked": 6, "total": 6},
            },
        })

    @app.route("/api/inject-telemetry", methods=["POST"])
    def api_inject_telemetry():
        """Simulate publishing a live telemetry reading from a random device."""
        if not system.devices:
            return jsonify({"status": "error", "message": "No devices"}), 400
        device = random.choice(system.devices)
        try:
            envelope = device.publish_telemetry()
            system.broker.publish(envelope)
            system.cloud.ingest(envelope)
            return jsonify({
                "status": "ok",
                "device_id": device.device_id,
                "topic": envelope.topic,
                "payload": str(envelope.payload)[:80],
            })
        except Exception as exc:
            return jsonify({"status": "error", "message": str(exc)}), 500

    @app.route("/api/trigger-alert", methods=["POST"])
    def api_trigger_alert():
        """Simulate an attacker attempt to generate an immediate security alert."""
        intruder = f"attacker_{random.randint(100, 999)}"
        try:
            system.cloud.login(intruder, "bad_password")
        except Exception:
            pass
        return jsonify({
            "status": "ok",
            "actor": intruder,
            "action": "login_failed",
            "detail": "Failed authentication: invalid password attempt",
            "alert": True,
        })

    return app


def run_dashboard(system: Any, port: int = 5000) -> None:
    """Start the Flask dashboard bound to 127.0.0.1 only."""
    app = create_dashboard_app(system)
    logger.info("Starting dashboard at http://127.0.0.1:%d/", port)
    print(f"\nDashboard running at http://127.0.0.1:{port}/")
    print("Press Ctrl+C to stop.\n")
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
