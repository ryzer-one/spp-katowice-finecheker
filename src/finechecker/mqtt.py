from __future__ import annotations

import json
import socket
from typing import Any, Dict

import paho.mqtt.client as mqtt

from .__init__ import __version__


def make_client(host: str, port: int, username: str | None, password: str | None, client_id: str | None = None, tls: bool = False) -> mqtt.Client:
    cid = client_id or f"finechecker-{socket.gethostname()}"
    client = mqtt.Client(client_id=cid, clean_session=True)
    if username and password:
        client.username_pw_set(username, password)
    if tls:
        client.tls_set()
    client.connect(host, port, keepalive=60)
    # Start network loop to ensure publishes are sent
    client.loop_start()
    return client


def discovery_payload(name: str, unique_id: str, plate: str, device_ident: str) -> Dict[str, Any]:
    return {
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


def publish_discovery(client: mqtt.Client, discovery_prefix: str, plate: str, device_ident: str) -> None:
    unique_id = f"finechecker_{plate}"
    name = f"Parking Fine ({plate})"
    topic = f"{discovery_prefix}/binary_sensor/{unique_id}/config"
    payload = discovery_payload(name, unique_id, plate, device_ident)
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
