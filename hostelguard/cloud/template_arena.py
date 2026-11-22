"""
hostelguard/cloud/template_arena.py
Interactive Attack Arena and Security Scorecard templates for live demonstrations.
"""

TEMPLATE_ARENA = """
<div id="tab-arena" class="tab-content">
  <div class="card" style="border: 1px solid #3b82f6;">
    <div class="card-header">
      <div>
        <div class="card-title">Live Attack & Defense Simulation Arena</div>
        <div class="card-subtitle">Execute simulated attacks live against both insecure and secure system pipelines</div>
      </div>
      <button id="btn-run-sim" class="btn btn-success" onclick="runLiveSimulation()">▶ Run Live Attack Demo</button>
    </div>
    <div style="margin-bottom: 16px;">
      <div style="font-size: 12px; font-weight: 600; color: #94a3b8; margin-bottom: 6px;">LIVE SIMULATION TERMINAL CONSOLE</div>
      <div id="attack-console" class="console-box">System idle. Click "Run Live Attack Demo" to execute all 6 simulated cyber attacks...</div>
    </div>
  </div>

  <div class="card">
    <div class="card-header">
      <div>
        <div class="card-title">Attack Defense Matrix (6 Threat Vectors)</div>
        <div class="card-subtitle">Real-time before vs after comparison for all evaluated IoT attack vectors</div>
      </div>
    </div>
    <div class="table-responsive">
      <table>
        <thead>
          <tr>
            <th style="width: 170px;">Attack Vector</th>
            <th style="width: 140px;">Target Layer</th>
            <th style="width: 130px;">Insecure System</th>
            <th style="width: 130px;">Secure System</th>
            <th>Defense & Mitigation Mechanism</th>
          </tr>
        </thead>
        <tbody>
          <tr id="attack-row-Replay_Attack">
            <td><strong>Replay Attack</strong></td>
            <td><span class="device-tag">Virtual Wire</span></td>
            <td><span class="badge badge-breached">BREACHED</span></td>
            <td class="status-cell"><span class="badge badge-blocked">BLOCKED</span></td>
            <td>Monotonic sequence counter + 30s freshness window rejects duplicates.</td>
          </tr>
          <tr id="attack-row-Spoofing_Attack">
            <td><strong>Spoofing Attack</strong></td>
            <td><span class="device-tag">Broker Gateway</span></td>
            <td><span class="badge badge-breached">BREACHED</span></td>
            <td class="status-cell"><span class="badge badge-blocked">BLOCKED</span></td>
            <td>HMAC-SHA256 message tag & ECDSA sender attribution verifies identity.</td>
          </tr>
          <tr id="attack-row-Brute_Force_Attack">
            <td><strong>Brute Force</strong></td>
            <td><span class="device-tag">Cloud Auth</span></td>
            <td><span class="badge badge-breached">BREACHED</span></td>
            <td class="status-cell"><span class="badge badge-blocked">BLOCKED</span></td>
            <td>Bcrypt adaptive hashing (cost 12) + 5-attempt progressive lockout.</td>
          </tr>
          <tr id="attack-row-Flooding__DoS__Attack">
            <td><strong>Flooding (DoS)</strong></td>
            <td><span class="device-tag">Broker Buffer</span></td>
            <td><span class="badge badge-breached">BREACHED</span></td>
            <td class="status-cell"><span class="badge badge-blocked">BLOCKED</span></td>
            <td>Token-bucket rate limiter throttles traffic bursts and drops excess.</td>
          </tr>
          <tr id="attack-row-Sniffing_Attack">
            <td><strong>Wire Sniffing</strong></td>
            <td><span class="device-tag">Virtual Wire</span></td>
            <td><span class="badge badge-breached">BREACHED</span></td>
            <td class="status-cell"><span class="badge badge-blocked">BLOCKED</span></td>
            <td>AES-256-GCM symmetric encryption conceals payload in random ciphertext.</td>
          </tr>
          <tr id="attack-row-Tampering_Attack">
            <td><strong>Payload Tampering</strong></td>
            <td><span class="device-tag">Wire / Integrity</span></td>
            <td><span class="badge badge-breached">BREACHED</span></td>
            <td class="status-cell"><span class="badge badge-blocked">BLOCKED</span></td>
            <td>Any bit change breaks the 32-byte HMAC integrity verification.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</div>

<div id="tab-benchmark" class="tab-content">
  <div class="grid-2" style="margin-bottom: 20px;">
    <div class="card" style="border: 1px solid #ef4444;">
      <div style="font-size: 13px; font-weight: 700; color: #f87171; text-transform: uppercase;">Baseline Insecure Mode</div>
      <div style="font-size: 38px; font-weight: 800; color: #ef4444; margin: 8px 0;">0 / 100 <span style="font-size: 20px;">(Grade F)</span></div>
      <p style="font-size: 13px; color: #cbd5e1; line-height: 1.5;">Defenseless baseline. 6 out of 6 attacks succeeded. Plaintext on wire, unauthenticated broker, plain SQL storage, and no rate limits.</p>
    </div>
    <div class="card" style="border: 1px solid #10b981;">
      <div style="font-size: 13px; font-weight: 700; color: #34d399; text-transform: uppercase;">Hardened Secure Mode</div>
      <div style="font-size: 38px; font-weight: 800; color: #10b981; margin: 8px 0;">100 / 100 <span style="font-size: 20px;">(Grade A+)</span></div>
      <p style="font-size: 13px; color: #cbd5e1; line-height: 1.5;">Fully defended. 6 out of 6 attacks blocked. Complete cryptographic defense: AES-GCM, HMAC, ECDSA, JWT, RBAC, and tamper logging.</p>
    </div>
  </div>

  <div class="card">
    <div class="card-header">
      <div>
        <div class="card-title">Before vs After Attack Success Comparison Chart</div>
        <div class="card-subtitle">Empirical validation chart generated by matplotlib during security benchmarking</div>
      </div>
      <a href="/outputs/comparison_chart.png" target="_blank" class="btn btn-primary" style="text-decoration:none;">Open High-Res PNG</a>
    </div>
    <div style="text-align: center; padding: 10px;">
      <img src="/outputs/comparison_chart.png" alt="Comparison Chart" style="max-width: 100%; height: auto; border-radius: 8px; border: 1px solid #334155;">
    </div>
  </div>
</div>
"""
