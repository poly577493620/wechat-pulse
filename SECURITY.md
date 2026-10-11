# Security Policy

## Sensitive data

Never submit any of the following to an issue, pull request, log, screenshot, or repository:

- `.env`
- WeRead or WeChat cookies
- `ADMIN_TOKEN`
- SQLite databases from `data/`
- Browser profiles or exported session files

If a cookie or token is exposed, revoke it immediately and create a replacement.

## Reporting a vulnerability

Please report vulnerabilities privately to the repository maintainer. Include the affected version, reproduction steps, impact, and a minimal proof of concept. Do not include real user credentials or collected article data.

## Deployment guidance

WePulse is designed for private, self-hosted use. Do not expose it directly to the public internet. Use HTTPS, a reverse proxy, firewall rules, a strong `ADMIN_TOKEN`, and regular backups. Run it with the least operating-system privilege necessary.
