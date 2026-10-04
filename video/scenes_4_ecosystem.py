"""Chapters 16-19: repositories, dependencies, hooks, tests."""

from __future__ import annotations

from components import arrow, box, code, label, notes, svg, terminal
from recordings import rec
from scenes_common import L, S, excerpt, lines, scene

DEPS = excerpt("charts/bookshop/Chart.yaml", "dependencies:", "condition:")
HOOK = excerpt("charts/bookshop/templates/report-hook.yaml", "kind: Job", "before-hook-creation")

# ---------------------------------------------------------------- 16. Repositories
scene("Repositories", "labs/11-repositories.md", "How charts get distributed", svg(
    box(0, 0, 40, 520, 180, "🧑‍💻", "Chart author", ["helm package → NAME-VERSION.tgz"], "blue")
    + arrow(1, 530, 90, 650, 60) + arrow(1, 530, 170, 650, 220)
    + box(1, 660, 0, 520, 130, "🌐", "HTTP repository", ["index.yaml + .tgz files"], "amber", "#2b2410")
    + box(1, 660, 170, 520, 130, "📦", "OCI registry", ["GHCR, ECR, Harbor ... helm push"], "violet", "#221a3a")
    + arrow(2, 1190, 60, 1300, 110) + arrow(2, 1190, 230, 1300, 170)
    + box(2, 1310, 60, 410, 180, "⎈", "Chart user", ["helm install", "--version X"], "ok", "#0f2a22")
    + label(3, 860, 420, "repo add · repo update · search repo · show chart/values/readme · install --version", 30, "amber", "middle", 800)
), [
    S("Charts are distributed by name and version. The author packages a chart into an archive."),
    S("Either an H T T P repository, which is a web server with an index and the archives, or an O C I registry, the "
      "same kind of registry that stores container images."),
    S("You consume them with a pinned version: the same package, every time."),
    S("This is most of Helm at work: installing ingress controllers, monitoring, cert manager, from their maintainers' "
      "charts."),
])

scene(None, "Recorded · labs/11-repositories.md", "Review someone else's chart before you install it", terminal(
    rec(L["11-repositories"], "helm search repo podinfo\nhelm search repo podinfo --versions", head=2, cmd="helm search repo podinfo", tones={"6.15.0": "ok"})
    + rec(L["11-repositories"], "helm template catalog podinfo/podinfo --version 6.14.1", step=1, tones={"stefanprodan/podinfo": "ok", "curl": "warn", "tiny-tools": "warn", "grpc": "warn"}),
    "bash (recorded)"), [
    S("podinfo, a small, well-maintained demo application with a public chart. Search shows chart and app versions.", zoom=1.3),
    S("Before installing, render it and look at what it creates and which images it pulls. A Deployment and a Service "
      "with the maintainer's image. But also three test Pods with three more images from Docker Hub, one without any "
      "tag. That is the kind of detail a review is for.", zoom=1.3),
])

scene(None, "Recorded · labs/11-repositories.md", "Install with your values, and publish your own", terminal(
    rec(L["11-repositories"], "curl -s http://podinfo.localhost:8080/ | grep -E", nth=0, tones={"Bookshop catalog": "ok"})
    + rec(L["11-repositories"], "helm push labs/work/demo-app-1.0.0.tgz", step=1, cmd="helm push labs/work/demo-app-1.0.0.tgz oci://localhost:5001/charts --plain-http", tones={"Pushed": "ok"})
    + rec(L["11-repositories"], "helm install shopfront oci://", step=2, head=4, tones={"Pulled": "ok"}),
    "bash (recorded)"), [
    S("Installed with a pinned version and a reviewed values file: our message, two replicas, an Ingress.", zoom=1.35),
    S("And the other direction: package demo app and push it to an O C I registry, here a local one standing in for G H "
      "C R.", zoom=1.35),
    S("Anyone can now install it by reference and version, instead of copying a folder.", zoom=1.35),
])

# ---------------------------------------------------------------- 17. Dependencies
scene("Dependencies", "charts/bookshop/Chart.yaml", "A parent chart and its database", code(
    "charts/bookshop/Chart.yaml (dependencies)", DEPS, "yaml", 26) + notes([
    (0, "name + version", "which chart, pinned"),
    (1, "repository", "file://, https:// or oci://"),
    (2, "condition", "postgres.enabled=false → external database"),
]), [
    S("The Bookshop chart depends on a small PostgreSQL chart from this repository.", hl=lines(DEPS, "name: postgres", "version:")),
    S("The repository can be a folder, an H T T P repository, or an O C I registry.", hl=lines(DEPS, "repository", "repository")),
    S("And a condition makes it optional: the bundled database for dev and C I, an external one in production.",
      hl=lines(DEPS, "condition", "condition")),
], layout="code")

scene(None, "Recorded · labs/12-dependencies.md", "Declared is not downloaded", terminal(
    rec(L["12-dependencies"], "helm dependency list examples/dependency-example", nth=0, tones={"missing": "bad"})
    + rec(L["12-dependencies"], "ls examples/dependency-example/charts/", step=1, head=6, tones={" ok": "ok"})
    + rec(L["12-dependencies"], "kubectl get deploy,svc --namespace lab-12", step=2, tones={"dependency of storefront": "ok"}, width=140),
    "bash (recorded)"), [
    S("A dependency must be in the parent's charts folder. Declared, but missing.", zoom=1.4),
    S("helm dependency update downloads it and writes Chart.lock: exact version and digest. Commit the lock, and build "
      "from it in C I.", zoom=1.3),
    S("One release, objects from two charts, and the child configured through the parent's values.", zoom=1.3),
])

