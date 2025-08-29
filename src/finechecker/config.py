from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional

try:  # Python 3.11+
    import tomllib as toml
except Exception:  # pragma: no cover
    import tomli as toml  # type: ignore


@dataclass
class MQTTConfig:
    host: str = "localhost"
    port: int = 1883
    username: Optional[str] = None
    password: Optional[str] = None
    discovery_prefix: str = "homeassistant"
    client_id: Optional[str] = None
    tls: bool = False


@dataclass
class ScheduleConfig:
    interval_hours: int = 24
    jitter_seconds: int = 300


@dataclass
class BrowserConfig:
    headless: bool = True


@dataclass
class AppConfig:
    plates: List[str] = field(default_factory=list)
    mqtt: MQTTConfig = field(default_factory=MQTTConfig)
    schedule: ScheduleConfig = field(default_factory=ScheduleConfig)
    browser: BrowserConfig = field(default_factory=BrowserConfig)


def load_config(path: Optional[str] = None) -> AppConfig:
    data = {}
    if path and os.path.exists(path):
        with open(path, "rb") as f:
            data = toml.load(f)

    plates = data.get("plates", {}).get("list", []) if isinstance(data.get("plates"), dict) else data.get("plates", [])

    mqtt_data = data.get("mqtt", {})
    schedule_data = data.get("schedule", {})
    browser_data = data.get("browser", {})

    cfg = AppConfig(
        plates=plates or [],
        mqtt=MQTTConfig(
            host=str(mqtt_data.get("host", os.getenv("MQTT_HOST", "localhost"))),
            port=int(mqtt_data.get("port", int(os.getenv("MQTT_PORT", "1883")))),
            username=mqtt_data.get("username", os.getenv("MQTT_USERNAME")),
            password=mqtt_data.get("password", os.getenv("MQTT_PASSWORD")),
            discovery_prefix=str(mqtt_data.get("discovery_prefix", os.getenv("MQTT_PREFIX", "homeassistant"))),
            client_id=mqtt_data.get("client_id", os.getenv("MQTT_CLIENT_ID")),
            tls=bool(mqtt_data.get("tls", os.getenv("MQTT_TLS", "false").lower() in ["1", "true", "yes"])),
        ),
        schedule=ScheduleConfig(
            interval_hours=int(schedule_data.get("interval_hours", 24)),
            jitter_seconds=int(schedule_data.get("jitter_seconds", 300)),
        ),
        browser=BrowserConfig(
            headless=bool(browser_data.get("headless", os.getenv("HEADLESS", "true").lower() in ["1", "true", "yes"])),
        ),
    )

    return cfg

