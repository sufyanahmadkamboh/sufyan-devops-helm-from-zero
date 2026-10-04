"""Chapters 1-4: introduction, why Helm, Kubernetes YAML before Helm, install Helm."""

from __future__ import annotations

from components import arrow, box, card, checklist, grid, label, notes, svg, terminal
from recordings import rec
from scenes_common import L, LEVEL1, S, scene

# ---------------------------------------------------------------- 1. Introduction
scene("Introduction", "Helm From Zero", "From copied YAML to one chart, three environments, a release history", svg(
    box(0, 0, 40, 520, 230, "📄", "Raw Kubernetes YAML", ["dev/ staging/ prod/", "1,374 lines, mostly copies"], "bad", "#2a1520")
    + arrow(1, 530, 155, 640, 155)
    + box(1, 650, 40, 420, 230, "⎈", "One Helm chart", ["templates, written once", "+ a values file per env"], "blue", "#16306a")
    + arrow(2, 1080, 155, 1190, 155)
    + box(2, 1200, 40, 520, 230, "🔁", "Releases", ["install, upgrade, test", "history, rollback"], "ok", "#0f2a22")
    + label(3, 860, 420, "YAML problem → chart → templates → values → render → lint → install → upgrade → rollback", 27, "amber", "middle", 800)
    + label(3, 860, 470, "→ environments → repositories → dependencies → hooks → tests → security → troubleshooting → capstone", 27, "amber", "middle", 800)
), [
    S("Welcome to Helm From Zero. We start with an application you already know how to deploy: five services and a "
      "database, written as plain Kubernetes YAML, copied three times for development, staging and production."),
    S("Then we replace those copies with one Helm chart: templates written once, and a small values file per "
      "environment."),
    S("And we operate it the way teams do every week: install, upgrade, test, and roll back, with a release history "
      "that records everything."),
    S("Twenty levels, from the YAML problem to a production-style chart and a capstone. Along the way we break things "
      "on purpose, and investigate them like we would in production."),
])

scene(None, "How this course works", "Every command you will see was really run", grid([
    card(0, "🧪", "Tested lessons", "every command runs automatically against a real kind cluster, with Helm 4.3", "ok"),
    card(0, "📺", "Real output", "every terminal in this video is a recording of those runs, nothing typed for the camera", "blue"),
    card(1, "🧭", "17 labs, 20 levels", "each lab: objective, commands, break it, troubleshoot it, challenge", "amber"),
    card(1, "🔧", "12 failures", "template errors, wrong values, immutable selectors, stuck releases, conflicts ...", "bad"),
], cols=2), [
    S("Everything comes from one free repository on GitHub. Each lesson is a Markdown file whose commands run "
      "automatically, on a real Kubernetes cluster. Every terminal in this video is a recording of those runs."),
    S("Seventeen labs, each with a part where you break something and a part where you investigate it, then twelve "
      "troubleshooting scenarios, twelve challenges, and a capstone."),
])

scene(None, "Recorded · labs/00-setup.md", "The lab: Kubernetes in Docker, and an ingress controller", terminal(
    rec(L["00-setup"], "kubectl config current-context", tones={" Ready": "ok"})
    + rec(L["00-setup"], "curl -s http://anything.localhost:8080/", step=1, tones={"404": "ok"}),
    "bash (recorded)"), [
    S("The lab cluster is kind: Kubernetes one point thirty-seven, each node a Docker container on your computer.", zoom=1.3),
    S("Traefik routes the traffic. Nothing is deployed yet, so it answers four oh four: proof that requests reach it. "
      "And notice: Traefik itself was installed with one Helm command. By chapter sixteen you will be able to read "
      "every word of it.", zoom=1.3),
])

# ---------------------------------------------------------------- 2. Why Helm?
scene("Why Helm?", "docs/01-what-is-helm.md", "Package · template · release", svg(
    box(0, 560, 0, 600, 120, "⎈", "Helm chart", ["Chart.yaml · values.yaml · templates/"], "blue", "#16306a")
    + arrow(1, 700, 125, 300, 230) + arrow(1, 860, 125, 860, 230) + arrow(1, 1020, 125, 1420, 230)
    + box(1, 60, 235, 480, 120, "🧪", "values-dev.yaml", ["1 replica · dev host"], "ok", "#0f2a22")
    + box(1, 620, 235, 480, 120, "🧭", "values-staging.yaml", ["2 replicas · staging host"], "amber", "#2b2410")
    + box(1, 1180, 235, 480, 120, "🏭", "values-prod.yaml", ["autoscaling · pinned tags"], "bad", "#2a1520")
    + arrow(2, 300, 360, 760, 455) + arrow(2, 860, 360, 860, 455) + arrow(2, 1420, 360, 960, 455)
    + box(2, 460, 460, 800, 120, "📄", "Rendered YAML", ["plain Kubernetes objects"], "blue")
    + arrow(3, 860, 585, 860, 635)
    + box(3, 360, 640, 1000, 100, "☸️", "Kubernetes + a release record", ["revision 1, 2, 3 ... · rollback"], "ok", "#0f2a22")
), [
    S("Helm is the package manager for Kubernetes. A chart packages the templates of an application, with a "
      "Chart.yaml that gives it a name and a version, and a values.yaml with every setting and its default."),
    S("Each environment adds a small file with only what differs: replicas, host names, resources, autoscaling."),
    S("Helm renders the templates with those values into plain Kubernetes YAML, on your computer, before Kubernetes "
      "receives anything."),
    S("And it records each installation as a release, with numbered revisions you can inspect, upgrade and roll back."),
])

