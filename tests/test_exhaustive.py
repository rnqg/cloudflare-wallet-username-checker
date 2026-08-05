from cloudflare_wallet_checker.exhaustive import generate_handles


def test_generate_letter_combinations() -> None:
    handles = generate_handles("letters")
    assert len(handles) == 26**3
    assert len(set(handles)) == 26**3
    assert handles[0] == "aaa"
    assert handles[-1] == "zzz"


def test_generate_all_combinations() -> None:
    handles = generate_handles("all")
    assert len(handles) == 37**3
    assert "0a-" in handles
