"""
hostelguard/access/rbac.py
Role-Based Access Control (RBAC) for the HostelGuard broker and cloud.

Defines which operations each role may perform.  The broker and cloud
service check these rules before executing any action.

Permission table
----------------
Role        | Publish telemetry | Subscribe any topic | Send unlock command | Query all | Admin
------------|-------------------|---------------------|---------------------|-----------|------
warden      |        Yes        |         Yes         |         Yes         |    Yes    |  Yes
technician  |        Yes        |         Yes         |          No         |    Yes    |   No
student     |         No        |  temp topics only   |          No         |    No     |   No
device      |   own topic only  |   own cmd topic     |          No         |    No     |   No
"""

import logging

from hostelguard import config
from hostelguard.exceptions import AuthorizationError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Topic-level permission rules
# ---------------------------------------------------------------------------

def _is_own_topic(client_id: str, topic: str) -> bool:
    """Return True if the topic starts with the client's own device ID."""
    return topic.startswith(client_id + "/") or topic == client_id


def can_publish(role: str, client_id: str, topic: str) -> bool:
    """Return True if the given role may publish to topic."""
    if role == config.ROLE_WARDEN:
        return True  # warden can publish anything (commands and admin messages)
    if role == config.ROLE_TECHNICIAN:
        return True  # technician can publish health/maintenance messages
    if role == config.ROLE_DEVICE:
        # Devices may only publish to their own telemetry topic
        expected = config.make_topic(client_id, config.TOPIC_TELEMETRY)
        return topic == expected
    if role == config.ROLE_STUDENT:
        return False  # students cannot publish
    return False


def can_subscribe(role: str, client_id: str, topic: str) -> bool:
    """Return True if the given role may subscribe to topic."""
    if role in (config.ROLE_WARDEN, config.ROLE_TECHNICIAN):
        return True  # full read access
    if role == config.ROLE_DEVICE:
        # Devices may only subscribe to their own command topic
        expected = config.make_topic(client_id, config.TOPIC_COMMAND)
        return topic == expected
    if role == config.ROLE_STUDENT:
        # Students may only subscribe to aggregated temperature topics
        return "temperature_sensor" in topic or "temp" in topic
    return False


def can_send_command(role: str, target_device_id: str, command: str) -> bool:
    """Return True if the role may send a command to the target device."""
    if role == config.ROLE_WARDEN:
        return True  # warden has full command authority
    if role == config.ROLE_TECHNICIAN:
        # Technicians can send health checks but not unlock commands
        return command != "unlock"
    return False  # students and devices cannot send commands


def can_query_all(role: str) -> bool:
    """Return True if the role may query all telemetry records."""
    return role in (config.ROLE_WARDEN, config.ROLE_TECHNICIAN)


def can_admin(role: str) -> bool:
    """Return True if the role may perform administrative actions."""
    return role == config.ROLE_WARDEN


def check_publish(role: str, client_id: str, topic: str) -> None:
    """Raise AuthorizationError if publish is not permitted."""
    if not can_publish(role, client_id, topic):
        raise AuthorizationError(
            f"Role '{role}' (client '{client_id}') may not publish to topic '{topic}'"
        )


def check_subscribe(role: str, client_id: str, topic: str) -> None:
    """Raise AuthorizationError if subscribe is not permitted."""
    if not can_subscribe(role, client_id, topic):
        raise AuthorizationError(
            f"Role '{role}' (client '{client_id}') may not subscribe to topic '{topic}'"
        )


def check_admin(role: str) -> None:
    """Raise AuthorizationError if admin is not permitted."""
    if not can_admin(role):
        raise AuthorizationError(f"Role '{role}' may not perform admin actions")
