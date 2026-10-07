"""Frontend class names must not look like advertising to an ad blocker.

EasyList and AdGuard Base carry generic cosmetic rules such as ``##.adv-link`` that hide any
element with that class on every site. v0.9.1 shipped adventurer names as
``<span class="adv-link">``, so every linked name vanished for players running uBlock Origin,
Adblock Plus, AdGuard or Brave. The filter lists own the ``ad-`` / ``ads-`` / ``adv-`` /
``advert-`` / ``sponsor-`` prefixes; staying out of them is cheaper than tracking the lists.
"""
import re
from pathlib import Path

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
SOURCES = [*FRONTEND.joinpath("src").rglob("*.vue"),
           *FRONTEND.joinpath("src").rglob("*.ts"),
           *FRONTEND.joinpath("src").rglob("*.css"),
           FRONTEND / "index.html"]

AD_LIKE = re.compile(r"(?<![A-Za-z0-9_-])(?:ad|ads|adv|advert|sponsor)[-_][A-Za-z0-9_-]+")


def test_no_ad_like_class_names() -> None:
    """No class, id or selector in the frontend starts with a prefix ad blockers hide."""
    hits = []
    for path in SOURCES:
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for match in AD_LIKE.finditer(line):
                hits.append(f"{path.relative_to(FRONTEND.parent).as_posix()}:{line_no}: {match.group(0)}")
    assert not hits, "ad-blocker-prone names (rename them):\n" + "\n".join(hits)
