# Roadmap / Tasks

Use this checklist to track progress. Grouped by milestones.

## M0 — Docs & Alignment
- [x] Record decisions (integration, scheduling, multi-plate, schema)
- [ ] Choose license (MIT or Apache-2.0)
- [ ] Finalize config format (TOML vs YAML)

## M1 — Package & CLI
- [ ] Create package skeleton under `src/finechecker/`
- [ ] Move Selenium logic into `katowice_spp.py`
- [ ] Add CLI `finechecker` with args: `--json/--text`, `--verbose`, `--timeout`, `--headful`, `--plates`, `--config`
- [ ] Support multiple plates; consistent JSON schema; add `checked_at`
- [ ] Define exit codes and error categories

## M2 — MQTT Discovery Integration
- [ ] Implement MQTT client and discovery payloads
- [ ] Create one binary_sensor per plate with attributes
- [ ] Configurable discovery prefix and device info
- [ ] Retain last state; publish on changes and on startup
 - [ ] Default device id to `finechecker-<hostname>`; allow override
 - [ ] Add `--require-mqtt` flag (fail hard if MQTT unavailable)

## M3 — Scheduling & Container
- [ ] Add internal daily scheduler (e.g., APScheduler/cron-like) with jitter/backoff
- [ ] Allow one-shot mode for ad-hoc checks
- [ ] Dockerfile (Python 3.12-slim, chromium, chromedriver, non-root)
- [ ] Healthcheck and logging defaults

## M4 — Config & Secrets
- [ ] Config file (TOML/YAML) with plates list and MQTT settings
- [ ] Environment variable overrides
- [ ] Validate config on startup with helpful errors
 - [ ] Auto-detect config: `./config.toml`, `$HOME/.config/finechecker/config.toml`, or `FINECHECKER_CONFIG`

## M5 — Reliability & Limits
- [ ] Centralize selectors/constants (future-proofing)
- [ ] Implement retry with exponential backoff and rate limiting between plates
- [ ] Timeouts for page load and element waits
 - [ ] MQTT connection: friendly errors, reconnect/backoff, soft-continue without MQTT when not required
 - [ ] Graceful shutdown in daemon mode (signals handling)

## M6 — Dev Environment & CI
- [ ] Nix flake for reproducible devShell (python, chromium, chromedriver, ruff, black, pytest)
- [ ] Pre-commit hooks (ruff, black, eof-fixer, trailing-whitespace)
- [ ] GitLab CI: lint, unit tests, build image (optional)

## M7 — Tests & Examples
- [ ] Unit tests for CLI and JSON shaping
- [ ] Mark live Selenium tests as `-m live` and skip by default
- [ ] HA MQTT discovery example and automation snippet in README

## M8 — Release
- [ ] Choose versioning (SemVer) and tag v0.1.0
- [ ] Publish Docker image (optional)
