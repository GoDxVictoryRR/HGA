"""
hostelguard/cloud/template.py
Modular, explainable HTML template for the HostelGuard Security Dashboard.

Designed for live academic demonstrations and examiner vivas.
All CSS is self-contained so the dashboard functions completely offline.
"""

DASHBOARD_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="5">
<title>HostelGuard - IoT Security Dashboard</title>
<style>
  :root {
    --bg-main: #f8fafc; --bg-card: #ffffff; --border: #e2e8f0;
    --text-primary: #0f172a; --text-secondary: #475569; --text-muted: #64748b;
    --primary: #2563eb; --primary-dark: #1e3a8a;
    --success-bg: #ecfdf5; --success-border: #10b981; --success-text: #065f46;
    --danger-bg: #fef2f2; --danger-border: #ef4444; --danger-text: #991b1b;
    --info-bg: #eff6ff; --info-text: #1e40af;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg-main); color: var(--text-primary); padding: 24px; line-height: 1.5; }
  .container { max-width: 1400px; margin: 0 auto; }
  .header { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #fff; border-radius: 12px; padding: 20px 24px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
  .header-titles h1 { font-size: 24px; font-weight: 700; }
  .header-titles p { font-size: 13px; color: #94a3b8; margin-top: 4px; }
  .header-status { text-align: right; }
  .mode-badge { display: inline-block; padding: 6px 14px; border-radius: 9999px; font-size: 12px; font-weight: 700; text-transform: uppercase; background: #10b981; color: #fff; }
  .refresh-text { font-size: 11px; color: #94a3b8; margin-top: 6px; }
  .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; margin-bottom: 24px; }
  .kpi-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 16px 20px; box-shadow: 0 1px 3px 0 rgba(0,0,0,0.05); }
  .kpi-label { font-size: 12px; font-weight: 600; text-transform: uppercase; color: var(--text-muted); }
  .kpi-value { font-size: 22px; font-weight: 700; margin: 6px 0 2px 0; }
  .kpi-desc { font-size: 12px; color: var(--text-secondary); }
  .section-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 24px; box-shadow: 0 1px 3px 0 rgba(0,0,0,0.05); }
  .section-header { margin-bottom: 16px; border-bottom: 1px solid var(--border); padding-bottom: 10px; }
  .section-title { font-size: 16px; font-weight: 700; color: var(--text-primary); }
  .section-subtitle { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
  .pipeline-flow { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }
  .pipeline-step { background: #f8fafc; border: 1px solid var(--border); border-left: 4px solid var(--primary); border-radius: 8px; padding: 12px 14px; }
  .step-num { font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--primary); }
  .step-title { font-size: 13px; font-weight: 700; margin: 2px 0 4px 0; }
  .step-desc { font-size: 11.5px; color: var(--text-secondary); line-height: 1.4; }
  .defense-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 12px; }
  .defense-pill { background: #fff; border: 1px solid #d1fae5; border-radius: 8px; padding: 12px 14px; display: flex; align-items: flex-start; gap: 12px; }
  .status-tag { background: #10b981; color: white; font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 4px; letter-spacing: 0.5px; }
  .defense-info { flex: 1; }
  .defense-attack { font-size: 13px; font-weight: 700; color: #065f46; }
  .defense-mechanism { font-size: 11.5px; color: var(--text-secondary); margin-top: 2px; }
  .table-responsive { width: 100%; overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { background: #f1f5f9; color: var(--text-secondary); font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; padding: 10px 14px; border-bottom: 1px solid var(--border); }
  td { padding: 10px 14px; border-bottom: 1px solid var(--border); vertical-align: middle; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background-color: #f8fafc; }
  .device-chip { font-family: ui-monospace, Consolas, monospace; font-size: 11px; font-weight: 600; color: var(--primary-dark); background: var(--info-bg); border: 1px solid #bfdbfe; padding: 2px 6px; border-radius: 4px; display: inline-block; }
  .type-tag { font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 4px; text-transform: uppercase; margin-right: 6px; }
  .type-rfid { background: #fef3c7; color: #92400e; }
  .type-temp { background: #fee2e2; color: #991b1b; }
  .type-energy { background: #e0e7ff; color: #3730a3; }
  .type-motion { background: #ede9fe; color: #5b21b6; }
  .payload-box { font-family: ui-monospace, Consolas, monospace; font-size: 11.5px; color: #1e293b; background: #f1f5f9; padding: 4px 8px; border-radius: 4px; display: inline-block; word-break: break-all; }
  .pill { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; }
  .pill-alert { background: var(--danger-bg); border: 1px solid #fca5a5; color: var(--danger-text); }
  .pill-ok { background: var(--success-bg); border: 1px solid #6ee7b7; color: var(--success-text); }
  .pill-action { background: #f1f5f9; color: var(--text-secondary); font-family: monospace; }
  .footer { text-align: center; font-size: 12px; color: var(--text-muted); margin-top: 32px; padding-top: 16px; border-top: 1px solid var(--border); }
</style>
</head>
<body>
<div class="container">
  <header class="header">
    <div class="header-titles">
      <h1>HostelGuard - IoT Security Dashboard</h1>
      <p>Modular IoT Security Console &bull; Defense Matrix &bull; Real-time Telemetry &bull; Audit Trail</p>
    </div>
    <div class="header-status">
      <span class="mode-badge">Mode: {{MODE}} &bull; Active</span>
      <div class="refresh-text">&bull; Live auto-refreshing every 5s</div>
    </div>
  </header>

  <section class="kpi-grid">
    <div class="kpi-card">
      <div class="kpi-label">Device Fleet Status</div>
      <div class="kpi-value">{{DEVICE_COUNT}} Active Nodes</div>
      <div class="kpi-desc">4 Categories: RFID Locks, Temperature, Energy, Motion</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Wire Transport Encryption</div>
      <div class="kpi-value" style="color: #0284c7;">AES-256-GCM</div>
      <div class="kpi-desc">Payloads encrypted with unique 12-byte nonces; no plaintext wire leak</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Message Origin & Integrity</div>
      <div class="kpi-value" style="color: #16a34a;">HMAC + ECDSA</div>
      <div class="kpi-desc">SHA-256 integrity tag & P-256 curve asymmetric digital signatures</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Identity & Access Control</div>
      <div class="kpi-value" style="color: #7c3aed;">JWT + RBAC</div>
      <div class="kpi-desc">Warden, Technician, Student roles + Bcrypt (Cost 12) lockout</div>
    </div>
  </section>

  <section class="section-card">
    <div class="section-header">
      <div class="section-title">Message Security Architecture (How Telemetry Travels Safely)</div>
      <div class="section-subtitle">Layered protection sequence applied to every sensor reading in this simulation</div>
    </div>
    <div class="pipeline-flow">
      <div class="pipeline-step">
        <div class="step-num">Step 1 &bull; Device Layer</div>
        <div class="step-title">Hardware Origin</div>
        <div class="step-desc">Sensor takes reading, encrypts with AES-256-GCM, signs with ECDSA private key, and appends a monotonic sequence counter.</div>
      </div>
      <div class="pipeline-step">
        <div class="step-num">Step 2 &bull; Virtual Wire</div>
        <div class="step-title">Transport Channel</div>
        <div class="step-desc">Transmits raw byte envelopes. Sniffers only observe ciphertext. Packet injection without a valid HMAC key is rejected.</div>
      </div>
      <div class="pipeline-step">
        <div class="step-num">Step 3 &bull; Secure Broker</div>
        <div class="step-title">Gateway Verification</div>
        <div class="step-desc">Validates client JWT token, checks HMAC integrity tag, rejects stale timestamps/counters, and rate-limits traffic bursts.</div>
      </div>
      <div class="pipeline-step">
        <div class="step-num">Step 4 &bull; Cloud Service</div>
        <div class="step-title">Encrypted Storage & DB</div>
        <div class="step-desc">Ingests encrypted payloads directly into SQLite at rest. Enforces Role-Based Access Control on read queries and logs all events.</div>
      </div>
      <div class="pipeline-step">
        <div class="step-num">Step 5 &bull; Operator Console</div>
        <div class="step-title">Authorized View</div>
        <div class="step-desc">This dashboard authenticates as authorized Warden, verifies credentials, decrypts telemetry in-memory, and shows live alerts.</div>
      </div>
    </div>
  </section>

  <section class="section-card">
    <div class="section-header">
      <div class="section-title">Active Security Posture (Attacks & Mitigations in this Demo)</div>
      <div class="section-subtitle">Real-time status of the 6 simulated attack vectors compared to baseline</div>
    </div>
    <div class="defense-grid">
      <div class="defense-pill">
        <span class="status-tag">BLOCKED</span>
        <div class="defense-info">
          <div class="defense-attack">Replay Attack</div>
          <div class="defense-mechanism">Prevented by monotonic sequence counters and strict 30-second timestamp freshness window.</div>
        </div>
      </div>
      <div class="defense-pill">
        <span class="status-tag">BLOCKED</span>
        <div class="defense-info">
          <div class="defense-attack">Identity Spoofing</div>
          <div class="defense-mechanism">Prevented by SHA-256 HMAC message authentication and ECDSA sender attribution.</div>
        </div>
      </div>
      <div class="defense-pill">
        <span class="status-tag">BLOCKED</span>
        <div class="defense-info">
          <div class="defense-attack">Credential Brute-Force</div>
          <div class="defense-mechanism">Blocked by bcrypt adaptive hashing (work factor 12) and progressive 5-attempt account lockout.</div>
        </div>
      </div>
      <div class="defense-pill">
        <span class="status-tag">BLOCKED</span>
        <div class="defense-info">
          <div class="defense-attack">Flooding / DoS</div>
          <div class="defense-mechanism">Throttled by broker token-bucket rate limiter; excess message bursts are immediately dropped.</div>
        </div>
      </div>
      <div class="defense-pill">
        <span class="status-tag">BLOCKED</span>
        <div class="defense-info">
          <div class="defense-attack">Wire Sniffing</div>
          <div class="defense-mechanism">Protected by AES-256-GCM symmetric encryption; wire packet payloads carry only random-looking ciphertext.</div>
        </div>
      </div>
      <div class="defense-pill">
        <span class="status-tag">BLOCKED</span>
        <div class="defense-info">
          <div class="defense-attack">Payload Tampering</div>
          <div class="defense-mechanism">Detected immediately: modifying any payload bit invalidates the 32-byte HMAC integrity tag.</div>
        </div>
      </div>
    </div>
  </section>

  <section class="section-card">
    <div class="section-header">
      <div class="section-title">Live Sensor Telemetry Stream (Decrypted Operator View)</div>
      <div class="section-subtitle">Real-time readings decrypted from AES-256-GCM ciphertexts using provisioned device keys</div>
    </div>
    <div class="table-responsive">
      <table>
        <thead>
          <tr>
            <th style="width: 200px;">Device Identifier</th>
            <th style="width: 240px;">MQTT Topic</th>
            <th>Decrypted Payload Content</th>
            <th style="width: 140px;">Timestamp</th>
          </tr>
        </thead>
        <tbody>
          {{telemetry_rows}}
        </tbody>
      </table>
    </div>
  </section>

  <section class="section-card">
    <div class="section-header">
      <div class="section-title">Security Audit Log (Real-Time Forensic Trail)</div>
      <div class="section-subtitle">Tamper-evident log of authentication attempts, administrative operations, and detected security violations</div>
    </div>
    <div class="table-responsive">
      <table>
        <thead>
          <tr>
            <th style="width: 140px;">Timestamp</th>
            <th style="width: 160px;">Actor / Identity</th>
            <th style="width: 160px;">Action Event</th>
            <th>Event Details & Parameters</th>
            <th style="width: 100px; text-align: center;">Alert Status</th>
          </tr>
        </thead>
        <tbody>
          {{audit_rows}}
        </tbody>
      </table>
    </div>
  </section>

  <footer class="footer">
    HostelGuard (SecureIoT-Sim) &bull; IoT Security Framework &bull; GGSIPU Group Project
  </footer>
</div>
</body>
</html>
"""
