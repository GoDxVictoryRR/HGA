# HostelGuard (SecureIoT-Sim)

**A Python-Based Simulated IoT Security Framework**
University School of Automation and Robotics, GGSIPU East Delhi Campus
IoT Security — Group Project

---

## What is this?

HostelGuard simulates a Smart Hostel Building with 8 IoT devices across 4 types.
The same system runs in two modes — **insecure** (intentional vulnerabilities) and
**secure** (fully hardened). Six real attack types are demonstrated against both
modes, and a before/after comparison proves every attack is blocked in secure mode.

**No hardware, no real network, no external services.** Everything runs in-process
in pure Python on a single laptop.

---

## Quick Start

```bash
# 1. Create and activate the virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the demos
python main.py --mode insecure    # insecure baseline + generate docs
python main.py --mode secure      # hardened system
python main.py --mode compare     # full before/after comparison

# 4. (Optional) Start the web dashboard
python main.py --mode secure --serve
# Then open http://127.0.0.1:5000/ in your browser
```

---

## Project Layout

```
HostelGuard_agents/
├── main.py                        Entry point (--mode insecure|secure|compare)
├── requirements.txt               Allowed third-party libraries
├── hostelguard/
│   ├── config.py                  All settings and device fleet definition
│   ├── clock.py                   Real/fake clock (for deterministic tests)
│   ├── db.py                      SQLite database helper
│   ├── exceptions.py              Project-specific exception classes
│   ├── sim/                       Simulation layer
│   │   ├── messages.py            MessageEnvelope (wire format)
│   │   ├── wire.py                Simulated network + attacker hook
│   │   ├── interfaces.py          Abstract base classes + AttackResult
│   │   ├── insecure_device.py     Plaintext device (Module 1)
│   │   ├── insecure_broker.py     Unauthenticated broker (Module 1)
│   │   ├── insecure_cloud.py      Plaintext cloud (Module 1)
│   │   └── secure_device.py       AES+HMAC+ECDSA device (Module 2)
│   ├── attacks/                   Six simulated attacks (Module 1)
│   │   ├── replay_attack.py
│   │   ├── spoofing_attack.py
│   │   ├── brute_force_attack.py
│   │   ├── flooding_attack.py
│   │   ├── sniffing_attack.py
│   │   ├── tampering_attack.py
│   │   ├── security_trees.py      Attack tree + fault tree diagrams
│   │   └── secure_attacks.py      Secure-mode attack wrappers
│   ├── crypto/                    Cryptography (Module 2)
│   │   ├── aes_gcm.py             AES-256-GCM encryption
│   │   ├── hmac_integrity.py      HMAC-SHA256 message authentication
│   │   ├── ecdsa_signatures.py    ECDSA P-256 digital signatures
│   │   ├── keystore.py            File-backed key store
│   │   └── cipher_comparison.py  AES-GCM vs XOR comparison chart
│   ├── access/                    Access control (Module 3)
│   │   ├── registry.py            Device/user registration + bcrypt
│   │   ├── rbac.py                Role-Based Access Control rules
│   │   ├── secure_broker.py       Authenticated + rate-limited broker
│   │   └── secure_cloud.py        JWT auth + RBAC + audit log cloud
│   ├── privacy/                   Privacy (Module 3)
│   │   └── techniques.py          Minimisation, DP noise, k-anonymity
│   ├── cloud/                     Cloud security (Module 4)
│   │   ├── dashboard.py           Flask dashboard (127.0.0.1 only)
│   │   └── case_study.py          Mirai Botnet case study
│   └── integration/               Wiring and comparison
│       ├── profiles.py            System factory (insecure / secure)
│       ├── runner.py              Normal-traffic demo runner
│       └── compare.py             Before/after comparison + chart
├── tests/                         pytest test suite (83 tests)
├── docs/                          Documentation and deliverables
└── outputs/                       Generated graphs, results, database
```

---

## Device Fleet

| Device ID           | Type               | Location      |
|---------------------|--------------------|---------------|
| rfid_main_gate      | RFID Door Lock     | Main Gate     |
| rfid_warden_room    | RFID Door Lock     | Warden Room   |
| temp_room_101       | Temperature Sensor | Room 101      |
| temp_mess_hall      | Temperature Sensor | Mess Hall     |
| energy_floor1       | Energy Meter       | Floor 1       |
| energy_floor2       | Energy Meter       | Floor 2       |
| motion_corridor     | Motion Sensor      | Corridor      |
| motion_stairwell    | Motion Sensor      | Stairwell     |

