"""
hostelguard/cloud/dashboard.py
Simple Flask dashboard for the HostelGuard cloud service.

Serves a minimal HTML page at http://127.0.0.1:5000/ showing:
- Recent telemetry readings (decrypted)
- Audit log entries and alerts
- System status

The server binds to 127.0.0.1 ONLY (never 0.0.0.0).
Start it with: python main.py --mode secure --serve
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# HTML template for the dashboard — inline for simplicity, ASCII only
_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>HostelGuard Dashboard</title>
<style>
  body {{ font-family: Arial, sans-serif; background: #f0f4f8; color: #1a202c; margin: 0; padding: 20px; }}
  h1 {{ background: #1e3a5f; color: white; padding: 16px; margin: -20px -20px 20px; }}
  h2 {{ color: #2563eb; border-bottom: 2px solid #2563eb; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
  th {{ background: #2563eb; color: white; padding: 8px; text-align: left; }}
  td {{ padding: 6px 8px; border-bottom: 1px solid #e2e8f0; }}
  tr:nth-child(even) {{ background: #f7fafc; }}
  .alert {{ background: #fff5f5; border-left: 4px solid #e53e3e; padding: 8px; margin: 4px 0; }}
  .ok {{ background: #f0fff4; border-left: 4px solid #38a169; padding: 8px; margin: 4px 0; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold; }}
  .badge-red {{ background: #fed7d7; color: #c53030; }}
  .badge-green {{ background: #c6f6d5; color: #276749; }}
</style>
</head>
<body>
<h1>HostelGuard - IoT Security Dashboard</h1>
<h2>System Status</h2>
<div class="ok">Mode: <strong>{mode}</strong> | Devices: <strong>{device_count}</strong></div>
<h2>Recent Telemetry</h2>
<table>
  <tr><th>Device</th><th>Topic</th><th>Reading</th><th>Time</th></tr>
  {telemetry_rows}
</table>
<h2>Audit Log (last 20 entries)</h2>
<table>
  <tr><th>Time</th><th>Actor</th><th>Action</th><th>Detail</th><th>Alert</th></tr>
  {audit_rows}
</table>
</body>
</html>"""


def create_dashboard_app(system: Any) -> "object":
    """Create and return the Flask dashboard application.

    system : SystemContainer with cloud and devices attributes.
    """
    try:
        from flask import Flask
    except ImportError as exc:
        raise RuntimeError("Flask is required for the dashboard: pip install Flask") from exc

    app = Flask(__name__)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

    @app.route("/")
    def index():
        """Main dashboard page."""
        from flask import make_response
        import datetime

        # Gather telemetry (use a warden token so we get all data)
        telemetry = []
        try:
            token = system.cloud.login("warden", "warden123")
            telemetry = system.cloud.query(token, {})
        except Exception as exc:
            logger.warning("Dashboard: could not fetch telemetry: %s", exc)

        def _fmt_time(ts):
            try:
                return datetime.datetime.fromtimestamp(float(ts), datetime.timezone.utc).strftime("%H:%M:%S")
            except Exception:
                return str(ts)

        trows = ""
        for row in telemetry[:20]:
            payload_text = row.get("payload_plaintext", row.get("payload", ""))
            trows += (
                f"<tr><td>{row.get('device_id','')}</td>"
                f"<td>{row.get('topic','')}</td>"
                f"<td>{str(payload_text)[:80]}</td>"
                f"<td>{_fmt_time(row.get('timestamp',''))}</td></tr>"
            )
        if not trows:
            trows = "<tr><td colspan='4'>No telemetry yet</td></tr>"

        # Gather audit log if available
        audit_rows = ""
        try:
            token = system.cloud.login("warden", "warden123")
            audit = system.cloud.admin(token, "get_audit_log", {})
            for entry in audit[:20]:
                badge = (
                    '<span class="badge badge-red">ALERT</span>'
                    if entry.get("alert")
                    else '<span class="badge badge-green">OK</span>'
                )
                audit_rows += (
                    f"<tr><td>{_fmt_time(entry.get('timestamp',''))}</td>"
                    f"<td>{entry.get('actor','')}</td>"
                    f"<td>{entry.get('action','')}</td>"
                    f"<td>{entry.get('detail','')}</td>"
                    f"<td>{badge}</td></tr>"
                )
        except Exception:
            pass
        if not audit_rows:
            audit_rows = "<tr><td colspan='5'>No audit log entries</td></tr>"

        html = _HTML_TEMPLATE.format(
            mode=system.mode,
            device_count=len(system.devices),
            telemetry_rows=trows,
            audit_rows=audit_rows,
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
    """Start the Flask dashboard.  Binds to 127.0.0.1 only."""
    app = create_dashboard_app(system)
    logger.info("Starting dashboard at http://127.0.0.1:%d/", port)
    print(f"\nDashboard running at http://127.0.0.1:{port}/")
    print("Press Ctrl+C to stop.\n")
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
