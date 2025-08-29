# SPP Katowice Finechecker

Checks for Katowice city parking penalty fees and integrates results with Home Assistant via MQTT Discovery.

## Status
- Early work-in-progress. See `docs/DECISIONS.md` and `docs/ROADMAP.md`.

## Overview
- Scrapes the official Katowice SPP website using Selenium (headless Chromium).
- Publishes one Home Assistant binary_sensor per license plate via MQTT Discovery.
- Runs once per day by default (self-scheduled in the container) or on demand.

## Quick Start (temporary)
- Existing script: `python selenium_fine_checker.py SK229TM --json`
- Upcoming CLI: `finechecker --plates SK229TM SK123AB --json`

## Home Assistant Integration
- Uses MQTT Discovery; no manual HA YAML needed beyond broker setup.
- Sensor state: `on` = fines present, `off` = no fines.
- Attributes: `message`, `details`, `checked_at`, `version`.

## Next Steps
- Finalize license and config format.
- Restructure into a package and add MQTT discovery.
- Add Docker and Nix flake for reproducible dev.

---
Contributions and suggestions welcome.
