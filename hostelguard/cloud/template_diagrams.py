"""
hostelguard/cloud/template_diagrams.py
Architecture and Threat Models gallery template.
"""

TEMPLATE_DIAGRAMS = """
<div id="tab-diagrams" class="tab-content">
  <div class="card">
    <div class="card-header">
      <div>
        <div class="card-title">1. System Architecture Diagram</div>
        <div class="card-subtitle">Layered simulation topology: Sensors, Virtual Wire, Secure Broker, Cloud Storage, and Admin Console</div>
      </div>
      <a href="/outputs/architecture.png" target="_blank" class="btn btn-primary" style="text-decoration:none;">View PNG</a>
    </div>
    <div style="text-align: center; padding: 10px;">
      <img src="/outputs/architecture.png" alt="Architecture Diagram" style="max-width: 100%; height: auto; border-radius: 8px; border: 1px solid #334155;">
    </div>
  </div>

  <div class="grid-2">
    <div class="card">
      <div class="card-header">
        <div>
          <div class="card-title">2. Attack Tree Analysis</div>
          <div class="card-subtitle">Hierarchical decomposition of adversary attack paths against the hostel IoT network</div>
        </div>
        <a href="/outputs/attack_tree.png" target="_blank" class="btn btn-primary" style="text-decoration:none;">View PNG</a>
      </div>
      <div style="text-align: center; padding: 8px;">
        <img src="/outputs/attack_tree.png" alt="Attack Tree" style="max-width: 100%; height: auto; border-radius: 8px; border: 1px solid #334155;">
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <div>
          <div class="card-title">3. Fault Tree Analysis</div>
          <div class="card-subtitle">Safety-critical failure analysis showing root causes for unauthorized physical access</div>
        </div>
        <a href="/outputs/fault_tree.png" target="_blank" class="btn btn-primary" style="text-decoration:none;">View PNG</a>
      </div>
      <div style="text-align: center; padding: 8px;">
        <img src="/outputs/fault_tree.png" alt="Fault Tree" style="max-width: 100%; height: auto; border-radius: 8px; border: 1px solid #334155;">
      </div>
    </div>
  </div>

  <div class="grid-2">
    <div class="card">
      <div class="card-header">
        <div>
          <div class="card-title">4. Cipher Benchmark: AES-256-GCM vs ChaCha20</div>
          <div class="card-subtitle">Empirical speed and latency evaluation across various simulated payload sizes</div>
        </div>
        <a href="/outputs/cipher_comparison.png" target="_blank" class="btn btn-primary" style="text-decoration:none;">View PNG</a>
      </div>
      <div style="text-align: center; padding: 8px;">
        <img src="/outputs/cipher_comparison.png" alt="Cipher Comparison" style="max-width: 100%; height: auto; border-radius: 8px; border: 1px solid #334155;">
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <div>
          <div class="card-title">5. Privacy Preservation Techniques</div>
          <div class="card-subtitle">Evaluation of Laplace differential privacy noise and k-anonymity across sensor streams</div>
        </div>
        <a href="/outputs/privacy_comparison.png" target="_blank" class="btn btn-primary" style="text-decoration:none;">View PNG</a>
      </div>
      <div style="text-align: center; padding: 8px;">
        <img src="/outputs/privacy_comparison.png" alt="Privacy Comparison" style="max-width: 100%; height: auto; border-radius: 8px; border: 1px solid #334155;">
      </div>
    </div>
  </div>
</div>
"""
