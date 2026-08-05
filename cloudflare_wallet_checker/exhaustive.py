from __future__ import annotations

import argparse
import asyncio
import itertools
import json
import sys
from pathlib import Path

from cloudflare_wallet_checker.core import CheckResult, CloudflareWalletClient, Status
from cloudflare_wallet_checker.files import write_lines, write_results

ALPHABETS = {
    "letters": "abcdefghijklmnopqrstuvwxyz",
    "alnum": "abcdefghijklmnopqrstuvwxyz0123456789",
    "all": "abcdefghijklmnopqrstuvwxyz0123456789-",
}


def generate_handles(alphabet: str) -> list[str]:
    return ["".join(chars) for chars in itertools.product(ALPHABETS[alphabet], repeat=3)]


def load_checkpoint(path: Path) -> dict[str, CheckResult]:
    results: dict[str, CheckResult] = {}
    if not path.is_file():
        return results
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            payload = json.loads(line)
            result = CheckResult(
                username=payload["username"],
                status=Status(payload["status"]),
                normalized=payload.get("normalized"),
                detail=payload.get("detail", ""),
            )
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            continue
        results[result.username] = result
    return results


async def worker(
    input_queue: asyncio.Queue[str | None],
    output_queue: asyncio.Queue[CheckResult],
    client: CloudflareWalletClient,
) -> None:
    while True:
        username = await input_queue.get()
        if username is None:
            input_queue.task_done()
            return
        await output_queue.put(await client.check(username))
        input_queue.task_done()


async def collect(
    output_queue: asyncio.Queue[CheckResult],
    results: dict[str, CheckResult],
    checkpoint: Path,
    amount: int,
    total: int,
) -> None:
    completed = total - amount
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    with checkpoint.open("a", encoding="utf-8") as stream:
        for index in range(amount):
            result = await output_queue.get()
            results[result.username] = result
            stream.write(json.dumps(result.to_dict(), ensure_ascii=True) + "\n")
            if index % 50 == 0:
                stream.flush()
            completed += 1
            if completed % 250 == 0 or completed == total:
                counts = {status: 0 for status in Status}
                for item in results.values():
                    counts[item.status] += 1
                print(
                    f"{completed}/{total} free={counts[Status.AVAILABLE]} "
                    f"taken={counts[Status.TAKEN]} reserved={counts[Status.RESERVED]} "
                    f"invalid={counts[Status.INVALID]} errors={counts[Status.ERROR]}",
                    flush=True,
                )
            output_queue.task_done()
        stream.flush()


async def run(args: argparse.Namespace) -> int:
    handles = generate_handles(args.alphabet)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_lines(args.output_dir / "all.txt", handles)
    checkpoint = args.output_dir / "checkpoint.jsonl"
    results = load_checkpoint(checkpoint)
    final_statuses = {Status.AVAILABLE, Status.TAKEN, Status.RESERVED, Status.INVALID}
    remaining = [
        handle
        for handle in handles
        if results.get(handle) is None or results[handle].status not in final_statuses
    ]
    print(
        f"total={len(handles)} resumed={len(handles) - len(remaining)} "
        f"remaining={len(remaining)} workers={args.workers}"
    )
    if remaining:
        input_queue: asyncio.Queue[str | None] = asyncio.Queue()
        output_queue: asyncio.Queue[CheckResult] = asyncio.Queue()
        for handle in remaining:
            await input_queue.put(handle)
        for _ in range(args.workers):
            await input_queue.put(None)
        async with CloudflareWalletClient(
            max_connections=args.workers,
            timeout=args.timeout,
            retries=args.retries,
        ) as client:
            tasks = [
                asyncio.create_task(worker(input_queue, output_queue, client))
                for _ in range(args.workers)
            ]
            collector = asyncio.create_task(
                collect(output_queue, results, checkpoint, len(remaining), len(handles))
            )
            await asyncio.gather(*tasks)
            await collector
    ordered_results = [
        results.get(handle, CheckResult(handle, Status.ERROR, detail="missing result"))
        for handle in handles
    ]
    counts = write_results(args.output_dir, ordered_results)
    unavailable = [
        result.normalized or result.username
        for result in ordered_results
        if result.status in {Status.TAKEN, Status.RESERVED}
    ]
    write_lines(args.output_dir / "unavailable.txt", unavailable)
    summary = [f"checked={len(handles)}"]
    summary.extend(f"{status.value}={counts[status]}" for status in Status)
    write_lines(args.output_dir / "summary.txt", summary)
    print(" ".join(summary))
    return 1 if counts[Status.ERROR] else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check every three-character wallet handle")
    parser.add_argument("--alphabet", choices=tuple(ALPHABETS), default="alnum")
    parser.add_argument("--output-dir", type=Path, default=Path("output/three-char"))
    parser.add_argument("--workers", type=int, default=20)
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--retries", type=int, default=3)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not 1 <= args.workers <= 50:
        print("--workers must be between 1 and 50", file=sys.stderr)
        return 2
    if args.timeout <= 0 or args.retries < 0:
        print("--timeout must be positive and --retries cannot be negative", file=sys.stderr)
        return 2
    try:
        return asyncio.run(run(args))
    except KeyboardInterrupt:
        print("Stopped. Run the same command to resume from checkpoint.jsonl.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