scene(None, "docs/01-what-is-helm.md", "Two versions, two meanings", notes([
    (0, "version: 1.2.0", "the CHART: the package, its templates and defaults; changes whenever the chart changes"),
    (1, "appVersion: \"2.0.0\"", "the APPLICATION it deploys by default: usually the image tag"),
    (2, "new template option", "chart 1.2.0 → 1.3.0, application unchanged"),
    (3, "new application release", "appVersion 2.0.0 → 2.1.0, and the chart version too: the package changed"),
]), [
    S("One distinction to get right from the start. The chart version describes the package."),
    S("The app version describes the software inside: usually the image tag that is deployed by default."),
    S("Add an option to the chart, and only the chart version moves."),
    S("Ship a new application release, and the app version moves, and the chart version too, because the package's "
      "contents changed. A published chart version never changes."),
])

# ---------------------------------------------------------------- 3. Kubernetes YAML before Helm
scene("Kubernetes YAML Before Helm", "Recorded · environments/README.md", "Deploy dev the way you know", terminal(
    rec(LEVEL1, "kubectl -n bookshop-dev get deployments", tones={"1/1": "ok"})
    + rec(LEVEL1, "curl -s http://dev.bookshop.localhost:8080/config.js", step=1, width=140, tones={"Ada": "ok", "APP_ENV": "ok"}),
    "bash (recorded)"), [
    S("Before Helm, let's see the problem. Here is the Bookshop, deployed with kubectl apply: five Deployments, "
      "a database, Services and an Ingress. All running.", zoom=1.15),
    S("The frontend reports environment dev, and the users come back from the database. Plain YAML works. For one "
      "environment, it is perfectly good.", zoom=1.2),
])

scene(None, "Recorded · environments/README.md", "Now imagine staging and production", terminal(
    rec(LEVEL1, "wc -l environments/dev/*.yaml")
    + rec(LEVEL1, "grep -rn \"bookshop-node-api:\" environments/", step=1, width=140, tones={"node-api": "warn"})
    + rec(LEVEL1, "grep -n -A1 \"stringData\" environments/dev/secret.yaml", step=2, tones={"password": "bad"}),
    "bash (recorded)"), [
    S("Now imagine maintaining it across three environments. About four hundred sixty lines each, and the diff between "
      "dev and staging is a few dozen lines: the rest is copies.", zoom=1.2),
    S("The node A P I team releases a new version. Where do you change the image? In three files. Forget one, and "
      "your environments silently drift apart.", zoom=1.15),
    S("And to make the folder applicable as-is, the password is written in a file, in Git, readable by everyone who can "
      "read the repository. That is the problem Helm addresses.", zoom=1.3),
])

# ---------------------------------------------------------------- 4. Install Helm
scene("Install Helm", "Recorded · labs/01-install-helm.md", "One binary, your kubeconfig, releases in the cluster", terminal(
    rec(L["01-install-helm"], "helm version", nth=0, wrap=118, tones={"v4.3": "ok"})
    + rec(L["01-install-helm"], "helm list --all-namespaces", step=1, width=150, tones={"deployed": "ok"})
    + rec(L["01-install-helm"], "helm env |", step=2, width=150),
    "bash (recorded)"), [
    S("Install Helm with an official method: the get helm four script, Homebrew, winget, or the release archive. This "
      "course is tested with Helm four point three.", zoom=1.2),
    S("Helm has no server. It uses your kubeconfig, like kubectl, and sees the same cluster: here the Traefik release "
      "from the setup.", zoom=1.15),
    S("Helm's own files hold the repositories you add and a cache. The releases are not here: they live in the cluster, "
      "which is why your teammates see the same list.", zoom=1.15),
])

scene(None, "Recorded · labs/01-install-helm.md", "Break it: a context that does not exist", terminal(
    rec(L["01-install-helm"], "helm list --kube-context does-not-exist", tones={"Error": "bad"}, wrap=118)
    + rec(L["01-install-helm"], "kubectl config get-contexts -o name", step=1, tones={"helm-lab": "ok"}),
    "bash (recorded)"), [
    S("Now let's intentionally break it. A typo in the context name, and Helm cannot reach a cluster.", zoom=1.3),
    S("The error names what it looked for; the list of contexts shows what exists. One more check worth making a habit: "
      "helm version. With two copies of Helm on the PATH, the first one wins, and while this course was being built, an "
      "older one made every hook wait for its full timeout.", zoom=1.3),
])
