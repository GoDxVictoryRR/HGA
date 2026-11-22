"""
tests/test_dashboard.py
Unit and route tests for the Flask-based IoT security dashboard.
"""

from hostelguard.cloud.dashboard import create_dashboard_app
from hostelguard.integration.runner import run_normal_traffic


def test_dashboard_routes_insecure(insecure_sys):
    """Test dashboard index and api/status on insecure system."""
    run_normal_traffic(insecure_sys)
    app = create_dashboard_app(insecure_sys)
    app.config["TESTING"] = True
    client = app.test_client()

    resp = client.get("/")
    assert resp.status_code == 200
    assert b"HostelGuard - IoT Security Dashboard" in resp.data
    assert b"insecure" in resp.data

    api_resp = client.get("/api/status")
    assert api_resp.status_code == 200
    json_data = api_resp.get_json()
    assert json_data["mode"] == "insecure"
    assert json_data["status"] == "ok"
    assert json_data["device_count"] == len(insecure_sys.devices)


def test_dashboard_routes_secure(secure_sys):
    """Test dashboard index and api/status on secure system."""
    run_normal_traffic(secure_sys)
    app = create_dashboard_app(secure_sys)
    app.config["TESTING"] = True
    client = app.test_client()

    resp = client.get("/")
    assert resp.status_code == 200
    assert b"HostelGuard - IoT Security Dashboard" in resp.data
    assert b"secure" in resp.data

    api_resp = client.get("/api/status")
    assert api_resp.status_code == 200
    json_data = api_resp.get_json()
    assert json_data["mode"] == "secure"
    assert json_data["status"] == "ok"

    # Test interactive API endpoints
    sim_resp = client.post("/api/run-simulation")
    assert sim_resp.status_code == 200
    sim_data = sim_resp.get_json()
    assert sim_data["status"] == "ok"
    assert "scorecard" in sim_data
    assert sim_data["scorecard"]["secure"]["blocked"] == 6

    inj_resp = client.post("/api/inject-telemetry")
    assert inj_resp.status_code == 200
    assert inj_resp.get_json()["status"] == "ok"

    alert_resp = client.post("/api/trigger-alert")
    assert alert_resp.status_code == 200
    assert alert_resp.get_json()["status"] == "ok"

    chart_resp = client.get("/outputs/comparison_chart.png")
    assert chart_resp.status_code in (200, 404)
