"""
hostelguard/cloud/template_ops.py
Operations console template showing live system KPIs, pipeline, telemetry, and audit log.
"""

TEMPLATE_OPS = """
<div id="tab-ops" class="tab-content active">
  <div class="grid-4" style="margin-bottom: 20px;">
    <div class="stat-card">
      <div style="font-size: 11px; text-transform: uppercase; color: var(--text-muted);">Fleet Nodes</div>
      <div class="stat-val" style="color: #60a5fa;">{{DEVICE_COUNT}} Active</div>
      <div style="font-size: 11px; color: var(--text-muted);">RFID, Temp, Energy, Motion</div>
    </div>
    <div class="stat-card">
      <div style="font-size: 11px; text-transform: uppercase; color: var(--text-muted);">Wire Encryption</div>
      <div class="stat-val" style="color: #38bdf8;">AES-256-GCM</div>
      <div style="font-size: 11px; color: var(--text-muted);">12-Byte Nonce & Authenticated Tag</div>
    </div>
    <div class="stat-card">
      <div style="font-size: 11px; text-transform: uppercase; color: var(--text-muted);">Origin & Integrity</div>
      <div class="stat-val" style="color: #4ade80;">HMAC + ECDSA</div>
      <div style="font-size: 11px; color: var(--text-muted);">P-256 Curve Asymmetric Signatures</div>
    </div>
    <div class="stat-card">
      <div style="font-size: 11px; text-transform: uppercase; color: var(--text-muted);">Identity & Access</div>
      <div class="stat-val" style="color: #c084fc;">JWT + RBAC</div>
      <div style="font-size: 11px; color: var(--text-muted);">Bcrypt (Cost 12) + Account Lockout</div>
    </div>
  </div>

  <div class="card">
    <div class="card-header">
      <div>
        <div class="card-title">Message Security Architecture (How Telemetry Travels Safely)</div>
        <div class="card-subtitle">5-step defense sequence applied to every simulated sensor packet</div>
      </div>
    </div>
    <div class="grid-4" style="grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));">
      <div style="background: #111827; border-left: 3px solid #3b82f6; border-radius: 6px; padding: 12px;">
        <div style="font-size: 10px; font-weight: 700; color: #3b82f6;">STEP 1 &bull; DEVICE</div>
        <div style="font-size: 13px; font-weight: 700; margin: 2px 0;">Hardware Origin</div>
        <div style="font-size: 11px; color: #94a3b8;">Encrypts reading with AES-GCM, signs with ECDSA, attaches monotonic sequence.</div>
      </div>
      <div style="background: #111827; border-left: 3px solid #06b6d4; border-radius: 6px; padding: 12px;">
        <div style="font-size: 10px; font-weight: 700; color: #06b6d4;">STEP 2 &bull; WIRE</div>
        <div style="font-size: 13px; font-weight: 700; margin: 2px 0;">Transport Channel</div>
        <div style="font-size: 11px; color: #94a3b8;">Sniffers see only ciphertext bytes. Packet injection without keys is rejected.</div>
      </div>
      <div style="background: #111827; border-left: 3px solid #10b981; border-radius: 6px; padding: 12px;">
        <div style="font-size: 10px; font-weight: 700; color: #10b981;">STEP 3 &bull; BROKER</div>
        <div style="font-size: 13px; font-weight: 700; margin: 2px 0;">Gateway Verification</div>
        <div style="font-size: 11px; color: #94a3b8;">Verifies device JWT, validates HMAC tag, enforces freshness and token-bucket rate limit.</div>
      </div>
      <div style="background: #111827; border-left: 3px solid #a855f7; border-radius: 6px; padding: 12px;">
        <div style="font-size: 10px; font-weight: 700; color: #a855f7;">STEP 4 &bull; CLOUD</div>
        <div style="font-size: 13px; font-weight: 700; margin: 2px 0;">Encrypted Storage</div>
        <div style="font-size: 11px; color: #94a3b8;">Stores encrypted telemetry in SQLite. RBAC protects queries; logs forensic events.</div>
      </div>
      <div style="background: #111827; border-left: 3px solid #f59e0b; border-radius: 6px; padding: 12px;">
        <div style="font-size: 10px; font-weight: 700; color: #f59e0b;">STEP 5 &bull; OPERATOR</div>
        <div style="font-size: 13px; font-weight: 700; margin: 2px 0;">Authorized Console</div>
        <div style="font-size: 11px; color: #94a3b8;">Authenticates with Warden JWT, decrypts telemetry in memory, and audits violations.</div>
      </div>
    </div>
  </div>

  <div class="card">
    <div class="card-header">
      <div>
        <div class="card-title">Live Decrypted Sensor Telemetry</div>
        <div class="card-subtitle">Real-time readings decrypted from AES-256-GCM ciphertexts</div>
      </div>
      <button class="btn btn-primary" onclick="injectTelemetry()">+ Send Live Sensor Reading</button>
    </div>
    <div class="table-responsive">
      <table>
        <thead>
          <tr>
            <th style="width: 220px;">Device Identifier</th>
            <th style="width: 240px;">MQTT Topic</th>
            <th>Decrypted Payload Content</th>
            <th style="width: 140px;">Timestamp</th>
          </tr>
        </thead>
        <tbody id="telemetry-tbody">
          {{TELEMETRY_ROWS}}
        </tbody>
      </table>
    </div>
  </div>

  <div class="card">
    <div class="card-header">
      <div>
        <div class="card-title">Forensic Audit Log & Security Alerts</div>
        <div class="card-subtitle">Tamper-evident trail of access checks, logins, and threat attempts</div>
      </div>
      <button class="btn btn-danger" onclick="triggerAlert()">⚡ Simulate Intruder Alert</button>
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
        <tbody id="audit-tbody">
          {{AUDIT_ROWS}}
        </tbody>
      </table>
    </div>
  </div>
</div>
"""
