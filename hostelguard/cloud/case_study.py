"""
hostelguard/cloud/case_study.py
Real IoT security incident case study: the 2016 Mirai Botnet.

This module writes docs/mirai_case_study.md comparing the Mirai attack
to the HostelGuard threat model and defenses.
"""

import pathlib
import logging

logger = logging.getLogger(__name__)

CASE_STUDY_TEXT = """# Mirai Botnet (2016) - IoT Security Case Study

## Incident Summary

In September 2016 the Mirai botnet hijacked hundreds of thousands of consumer
IoT devices (IP cameras, routers, DVRs) and used them to launch one of the
largest distributed denial-of-service (DDoS) attacks ever recorded.  The
attack peaked at over 620 Gbps and took down major services including DNS
provider Dyn, making sites such as Twitter, Netflix and Reddit unreachable
for hours.

## How Mirai Worked

1. Scanning: Mirai continuously scanned the public internet for devices with
   open Telnet ports (23 and 2323).

2. Credential stuffing: It tried 61 hard-coded default username/password pairs
   (e.g., admin:admin, root:root).  Most devices still used factory defaults.

3. Infection: Once logged in, Mirai downloaded and executed its malware binary,
   turning the device into a bot.

4. DDoS: Infected bots received commands from a C2 server and sent UDP/TCP
   flood traffic to the target IP address.

## Vulnerabilities Exploited

| Vulnerability          | Description                                              |
|------------------------|----------------------------------------------------------|
| Default credentials    | Devices shipped with hard-coded admin/admin passwords    |
| No account lockout     | Unlimited login attempts allowed brute force             |
| Telnet over internet   | Unencrypted remote management exposed publicly           |
| No firmware signing    | Arbitrary binaries could be executed                     |
| No network segmentation| IoT devices on the same network as critical services     |

## Comparison with HostelGuard Threat Model

| Attack vector          | Mirai (2016)             | HostelGuard insecure     | HostelGuard secure       |
|------------------------|--------------------------|--------------------------|--------------------------|
| Brute force login      | Succeeds (no lockout)    | Succeeds (plaintext pw)  | Blocked (bcrypt + lockout)|
| Default credentials    | Succeeds                 | Succeeds                 | Blocked (hashed pw)      |
| Traffic sniffing       | Telnet in plaintext      | All payloads readable    | AES-GCM encryption       |
| Message tampering      | No integrity check       | No MAC check             | HMAC-SHA256 verified     |
| Replay attack          | N/A (Telnet sessions)    | Accepted (no counter)    | Blocked (counter + window)|
| Flooding / DoS         | Massive DDoS achieved    | All packets accepted     | Rate limiter blocks burst |
| Spoofed commands       | Full device control      | Accepted (no signature)  | ECDSA signature required |

## Lessons Applied to HostelGuard

1. **No default credentials**: Users are registered with bcrypt-hashed
   passwords.  Plain-text storage is never used in secure mode.

2. **Account lockout**: After {lockout_threshold} failed attempts the account
   is locked for {lockout_duration} seconds, stopping brute-force attacks.

3. **Encrypted channels**: AES-256-GCM encrypts all telemetry so a network
   sniffer cannot read sensor data.

4. **Message authentication**: HMAC-SHA256 and ECDSA signatures ensure messages
   come from legitimate, registered devices.

5. **Replay protection**: A monotonic counter and timestamp window reject
   replayed packets.

6. **Rate limiting**: The secure broker limits each device to {rate_limit}
   messages per second, preventing flooding.

7. **Audit log**: Every login, query and admin action is recorded with
   timestamps and alerts for suspicious behaviour.

## References

- Krebs on Security (2016). "KrebsOnSecurity Hit With Record DDoS."
  https://krebsonsecurity.com/2016/09/krebsonsecurity-hit-with-record-ddos/
- Antonakakis et al. (2017). "Understanding the Mirai Botnet."
  USENIX Security 2017.
- NIST SP 800-213: IoT Device Cybersecurity Guidance for the Federal Government.
"""


def write_case_study(output_path: pathlib.Path) -> None:
    """Write the Mirai case study markdown file."""
    from hostelguard import config
    text = CASE_STUDY_TEXT.format(
        lockout_threshold=config.LOCKOUT_THRESHOLD,
        lockout_duration=config.LOCKOUT_DURATION_SECONDS,
        rate_limit=config.RATE_LIMIT_MAX_PER_SECOND,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    logger.info("Case study written to %s", output_path)
