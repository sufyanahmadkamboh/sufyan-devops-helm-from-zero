"""Production layer: the title sting, the end card and the sound-effect cues.

The scene scripts stay focused on teaching; this module adds the packaging around them:
  * an animated title card at the start (with the intro sound) and an end card at the finish
  * cues for the sound effects: an error tone when something breaks on screen, a chime when it is fixed or proven
Silent steps ("say": "") are held for "hold" seconds; build.py gives them silence instead of narration.
"""

from __future__ import annotations

from components import card, grid


def _intro(subtitle: str, chips: list[str]) -> dict:
    chip_html = "".join(f'<span class="chip st" data-s="1">{c}</span>' for c in chips)
    body = (
        '<div class="titlecard">'
        '<div class="tc-logo st" data-s="0">⎈</div>'
        '<div class="tc-name st" data-s="0">Helm From Zero</div>'
        f'<div class="tc-part st" data-s="1">{subtitle}</div>'
        f'<div class="tc-chips">{chip_html}</div>'
        '</div>')
    return {"chapter": None, "kicker": "A hands-on Helm course, every command real", "title": "&nbsp;", "body": body,
            "layout": "full", "steps": [{"say": "", "hl": None, "tts": None, "hold": 1.9, "sfx": "intro"},
                                        {"say": "", "hl": None, "tts": None, "hold": 2.3, "sfx": "pop"}]}


def _outro() -> dict:
    body = grid([
        card(0, "💻", "The free lab", "github.com/sufyanahmadkamboh/sufyan-devops-helm-from-zero", "ok"),
        card(1, "🏁", "Your turn", "chart, values, install, upgrade, break, roll back: then the capstone", "amber"),
        card(1, "📚", "Study material", "17 labs, 12 troubleshooting scenarios, 12 challenges, a glossary and interview questions", "blue"),
        card(1, "🧭", "The roadmap", "twenty levels, from copied YAML to a production-style chart", "blue"),
    ], cols=2)
    return {"chapter": None, "kicker": "Helm From Zero", "title": "Thanks for watching", "body": body, "layout": "full",
            "steps": [{"say": "", "hl": None, "tts": None, "hold": 2.2, "sfx": "outro"},
                      {"say": "", "hl": None, "tts": None, "hold": 5.0}]}


CSS = """
.titlecard{height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px;margin-top:-40px}
.tc-logo{font-size:150px;line-height:1}
.tc-name{font-size:100px;font-weight:900;letter-spacing:-3px;color:#f1f6fc}
.tc-part{font-size:42px;font-weight:800;color:#ffc94d}
.tc-chips{display:flex;gap:16px;margin-top:18px}
.chip{background:#13233a;border:3px solid #3b82d6;border-radius:40px;padding:10px 26px;font-size:30px;font-weight:800;color:#f1f6fc}
"""


def package(scenes: list[dict], subtitle: str, chips: list[str], cues: dict[str, dict[int, str]]) -> None:
    """Add the title card and end card, and mark sound-effect cues (title fragment -> {step: kind})."""
    for frag, marks in cues.items():
        hits = [s for s in scenes if frag in s["title"]]
        if len(hits) != 1:
            raise SystemExit(f"sound cue: {frag!r} matches {len(hits)} scenes")
        for k, kind in marks.items():
            hits[0]["steps"][k]["sfx"] = kind
    intro = _intro(subtitle, chips)
    intro["chapter"], scenes[0]["chapter"] = scenes[0]["chapter"], None   # YouTube chapters must start at 0:00
    scenes.insert(0, intro)
    scenes.append(_outro())
