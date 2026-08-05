from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from cloudflare_wallet_checker.core import CheckResult, Status, unique_handles


def read_handles(path: Path) -> list[str]:
    return unique_handles(path.read_text(encoding="utf-8-sig").splitlines())


def write_lines(path: Path, lines: Iterable[str]) -> None:
    values = list(lines)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(values) + ("\n" if values else ""), encoding="utf-8")


def write_results(output_dir: Path, results: Iterable[CheckResult]) -> dict[Status, int]:
    groups: dict[Status, list[str]] = {status: [] for status in Status}
    for result in results:
        value = result.normalized or result.username
        if result.status is Status.ERROR:
            groups[result.status].append(f"{value}\t{result.detail}")
        else:
            groups[result.status].append(value)
    output_dir.mkdir(parents=True, exist_ok=True)
    for status, lines in groups.items():
        write_lines(output_dir / f"{status.value}.txt", lines)
    return {status: len(lines) for status, lines in groups.items()}
