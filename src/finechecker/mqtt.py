from __future__ import annotations

import json
import socket
from typing import Any, Dict

import paho.mqtt.client as mqtt

from .__init__ import __version__

# Retained "online"/"offline"; the broker publishes "offline" (LWT) when the daemon dies.
AVAILABILITY_TOPIC = "finechecker/availability"
PAYLOAD_ONLINE = "online"
PAYLOAD_OFFLINE = "offline"


def make_client(
    host: str,
    port: int,
    username: str | None,
    password: str | None,
    client_id: str | None = None,
    tls: bool = False,
    availability: bool = False,
) -> mqtt.Client:
    cid = client_id or f"finechecker-{socket.gethostname()}"
    client = mqtt.Client(client_id=cid, clean_session=True)
    if username and password:
        client.username_pw_set(username, password)
    if tls:
        client.tls_set()
    if availability:
        client.will_set(AVAILABILITY_TOPIC, PAYLOAD_OFFLINE, retain=True)

        def _on_connect(c: mqtt.Client, userdata: Any, flags: Any, rc: int) -> None:
            # Runs on every (re)connect, so availability recovers after broker restarts.
            if rc == 0:
                c.publish(AVAILABILITY_TOPIC, PAYLOAD_ONLINE, retain=True)

        client.on_connect = _on_connect
    client.connect(host, port, keepalive=60)
    # Start network loop to ensure publishes are sent
    client.loop_start()
    return client


def discovery_payload(
    name: str, unique_id: str, plate: str, device_ident: str, availability: bool = False
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "name": name,
        "uniq_id": unique_id,
        "stat_t": f"finechecker/{plate}/state",
        "json_attr_t": f"finechecker/{plate}/attributes",
        "dev": {
            "ids": [device_ident],
            "name": "Katowice SPP Finechecker",
            "mf": "finechecker",
            "mdl": "katowice-spp",
            "sw": __version__,
        },
        "dev_cla": "problem",
        "pl_on": "on",
        "pl_off": "off",
    }
    if availability:
        payload["avty_t"] = AVAILABILITY_TOPIC
        payload["pl_avail"] = PAYLOAD_ONLINE
        payload["pl_not_avail"] = PAYLOAD_OFFLINE
    return payload


def publish_discovery(
    client: mqtt.Client,
    discovery_prefix: str,
    plate: str,
    device_ident: str,
    availability: bool = False,
) -> None:
    unique_id = f"finechecker_{plate}"
    name = f"Parking Fine ({plate})"
    topic = f"{discovery_prefix}/binary_sensor/{unique_id}/config"
    payload = discovery_payload(name, unique_id, plate, device_ident, availability)
    client.publish(topic, json.dumps(payload), retain=True)


def publish_state(client: mqtt.Client, plate: str, result: Dict[str, Any]) -> None:
    state_topic = f"finechecker/{plate}/state"
    attrs_topic = f"finechecker/{plate}/attributes"
    state = "on" if result.get("has_fines") is True else "off" if result.get("has_fines") is False else "off"
    client.publish(state_topic, state, retain=True)
    # Strip noisy fields; ensure json-serializable
    attrs = {k: v for k, v in result.items() if k not in {"has_fines"}}
    attrs["version"] = __version__
    client.publish(attrs_topic, json.dumps(attrs, ensure_ascii=False), retain=True)