scene(None, "Recorded · labs/12-dependencies.md", "The whole Bookshop, one command", terminal(
    rec(L["12-dependencies"], "kubectl get pods --namespace bookshop-dev", tones={"Running": "ok", "Completed": "ok"})
    + rec(L["12-dependencies"], "curl -s http://dev.bookshop.localhost:8080/config.js", step=1, width=140, tones={"Ada": "ok"}),
    "bash (recorded)"), [
    S("Five services, the database from the dependency, and a completed report Job: seven workloads from two charts, "
      "one release, one command. Compare with chapter three.", zoom=1.2),
    S("And it works: dev environment, users from PostgreSQL, with a password nobody ever typed.", zoom=1.3),
])

# ---------------------------------------------------------------- 18. Hooks
scene("Hooks", "Recorded · labs/13-hooks.md", "When Helm runs each hook", terminal(
    rec(L["13-hooks"], "for job in $(kubectl get jobs", cmd="kubectl logs <each hook Job, in creation order>", tones={"hook": "ok"})
    + rec(L["13-hooks"], "kubectl logs --namespace lab-13 job/hooks-pre-delete", step=1, tones={"pre-delete": "ok"}, drop=r"kube-root-ca|^$|^NAME\s+DATA"),
    "bash (recorded)"), [
    S("A hook is an ordinary Job with an annotation. Helm creates it at its moment and waits for it. Pre install before "
      "anything exists, post install after, pre and post upgrade around an upgrade.", zoom=1.3),
    S("Pre delete runs on uninstall, before anything is deleted. And notice: all five hook Jobs are still there after "
      "the uninstall. They were never part of the release. Hooks are powerful, and they add moving parts.", zoom=1.2),
])

scene(None, "charts/bookshop/templates/report-hook.yaml", "A real hook, for a real reason", code(
    "charts/bookshop/templates/report-hook.yaml", HOOK, "yaml", 24) + notes([
    (0, "post-install, post-upgrade", "after every deployment, when the services are up"),
    (1, "before-hook-creation", "replace the previous Job; keep the last one's log"),
]), [
    S("The Bookshop has exactly one hook: after every install and upgrade, the report worker writes a deployment report. "
      "A task that must run at a precise moment of each deployment: that is when a hook is the right tool.",
      hl=lines(HOOK, "helm.sh/hook\"", "hook-weight")),
    S("Its delete policy replaces the previous Job just before the next run, so the last report's log is always there.",
      hl=lines(HOOK, "before-hook-creation", "before-hook-creation")),
], layout="code")

scene(None, "Recorded · labs/13-hooks.md", "A failing pre-upgrade hook is a gate", terminal(
    rec(L["13-hooks"], "--set failAt=pre-upgrade", tones={"FAILED": "bad"}, drop="level=WARN", wrap=118)
    + rec(L["13-hooks"], "helm history hooks --namespace lab-13", step=1, tones={"failed": "bad", "hello from": "ok"}, width=130),
    "bash (recorded)"), [
    S("Now a pre upgrade hook fails, as a migration might. The upgrade fails immediately, naming the hook.", zoom=1.3),
    S("Revision two is failed, and the ConfigMap still holds the old message: nothing was touched. That is what a pre "
      "upgrade hook is for. Before writing one, ask whether an init container, a normal Job or a pipeline step would do: "
      "a rollback does not undo what a hook did.", zoom=1.3),
])

# ---------------------------------------------------------------- 19. Tests
scene("Tests", "Recorded · labs/14-tests.md", "helm test: a one-command health check", terminal(
    rec(L["14-tests"], "helm test shop --namespace bookshop-dev --logs", nth=0, drop=r"^(NAME|LAST|NAMESPACE|STATUS|REVISION|DESCRIPTION|Last)",
        tones={"Succeeded": "ok", "passed": "ok"}),
    "bash (recorded)"), [
    S("A Helm test is a Pod that only helm test creates. The Bookshop's calls every service through its Service, the "
      "A P Is check their database connection, and the frontend must report this release's environment. All checks "
      "passed. Run it after every upgrade, and on a schedule.", zoom=1.15),
])

scene(None, "Recorded · labs/14-tests.md", "Helm doesn't watch the cluster. The test does.", terminal(
    rec(L["14-tests"], "kubectl scale deployment shop-java-api", tones={"scaled": "warn"})
    + rec(L["14-tests"], "helm test shop --namespace bookshop-dev --logs", step=1, out_has="Phase:          Failed", tail=6,
          tones={"Failed": "bad", "can't connect": "bad"}, wrap=118)
    + rec(L["14-tests"], "helm get manifest shop --namespace bookshop-dev \\\n  | kubectl diff", step=2,
          cmd="helm get manifest shop | kubectl diff --server-side --field-manager=helm -f -", tones={"+": "ok", "-": "bad"}),
    "bash (recorded)"), [
    S("Someone scales java A P I to zero by hand. helm status still says deployed: Helm records what it applied, it "
      "does not watch the cluster.", zoom=1.35),
    S("The test does. After go status, the next check, java A P I, cannot connect.", zoom=1.25),
    S("Compare what Helm applied with what is live: the release says one replica, the cluster has zero. Drift. An "
      "upgrade re-applies the release's state, and the test passes again.", zoom=1.4),
])
