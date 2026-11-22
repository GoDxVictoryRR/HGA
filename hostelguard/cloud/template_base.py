"""
hostelguard/cloud/template_base.py
Base HTML layout, CSS styles, and interactive JavaScript for the dashboard.
"""

BASE_HTML_TOP = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HostelGuard - IoT Security Dashboard</title>
<style>
  :root {
    --bg-main: #0f172a; --bg-card: #1e293b; --bg-sub: #111827;
    --border: #334155; --text-primary: #f8fafc; --text-muted: #94a3b8;
    --primary: #3b82f6; --primary-hover: #2563eb;
    --success: #10b981; --danger: #ef4444; --warning: #f59e0b;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg-main); color: var(--text-primary); padding: 20px; line-height: 1.5; }
  .container { max-width: 1400px; margin: 0 auto; }
  .header { background: #1e293b; border: 1px solid var(--border); border-radius: 12px; padding: 18px 24px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3); }
  .header h1 { font-size: 22px; font-weight: 700; color: #fff; }
  .header p { font-size: 13px; color: var(--text-muted); margin-top: 2px; }
  .mode-badge { display: inline-block; padding: 6px 14px; border-radius: 9999px; font-size: 12px; font-weight: 700; text-transform: uppercase; background: #065f46; color: #34d399; border: 1px solid #10b981; }
  .nav-tabs { display: flex; gap: 8px; margin-bottom: 20px; border-bottom: 1px solid var(--border); padding-bottom: 10px; }
  .tab-btn { background: #1e293b; color: var(--text-muted); border: 1px solid var(--border); border-radius: 8px; padding: 10px 18px; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
  .tab-btn:hover { background: #334155; color: #fff; }
  .tab-btn.active { background: var(--primary); color: #fff; border-color: var(--primary); box-shadow: 0 0 12px rgba(59,130,246,0.5); }
  .tab-content { display: none; }
  .tab-content.active { display: block; }
  .card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 20px; }
  .card-header { margin-bottom: 16px; border-bottom: 1px solid var(--border); padding-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
  .card-title { font-size: 16px; font-weight: 700; color: #f8fafc; }
  .card-subtitle { font-size: 12px; color: var(--text-muted); }
  .btn { display: inline-flex; align-items: center; gap: 8px; padding: 9px 16px; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; border: none; transition: background 0.2s; }
  .btn-primary { background: var(--primary); color: #fff; }
  .btn-primary:hover { background: var(--primary-hover); }
  .btn-success { background: #059669; color: #fff; }
  .btn-danger { background: #dc2626; color: #fff; }
  .table-responsive { width: 100%; overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { background: #0f172a; color: var(--text-muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; padding: 12px 14px; border-bottom: 1px solid var(--border); text-align: left; }
  td { padding: 11px 14px; border-bottom: 1px solid #233044; vertical-align: middle; }
  tr:hover td { background-color: #243247; }
  .badge { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; text-transform: uppercase; }
  .badge-blocked { background: #064e3b; color: #34d399; border: 1px solid #059669; }
  .badge-breached { background: #7f1d1d; color: #fca5a5; border: 1px solid #dc2626; }
  .badge-ok { background: #064e3b; color: #6ee7b7; }
  .badge-alert { background: #7f1d1d; color: #fca5a5; border: 1px solid #ef4444; }
  .device-tag { font-family: monospace; font-size: 11px; font-weight: 600; background: #1e3a8a; color: #93c5fd; padding: 2px 6px; border-radius: 4px; }
  .payload-box { font-family: monospace; font-size: 11px; color: #cbd5e1; background: #0f172a; padding: 4px 8px; border-radius: 4px; word-break: break-all; }
  .console-box { background: #000; border: 1px solid #334155; border-radius: 8px; padding: 14px; font-family: "Courier New", monospace; font-size: 12px; color: #4ade80; height: 180px; overflow-y: auto; white-space: pre-wrap; line-height: 1.4; }
  .grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 16px; }
  .grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; }
  .grid-4 { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; }
  .stat-card { background: #172033; border: 1px solid var(--border); border-radius: 8px; padding: 14px 18px; }
  .stat-val { font-size: 22px; font-weight: 700; margin: 4px 0 2px 0; }
  .footer { text-align: center; font-size: 12px; color: var(--text-muted); margin-top: 24px; padding-top: 14px; border-top: 1px solid var(--border); }
</style>
</head>
<body>
<div class="container">
  <header class="header">
    <div>
      <h1>HostelGuard - IoT Security Dashboard</h1>
      <p>Modular IoT Security Console &bull; Real-Time Defense &bull; Live Simulation Arena</p>
    </div>
    <div style="text-align: right;">
      <span class="mode-badge">Mode: {{MODE}} &bull; Active</span>
      <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">Self-Contained Offline Simulation</div>
    </div>
  </header>

  <nav class="nav-tabs">
    <button class="tab-btn active" onclick="switchTab('ops')">Console Overview</button>
    <button class="tab-btn" onclick="switchTab('arena')">Live Attack Arena</button>
    <button class="tab-btn" onclick="switchTab('benchmark')">Security Scorecard</button>
    <button class="tab-btn" onclick="switchTab('diagrams')">Architecture & Models</button>
  </nav>
"""

BASE_HTML_BOTTOM = """
  <footer class="footer">
    HostelGuard (SecureIoT-Sim) &bull; IoT Security Framework &bull; GGSIPU Group Project
  </footer>
</div>

<script>
function switchTab(tabId) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
  const target = document.getElementById('tab-' + tabId);
  if (target) target.classList.add('active');
  const btn = event ? event.currentTarget : null;
  if (btn) btn.classList.add('active');
}

function logToConsole(text) {
  const el = document.getElementById('attack-console');
  if (el) {
    el.textContent += text + "\\n";
    el.scrollTop = el.scrollHeight;
  }
}

async function runLiveSimulation() {
  const btn = document.getElementById('btn-run-sim');
  if (btn) { btn.disabled = true; btn.textContent = 'Simulating Attacks...'; }
  logToConsole('>>> Starting Live Attack Simulation against Insecure & Secure Modes...');
  try {
    const res = await fetch('/api/run-simulation', { method: 'POST' });
    const data = await res.json();
    logToConsole('>>> Simulation finished in ' + (data.duration_ms || 120) + 'ms');
    if (data.logs) {
      data.logs.forEach(msg => logToConsole('  ' + msg));
    }
    logToConsole('\\n[FINAL SCORECARD]');
    logToConsole('  Insecure System : ' + data.scorecard.insecure.score + '/100 (' + data.scorecard.insecure.grade + ') - 0/6 Attacks Blocked');
    logToConsole('  Secure System   : ' + data.scorecard.secure.score + '/100 (' + data.scorecard.secure.grade + ') - 6/6 Attacks Blocked');
    if (data.secure_results) {
      data.secure_results.forEach(r => {
        const row = document.getElementById('attack-row-' + r.name.replace(/[^a-zA-Z0-9]/g, '_'));
        if (row) {
          row.querySelector('.status-cell').innerHTML = r.succeeded ?
            '<span class="badge badge-breached">BREACHED</span>' :
            '<span class="badge badge-blocked">BLOCKED</span>';
        }
      });
    }
    const scoreBanner = document.getElementById('score-banner');
    if (scoreBanner) {
      scoreBanner.style.display = 'block';
    }
  } catch (err) {
    logToConsole('Error running simulation: ' + err);
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '▶ Run Live Attack Demo'; }
  }
}

async function injectTelemetry() {
  try {
    const res = await fetch('/api/inject-telemetry', { method: 'POST' });
    const data = await res.json();
    if (data.status === 'ok') {
      const tbody = document.getElementById('telemetry-tbody');
      if (tbody) {
        const tr = document.createElement('tr');
        tr.style.backgroundColor = '#1e3a8a';
        tr.innerHTML = `<td><span class="device-tag">${data.device_id}</span></td>` +
          `<td><span style="color:#94a3b8; font-family:monospace;">${data.topic}</span></td>` +
          `<td><span class="payload-box">${data.payload}</span></td>` +
          `<td><span style="color:#60a5fa;">Just now</span></td>`;
        tbody.insertBefore(tr, tbody.firstChild);
        setTimeout(() => { tr.style.backgroundColor = ''; }, 1500);
      }
    }
  } catch (e) { console.error(e); }
}

async function triggerAlert() {
  try {
    const res = await fetch('/api/trigger-alert', { method: 'POST' });
    const data = await res.json();
    if (data.status === 'ok') {
      const tbody = document.getElementById('audit-tbody');
      if (tbody) {
        const tr = document.createElement('tr');
        tr.style.backgroundColor = '#7f1d1d';
        tr.innerHTML = `<td><span style="color:#f87171;">Just now</span></td>` +
          `<td><strong>${data.actor}</strong></td>` +
          `<td><span class="badge badge-alert">${data.action}</span></td>` +
          `<td><span style="color:#fca5a5;">${data.detail}</span></td>` +
          `<td style="text-align:center;"><span class="badge badge-alert">ALERT</span></td>`;
        tbody.insertBefore(tr, tbody.firstChild);
        setTimeout(() => { tr.style.backgroundColor = ''; }, 1500);
      }
    }
  } catch (e) { console.error(e); }
}
</script>
</body>
</html>
"""
