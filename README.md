# SPP Katowice Finechecker

Checks for Katowice city parking penalty fees and integrates results with Home Assistant via MQTT Discovery.

## Status
- Early work-in-progress. See `docs/DECISIONS.md` and `docs/ROADMAP.md`.
- License: MIT. Config format: TOML.

## Overview
- Scrapes the official Katowice SPP website using Selenium (headless Chromium).
- Publishes one Home Assistant binary_sensor per license plate via MQTT Discovery.
- Runs once per day by default (self-scheduled in the container) or on demand.

## Quick Start (temporary)
- Existing script: `python selenium_fine_checker.py SK229TM --json`
- CLI: `finechecker --plates SK229TM --json [-v] [--headful]`

## Configuration
- Copy `config.example.toml` to `config.toml` and adjust.
- CLI can override: plates, headless mode, output format, MQTT publishing.

## Home Assistant Integration
- Uses MQTT Discovery; no manual HA YAML needed beyond broker setup.
- Sensor state: `on` = fines present, `off` = no fines.
- Attributes: `message`, `details`, `checked_at`, `version`.

## Next Steps
- Implement MQTT discovery publishing and container scheduler.
- Add CI and tests.

---
Contributions and suggestions welcome.

## GitHub Container Registry (GHCR)
- This repo includes a GitHub Actions workflow that builds and pushes a Docker image to GHCR on pushes to `main` and tags `v*`.
- Image name: `ghcr.io/<owner>/<repo>` (GitHub will replace `<owner>/<repo>` with this repo path).

### Enable publishing
- Ensure GitHub Actions is enabled for the repo.
- No extra secrets needed: the workflow uses the built-in `GITHUB_TOKEN` to push to GHCR.
- The image will be tagged `latest` on the default branch, plus branch/tag/sha tags.

## Docker Compose
- Copy `.env.example` to `.env` and set `GHCR_IMAGE=ghcr.io/<owner>/<repo>:latest` and your MQTT creds.
- Make a `config.toml` (see `config.example.toml`).
- Start:
  - `docker compose up -d`
- Logs:
  - `docker compose logs -f`

Compose service runs the app in daemon mode, publishes MQTT discovery/state, and restarts unless stopped.
