# Cloudflare Wallet Username Checker

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![CI](https://github.com/rnqg/cloudflare-wallet-username-checker/actions/workflows/ci.yml/badge.svg)](https://github.com/rnqg/cloudflare-wallet-username-checker/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-26A5E4?logo=telegram&logoColor=white)](#telegram-bot)

**English** · [Русский](README.ru.md)

An asynchronous CLI, resumable three-character scanner and bilingual Telegram bot for checking
`cloudflare.pay` wallet handles.

> This is an unofficial community project. It is not affiliated with or endorsed by Cloudflare.

## Why this checker exists

The visible website behavior is not enough to determine availability. Both genuinely available names
and some Cloudflare-reserved names can redirect to the reservation form. This project uses the public
availability endpoint and keeps these states separate:

| API state | Meaning | Output |
| --- | --- | --- |
| `available: true` | Can currently be reserved | `available.txt` |
| `TAG_TAKEN` | Already claimed | `taken.txt` |
| `RESERVED_TAG` | Reserved by Cloudflare | `reserved.txt` |
| `INVALID_TAG` | Invalid handle | `invalid.txt` |
| Network/API failure | Result is unknown | `error.txt` |

Unknown responses are never reported as available.

## Features

- HTTP/2 and connection pooling with bounded concurrency
- retries with exponential backoff and `Retry-After` support
- single, list and file-based checks
- JSON output and one result file per status
- resumable exhaustive scanner for every three-character combination
- EN/RU Telegram bot with persistent language selection
- Telegram premium custom emoji and formatted messages
- Docker and Docker Compose deployment
- Python 3.10–3.13 CI, tests, Ruff and strict mypy

## Quick start

```bash
git clone https://github.com/rnqg/cloudflare-wallet-username-checker.git
cd cloudflare-wallet-username-checker
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install:

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

Check one or more handles:

```bash
cfwallet qqq x402agent my-wallet
```

Check a file:

```bash
cfwallet --input examples/usernames.txt --workers 5
```

Russian CLI output:

```bash
cfwallet --input examples/usernames.txt --lang ru
```

Machine-readable output:

```bash
cfwallet qqq x402agent --json
```

Results are written to `output/` by default. Change the directory with `--output-dir`.

## Exhaustive three-character scan

The exhaustive scanner writes a JSONL checkpoint after every response. Running the same command again
resumes the scan and retries only missing or failed handles.

Letters and digits, 36³ combinations:

```bash
cfwallet-exhaustive --alphabet alnum --workers 20
```

Letters, digits and hyphen, 37³ combinations:

```bash
cfwallet-exhaustive --alphabet all --workers 20
```

Use conservative worker counts. A larger number can increase rate limiting and make the scan slower.
Do not run repeated exhaustive scans without a legitimate reason.

## Telegram bot

The bot supports English and Russian, `/check`, plain-text handle lists, language switching and grouped
availability results. User language preferences are stored in SQLite. No checked handles are stored.

Create a bot with [@BotFather](https://t.me/BotFather), then configure the environment:

```bash
cp .env.example .env
```

Set `TELEGRAM_BOT_TOKEN` in `.env`, then run:

```bash
set -a
source .env
set +a
cfwallet-bot
```

Windows PowerShell:

```powershell
$env:TELEGRAM_BOT_TOKEN="1234567890:your_token"
cfwallet-bot
```

Bot commands:

| Command | Description |
| --- | --- |
| `/start` | Open the checker |
| `/check name1 name2` | Check handles |
| `/language` | Switch EN/RU |
| `/help` | Usage help |
| `/about` | Project information |

### Docker Compose

```bash
cp .env.example .env
docker compose up -d --build
docker compose logs -f bot
```

The SQLite database is persisted in `./data`.

## CLI reference

```text
cfwallet [-i FILE] [-o DIRECTORY] [--workers N] [--timeout SECONDS]
         [--retries N] [--lang en|ru] [--json] [--quiet] [HANDLE ...]
```

The accepted handle format is 3–32 ASCII letters, digits or hyphens. The API remains the authority for
normalization and final validation.

## Responsible use

- Availability changes over time; reserve a name through the official website.
- The project does not automate reservations or bypass authentication.
- Respect Cloudflare rate limits and terms.
- Do not use the tool for service disruption, credential collection or trademark abuse.
- Never commit `.env`, bot tokens, databases, checkpoints or exported results.

## Development

```bash
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
pytest
mypy
```

See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md) and
[architecture notes](docs/ARCHITECTURE.md).

## License

[MIT](LICENSE)
