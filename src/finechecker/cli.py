from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from typing import List

from .config import load_config
from .katowice_spp import KatowiceSeleniumChecker
from .mqtt import make_client, publish_discovery, publish_state


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Katowice parking fine checker")
    # Support both positional plates and --plates option
    p.add_argument("plates", nargs="*", help="License plates to check (positional)")
    p.add_argument("--plates", "-p", dest="plates_opt", nargs="+", help="License plates to check (option)")
    p.add_argument("--config", "-c", help="Path to TOML config file")
    p.add_argument("--json", action="store_true", help="Output JSON to stdout")
    p.add_argument("--text", action="store_true", help="Output human-readable text")
    p.add_argument("--headful", action="store_true", help="Run browser in visible mode")
    p.add_argument("--verbose", "-v", action="store_true", help="Print progress logs to stderr")
    p.add_argument("--mqtt", action="store_true", help="Publish via MQTT (discovery + state)")
    p.add_argument("--daemon", action="store_true", help="Run forever on a schedule (from config)")
    return p.parse_args(argv)


def check_once(plate: str, headless: bool = True, verbose: bool = False):
    try:
        with KatowiceSeleniumChecker(headless=headless, verbose=verbose) as checker:
            result = checker.check_license_plate(plate)
    except ImportError as e:
        result = {"license_plate": plate, "status": "error", "has_fines": None, "message": str(e)}
    result["checked_at"] = datetime.now(timezone.utc).isoformat()
    result.setdefault("source", "spp.katowice.eu")
    return result


def output_result(result, as_json: bool, human: bool):
    if as_json or not human:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        plate = result.get("license_plate", "?")
        status = result.get("status")
        has = result.get("has_fines")
        msg = result.get("message", "")
        print(f"{plate}: status={status} has_fines={has} message={msg}")


def run_once(args, plates: List[str], headless: bool):
    results = []
    for plate in plates:
        res = check_once(plate, headless=headless, verbose=args.verbose)
        results.append(res)
        output_result(res, as_json=args.json, human=args.text)
    return results


def run_daemon(args, plates: List[str], headless: bool, interval_hours: int, jitter_seconds: int, mqtt_cfg):
    # MQTT connection reused across loops if enabled
    client = None
    device_ident = "finechecker"
    if args.mqtt:
        client = make_client(
            mqtt_cfg.host,
            mqtt_cfg.port,
            mqtt_cfg.username,
            mqtt_cfg.password,
            client_id=mqtt_cfg.client_id,
            tls=mqtt_cfg.tls,
        )
        for plate in plates:
            publish_discovery(client, mqtt_cfg.discovery_prefix, plate, device_ident)

    while True:
        for plate in plates:
            res = check_once(plate, headless=headless)
            output_result(res, as_json=args.json, human=args.text)
            if client is not None:
                publish_state(client, plate, res)
            # small delay between plates to avoid hammering
            time.sleep(5)
        # sleep until next run
        sleep_for = max(60, interval_hours * 3600)
        # simple jitter
        jitter = min(jitter_seconds, 3600)
        time.sleep(sleep_for + (jitter // 2))


def main(argv: List[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    cfg = load_config(args.config)
    # Precedence: --plates option > positional plates > config
    plates = (args.plates_opt or args.plates or cfg.plates)
    if not plates:
        print("No plates provided (CLI or config)", file=sys.stderr)
        return 2
    headless = (cfg.browser.headless and not args.headful) or (not args.headful)

    if args.daemon:
        run_daemon(
            args,
            plates,
            headless=headless,
            interval_hours=cfg.schedule.interval_hours,
            jitter_seconds=cfg.schedule.jitter_seconds,
            mqtt_cfg=cfg.mqtt,
        )
        return 0

    results = run_once(args, plates, headless=headless)

    if args.mqtt:
        client = make_client(
            cfg.mqtt.host, cfg.mqtt.port, cfg.mqtt.username, cfg.mqtt.password, client_id=cfg.mqtt.client_id, tls=cfg.mqtt.tls
        )
        device_ident = "finechecker"
        for plate in plates:
            publish_discovery(client, cfg.mqtt.discovery_prefix, plate, device_ident)
        for res in results:
            publish_state(client, res["license_plate"], res)

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
