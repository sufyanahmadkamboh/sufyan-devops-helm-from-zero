"""Helm From Zero: the video course, 24 chapters.

Every terminal shows real output, recorded while the lessons ran (tests/mdrun.py --record) on a kind cluster with
Helm 4.3. Code panels show the real files of the repository. The chapters are split over five modules; this one
collects them and adds the production layer.
"""

from __future__ import annotations

import scenes_1_intro  # noqa: F401  (chapters 1-4)
import scenes_2_charts  # noqa: F401  (chapters 5-11)
import scenes_3_releases  # noqa: F401  (chapters 12-15)
import scenes_4_ecosystem  # noqa: F401  (chapters 16-19)
import scenes_5_finish  # noqa: F401  (chapters 20-24)
from production import package
from scenes_common import SCENES

package(SCENES, "From copied Kubernetes YAML to one chart",
        ["Charts", "Values", "Templates", "Releases", "Rollbacks", "Troubleshooting"], {
    "Break it, then make it ours": {0: "error", 1: "success"},
    "Package it twice, then break it": {1: "error"},
    "A value that does nothing, and a schema that stops it": {0: "error", 1: "success"},
    "Don't trust the template just because Helm accepted it": {0: "error", 1: "error"},
    "Three mistakes, reported one at a time": {0: "error", 3: "success"},
    "The upgrade that succeeded and broke everything": {0: "error"},
    "Deploy a bad version on purpose": {0: "error"},
    "This is where Helm history becomes useful": {0: "success"},
    "A failing pre-upgrade hook is a gate": {0: "error"},
    "Helm doesn't watch the cluster. The test does.": {1: "error", 2: "success"},
    "Where secrets leak": {1: "error", 2: "success"},
    "A failed upgrade that still broke the site": {1: "error"},
    "Helm 4 and server-side apply: a conflict": {1: "error", 2: "success"},
    "Three environments, one chart version": {1: "success"},
    "Upgrade, break, roll back, test": {1: "error", 2: "success"},
})

assert len([s for s in SCENES if s["chapter"]]) == 24, [s["chapter"] for s in SCENES if s["chapter"]]
