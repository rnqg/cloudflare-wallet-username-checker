from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from cloudflare_wallet_checker.core import (
    CheckResult,
    CloudflareWalletClient,
    Status,
    unique_handles,
)
from cloudflare_wallet_checker.files import read_handles, write_results

CLI_TEXT = {
    "en": {
        "description": "Check Cloudflare Wallet username availability",
        "no_handles": "Provide usernames or use --input FILE.",
        "checking": "Checking {count} unique username(s) with {workers} workers",
        "done": "Done: free={available}, taken={taken}, reserved={reserved}, invalid={invalid}, errors={error}",
        "files": "Results: {path}",
    },
    "ru": {
        "description": "Проверка доступности юзернеймов Cloudflare Wallet",
        "no_handles": "Укажите юзернеймы или используйте --input FILE.",
        "checking": "Проверяю {count} уникальных имён, потоков: {workers}",
        "done": "Готово: свободно={available}, занято={taken}, резерв={reserved}, неверно={invalid}, ошибки={error}",
        "files": "Результаты: {path}",
    },
}

STATUS_LABELS = {
    "en": {
        Status.AVAILABLE: "FREE",
        Status.TAKEN: "TAKEN",
        Status.RESERVED: "RESERVED",
        Status.INVALID: "INVALID",
        Status.ERROR: "ERROR",
    },
    "ru": {
        Status.AVAILABLE: "СВОБОДЕН",
        Status.TAKEN: "ЗАНЯТ",
        Status.RESERVED: "РЕЗЕРВ",
        Status.INVALID: "НЕВЕРНЫЙ",
        Status.ERROR: "ОШИБКА",
    },
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=CLI_TEXT["en"]["description"])
    parser.add_argument("handles", nargs="*")
    parser.add_argument("-i", "--input", type=Path)
    parser.add_argument("-o", "--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--lang", choices=("en", "ru"), default="en")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")
    return parser


async def run(args: argparse.Namespace) -> int:
    values = list(args.handles)
    if args.input is not None:
        if not args.input.is_file():
            print(f"Input file not found: {args.input}", file=sys.stderr)
            return 2
        values.extend(read_handles(args.input))
    handles = unique_handles(values)
    if not handles:
        print(CLI_TEXT[args.lang]["no_handles"], file=sys.stderr)
        return 2
    if not 1 <= args.workers <= 50:
        print("--workers must be between 1 and 50", file=sys.stderr)
        return 2
    if args.timeout <= 0 or args.retries < 0:
        print("--timeout must be positive and --retries cannot be negative", file=sys.stderr)
        return 2
    if not args.quiet and not args.json:
        print(CLI_TEXT[args.lang]["checking"].format(count=len(handles), workers=args.workers))

    async def progress(current: int, total: int, result: CheckResult) -> None:
        if args.quiet or args.json:
            return
        label = STATUS_LABELS[args.lang][result.status]
        value = result.normalized or result.username
        suffix = f" — {result.detail}" if result.status is Status.ERROR else ""
        print(f"[{current}/{total}] {label:<9} @{value}{suffix}", flush=True)

    async with CloudflareWalletClient(
        max_connections=args.workers,
        timeout=args.timeout,
        retries=args.retries,
    ) as client:
        results = await client.check_many(handles, workers=args.workers, on_result=progress)
    counts = write_results(args.output_dir, results)
    if args.json:
        print(json.dumps([result.to_dict() for result in results], ensure_ascii=False, indent=2))
    elif not args.quiet:
        values_by_status = {status.value: counts[status] for status in Status}
        print(CLI_TEXT[args.lang]["done"].format(**values_by_status))
        print(CLI_TEXT[args.lang]["files"].format(path=args.output_dir.resolve()))
    return 1 if counts[Status.ERROR] else 0


def main() -> int:
    return asyncio.run(run(build_parser().parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
