# Decisions

This document records agreed decisions for the Katowice SPP fine checker project.

## Scope
- Purpose: Check Katowice city parking penalties and expose results to Home Assistant.
- Output focus: Binary sensor semantics per license plate with useful attributes.

## Naming
- Package/module: `finechecker`.
- Repository: `spp-katowice-finechecker`.

## Runtime & Tech
- Language: Python 3.12.
- Browser automation: Selenium 4.x with headless Chromium + chromedriver.
- Logging: Informational to stderr; `--verbose` for debug.

## Integration with Home Assistant
- Primary integration: MQTT Discovery (not command_line sensors).
- One binary_sensor per license plate.
- Attributes include: `message`, `details`, `checked_at` (UTC ISO8601), and implementation `version`.
- MQTT topics: use Home Assistant discovery (`homeassistant/binary_sensor/<plate>_finechecker/...`).
- Sensor state: `on` when fines present, `off` otherwise.
- Availability (daemon mode only): retained `online`/`offline` on `finechecker/availability`, LWT `offline` set at connect; discovery carries `avty_t`, so Home Assistant shows the sensor unavailable when the daemon is down.

## Deployment & Scheduling
- Packaging: Python package with console script `finechecker`.
- Deployment: Docker container (non-root, slim base) and venv for local runs.
- Scheduling: Container self-schedules periodic checks (default: once per day). Also supports one-shot run.

## Configuration
- List of plates in config (file and/or env). One sensor per plate.
- MQTT connection from env vars and/or config (host, port, user, pass, TLS optional, discovery prefix).
- Scraper selectors externalized for easier updates.

## Reliability & Limits
- Timeouts, retries, and exponential backoff to respect target site.
- Clear error categories and exit codes.
- Rate limiting between requests when checking multiple plates.

## Outputs
- JSON output for CLI by default. Human-readable/text optional.
- Stable schema with `license_plate`, `status`, `has_fines`, `message`, `details`, `checked_at`, `source`.

## Security & Privacy
- Plates need not be hidden in HA.
- Container runs as non-root; minimal privileges.

## Open Decisions (TBD)
- License: MIT vs Apache-2.0.
- Config format: `toml` vs `yaml` (leaning `toml`).

