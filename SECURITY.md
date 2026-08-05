# Security policy

## Supported versions

Security fixes are provided for the latest release.

## Reporting a vulnerability

Do not publish credentials, bot tokens, private logs or proof-of-concept secrets in a public issue.
Open a private GitHub security advisory for this repository instead. Include the affected version,
impact, reproduction steps and a minimal proof of concept.

## Operational guidance

- Keep `TELEGRAM_BOT_TOKEN` outside the repository.
- Do not commit `.env`, SQLite databases, checkpoints or result exports.
- Use conservative worker counts and respect rate limiting from `cloudflare.pay`.
- Rotate a token immediately if it was exposed.
