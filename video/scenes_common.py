"""Shared helpers for the scene scripts (scenes_1_*.py ... scenes_5_*.py, collected by scenes.py)."""

from __future__ import annotations

from pathlib import Path

SCENES: list[dict] = []
REPO = Path(__file__).resolve().parent.parent


def S(say: str, hl: tuple[int, int] | None = None, tts: str | None = None, zoom: float = 1) -> dict:
    """One narration step. zoom > 1 moves the camera into the terminal, centred on the lines this step reveals."""
    return {"say": say, "hl": hl, "tts": tts, "zoom": zoom}


def scene(chapter, kicker, title, body, steps, layout="full"):
    SCENES.append({"chapter": chapter, "kicker": kicker, "title": title, "body": body, "steps": steps, "layout": layout})


def src(path: str) -> str:
    """A real file from the repository, for code panels."""
    return (REPO / path).read_text(encoding="utf-8")


def lines(text: str, first: str, last: str) -> tuple[int, int]:
    """1-based line range from the first line containing `first` to the next line containing `last`."""
    ls = text.splitlines()
    a = next(i for i, x in enumerate(ls, 1) if first in x)
    return a, next(i for i, x in enumerate(ls, 1) if i >= a and last in x)


L = {n: f"labs/{n}.md" for n in [
    "00-setup", "01-install-helm", "02-first-chart", "03-chart-structure", "04-values", "05-templates", "06-rendering",
    "07-install-release", "08-upgrade", "09-rollback", "10-environments", "11-repositories", "12-dependencies",
    "13-hooks", "14-tests", "15-troubleshooting", "16-capstone", "cleanup"]}
LEVEL1 = "environments/README.md"
SEC = "docs/13-security.md"
PROD = "docs/16-production-style-chart.md"
CH = "challenges/README.md"
TS = {n: f"troubleshooting/{n}.md" for n in [
    "01-template-syntax-error", "02-wrong-value", "03-incorrect-image", "04-wrong-service-selector",
    "05-wrong-environment-values", "06-failed-upgrade", "07-bad-revision-rollback", "08-missing-configmap",
    "09-secret-problem", "10-dependency-problem", "11-failed-helm-test", "12-values-conflict"]}


def excerpt(path: str, first: str, last: str) -> str:
    """The lines of a real file from the line containing `first` to the next line containing `last` (inclusive)."""
    text = src(path).splitlines()
    a = next(i for i, x in enumerate(text) if first in x)
    b = next(i for i, x in enumerate(text) if i >= a and last in x)
    return "\n".join(text[a:b + 1])


def bare(path: str) -> str:
    """A real file without full-line comments and blank lines (Dockerfiles and YAML on one screen)."""
    return "\n".join(x for x in src(path).splitlines() if x.strip() and not x.lstrip().startswith("#"))
