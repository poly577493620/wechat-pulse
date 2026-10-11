# Contributing

Thank you for contributing to WePulse.

1. Create a focused branch from the latest main branch.
2. Keep collectors isolated from storage and presentation code.
3. Never commit credentials, cookies, databases, or copyrighted article bodies.
4. Add or update tests for behavioral changes.
5. Run `uv sync --extra dev` and `uv run pytest -q` before opening a pull request.
6. Explain any reliance on an undocumented upstream endpoint and provide a safe fallback or clear error.
7. If a change affects setup, configuration, dashboard behavior, or Windows scripts, update `README.md`, `docs/QUICKSTART.zh-CN.md`, and `docs/TROUBLESHOOTING.zh-CN.md` together.
8. Test Windows entry scripts with Windows PowerShell 5 as well as PowerShell 7; preserve UTF-8 BOM for `.ps1` files.

Bug reports should include the WePulse version, operating system, connector type, sanitized logs, expected behavior, and actual behavior. Replace all cookies, tokens, article identifiers, and personal paths with placeholders.

Before preparing a release, follow [docs/maintainers/OPEN_SOURCE_RELEASE.zh-CN.md](docs/maintainers/OPEN_SOURCE_RELEASE.zh-CN.md). Never build a public archive directly from a personal runtime directory containing `.env` or `data/`.
