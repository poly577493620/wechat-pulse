# Changelog

## Unreleased

- Reorganized supplementary documentation under `docs/` and implementation scripts under `scripts/`, while preserving the three root-level Windows start, stop, and restart entry points.
- Added a copy-ready Codex automation guide for daily WePulse summaries, state-based deduplication, credential-safe local API access, and bounded failure retries.
- Added a dedicated Chinese troubleshooting guide covering PowerShell encoding, folder permissions, stale management tokens, WeRead Cookie selection, HTTP 400 responses, background startup, notification tests, and missed schedules.
- Added an open-source release checklist to prevent publishing credentials, local databases, logs, virtual environments, or personal paths.
- Clarified the management dashboard button behavior, hidden Windows background process, restart flow, and current daily-delivery retry boundary.

## 0.3.4 - 2026-10-11

- Added a password-style Cookie input to the local management dashboard.
- Cookie updates are validated, saved to the local `.env`, and applied immediately without restart.
- Rejected incomplete Cookies and invisible control characters before they can break collection.
- Removed the error-prone hidden terminal Cookie prompt from first-run setup.

## 0.3.3 - 2026-10-11

- Added an early project-directory write-permission check with actionable Windows guidance.
- Documented the required folder permission and discouraged permanent administrator execution.

## 0.3.2 - 2026-10-11

- Saved every PowerShell script as UTF-8 with BOM for Windows PowerShell 5 compatibility.
- Added release validation with the same `powershell.exe` used by the Windows double-click entry point.

## 0.3.1 - 2026-10-11

- Added a prominent prerequisites guide for network/WinGet and WeRead Cookie access.
- Added a safe personal-account trial checklist and Cookie renewal instructions.
- Added first-run security guidance directly to the web management dashboard.

## 0.3.0 - 2026-10-11

- Made native Windows execution the default; Docker is now optional.
- Added one-click local setup using WinGet and uv, including automatic Python 3.12 management.
- Added hidden background startup, health waiting, local logs, and safe PID-based shutdown.
- Added install/remove scripts for Windows logon autostart.
- Added clipboard-assisted dashboard login and updated end-user documentation.

## 0.2.0 - 2026-10-11

- Added a Chinese web management dashboard at `/admin`.
- Added one-click Docker startup scripts for Windows, Linux, and macOS.
- Added real WeRead Cookie verification and visible collection-failure alerts.
- Added daily email and WeCom robot delivery with an in-dashboard test action.
- Daily delivery now collects first, then renders and sends the latest digest.
- Added account collection/deletion controls and deployment entry-point documentation.

## 0.1.0 - 2026-10-11

- Initial self-hosted release.
- Added SQLite subscription and article storage.
- Added WeRead latest-article and generic RSS collectors.
- Added automatic subscription setup from a public WeChat article URL.
- Added scheduled collection, Markdown digests, RSS output, JSON API, and optional Webhook delivery.
- Added Docker packaging, tests, security guidance, and deployment documentation.
