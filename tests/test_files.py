from pathlib import Path

from cloudflare_wallet_checker.core import CheckResult, Status
from cloudflare_wallet_checker.files import read_handles, write_results


def test_read_handles(tmp_path: Path) -> None:
    source = tmp_path / "names.txt"
    source.write_text("One\n@one\nTwo\n", encoding="utf-8")
    assert read_handles(source) == ["one", "two"]


def test_write_results(tmp_path: Path) -> None:
    results = [
        CheckResult("free", Status.AVAILABLE, "free"),
        CheckResult("taken", Status.TAKEN, "taken"),
        CheckResult("failed", Status.ERROR, detail="timeout"),
    ]
    counts = write_results(tmp_path, results)
    assert counts[Status.AVAILABLE] == 1
    assert (tmp_path / "available.txt").read_text(encoding="utf-8") == "free\n"
    assert (tmp_path / "error.txt").read_text(encoding="utf-8") == "failed\ttimeout\n"