---

## Roles and Permissions

| Role        | Publish telemetry | Subscribe all | Unlock doors | Query all | Admin |
|-------------|:-----------------:|:-------------:|:------------:|:---------:|:-----:|
| Warden      | Yes               | Yes           | Yes          | Yes       | Yes   |
| Technician  | Yes               | Yes           | No           | Yes       | No    |
| Student     | No                | Temp only     | No           | No        | No    |
| Device      | Own topic only    | Own cmd only  | No           | No        | No    |

---

## Security Modules

### Module 1 — Threats and Attacks (6 marks)
Insecure baseline with 6 attacks, security requirements table, attack tree,
fault tree. All six attacks succeed against the insecure system.

### Module 2 — Cryptography (7 marks)
- **AES-256-GCM** — authenticated encryption of all telemetry payloads
- **HMAC-SHA256** — message integrity over all envelope fields
- **ECDSA P-256** — digital signatures per device (non-repudiation)
- **Key Store** — file-backed key management
- Cipher comparison chart: AES-GCM vs XOR

### Module 3 — Access Control and Privacy (7 marks)
- Device and user registration with revocation
- bcrypt password hashing (cost=12 in production, cost=4 in tests)
- Role-Based Access Control (RBAC) on broker and cloud
- Rate limiting (10 msg/s) + account lockout after 5 failures
- Privacy: data minimisation, differential privacy (Laplace), k-anonymity

### Module 4 — Cloud Security and Case Study (6 marks)
- JWT authentication with 1-hour expiry
- Encrypted telemetry storage (AES-GCM in SQLite)
- Tamper-evident audit log with alerts
- Flask dashboard at 127.0.0.1:5000
- Mirai Botnet (2016) case study

### Integration (4 marks)
- `python main.py --mode insecure|secure|compare`
- Before/after comparison chart (`outputs/comparison_chart.png`)
- 92 automated tests (100% pass rate)

---

## Before / After Results

| Attack              | Insecure  | Secure    | Defense                      |
|---------------------|-----------|-----------|------------------------------|
| Replay              | SUCCEEDED | BLOCKED   | Counter + timestamp window   |
| Spoofing            | SUCCEEDED | BLOCKED   | HMAC + ECDSA signature       |
| Brute Force         | SUCCEEDED | BLOCKED   | bcrypt + account lockout     |
| Flooding (DoS)      | SUCCEEDED | BLOCKED   | Rate limiter (burst limit)   |
| Sniffing            | SUCCEEDED | BLOCKED   | AES-256-GCM encryption       |
| Tampering           | SUCCEEDED | BLOCKED   | HMAC-SHA256 verification     |

---

## Running Tests

```bash
python -m pytest tests/ -v
# Expected: 92 passed
```

---

## Generated Outputs

| File                              | Description                        |
|-----------------------------------|------------------------------------|
| outputs/architecture.png          | Complete system architecture diagram|
| outputs/attack_tree.png           | Attack tree diagram                |
| outputs/fault_tree.png            | Fault tree diagram                 |
| outputs/cipher_comparison.png     | AES-GCM vs XOR speed/security      |
| outputs/privacy_comparison.png    | DP noise + k-anonymity graphs      |
| outputs/comparison_chart.png      | Before/after attack results        |
| outputs/results_insecure.json     | Raw insecure attack results        |
| outputs/results_secure.json       | Raw secure attack results          |
| docs/security_requirements.md    | Security requirements table (SR1-15)|
| docs/mirai_case_study.md          | Mirai Botnet case study            |

---

## Academic Integrity

This code was generated by an AI coding agent (Antigravity/Gemini) as the
initial implementation. The group has reviewed, tested, and understands every
module. See `docs/ai_use_declaration.md` for the full declaration.

---

## Members (fill in before submission)

| Name | Roll Number | Module |
|------|-------------|--------|
| [Name 1] | [Roll] | Module 1 — Threats & Attacks |
| [Name 2] | [Roll] | Module 2 — Cryptography |
| [Name 3] | [Roll] | Module 3 — Access Control & Privacy |
| [Name 4] | [Roll] | Module 4 — Cloud Security & Case Study |
