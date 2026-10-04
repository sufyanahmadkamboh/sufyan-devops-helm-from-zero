"""Chapters 20-24: secrets and security, troubleshooting, production-style chart, capstone, cleanup."""

from __future__ import annotations

from components import arrow, box, checklist, label, notes, svg, terminal
from recordings import rec
from scenes_common import CH, L, PROD, S, SEC, TS, scene

# ---------------------------------------------------------------- 20. Secrets & security
scene("Secrets & Security", "Recorded · docs/13-security.md", "Chart security is Kubernetes security", terminal(
    rec(SEC, "helm get manifest traefik --namespace traefik", tones={"ClusterRole": "warn"})
    + rec(SEC, "kubectl get clusterrole traefik-traefik", step=1, grep="secrets|ingresses\"\\]", tones={"secrets": "warn"})
    + rec(SEC, "-o custom-columns='POD:.metadata.name,NON_ROOT", step=2, tones={"true": "ok"}),
    "bash (recorded)"), [
    S("Installing a chart creates Kubernetes resources, with your credentials. Traefik, from chapter one, created a "
      "ClusterRole: permissions across the whole cluster.", zoom=1.35),
    S("Read what it may do: get, list and watch Secrets in every namespace, to load T L S certificates. Expected for an "
      "ingress controller, and worth knowing before you install it.", zoom=1.35),
    S("And what the Bookshop runs: every Pod non root, no A P I token mounted. The audit found one gap while this course "
      "was being built, the database Pod, and the chart was fixed.", zoom=1.2),
])

scene(None, "Recorded · docs/13-security.md", "Where secrets leak", terminal(
    rec(SEC, "helm install leaky examples/values-example", tones={"example-not-a-real-token": "bad"})
    + rec(SEC, "kubectl get secret sh.helm.release.v1.leaky.v1", step=1, tones={"apiToken": "bad"})
    + rec(SEC, "kubectl create secret generic shop-db-external", step=2, cmd="helm template shop charts/bookshop --set database.existingSecret=shop-db-external ...",
          tones={"shop-db-external": "ok"}),
    "bash (recorded)"), [
    S("Values files end up in Git. And dash dash set is not safer: the value is stored in the release record.", zoom=1.3),
    S("Here it is, read back with nothing but kubectl: base sixty-four, base sixty-four again, gzip. Encoding, not "
      "encryption. Anyone who can read Secrets in the namespace can read it.", zoom=1.3),
    S("The safe patterns: generate the password in the cluster, or reference an existing Secret by name. With existing "
      "secret set, the chart renders no Secret at all: every service and the database point at the named one, and the "
      "password never passes through Helm.", zoom=1.3),
])

# ---------------------------------------------------------------- 21. Troubleshooting
scene("Troubleshooting", "troubleshooting/README.md", "Investigate like you would in production", checklist([
    (0, "Render", "is the chart valid? helm lint, helm template --debug"),
    (1, "Compare", "is what Helm applied what I meant? helm get values / manifest, history, a diff with the cluster"),
    (2, "Observe", "what does Kubernetes say? pods, describe, events, endpoints, logs"),
    (3, "Fix through Helm", "in values or the chart, never only in the cluster; then upgrade --wait"),
    (4, "Verify", "helm test, the application itself; a second fault can hide behind the first"),
]), [
    S("Twelve broken deployments, and one method. Render first: is the chart even valid?"),
    S("Compare: is what Helm applied what you meant? Values, manifest, history."),
    S("Observe: what does Kubernetes say about the objects?"),
    S("Fix through Helm, in values or the chart, never only in the cluster."),
    S("And verify, with a test and the application itself. Three of the twelve, the ones that surprise most people."),
])

scene(None, "Recorded · troubleshooting/04", "A failed upgrade that still broke the site", terminal(
    rec(TS["04-wrong-service-selector"], "helm upgrade demo labs/work/ts04", tones={"immutable": "bad"}, drop="level=WARN", wrap=118)
    + rec(TS["04-wrong-service-selector"], "curl -s http://trouble.localhost:8080/; echo", step=1, tones={"no available": "bad"})
    + rec(TS["04-wrong-service-selector"], "kubectl get service demo-demo-app --namespace trouble -o jsonpath", step=2, tones={"component": "bad"}, width=150),
    "bash (recorded)"), [
    S("A tidy-up adds a label to the selector helper. The upgrade fails: a Deployment's selector is immutable.", zoom=1.2),
    S("So nothing changed? The site is down.", zoom=1.4),
    S("The Service accepted the new selector before the Deployment was rejected. Helm stops at the first error and does "
      "not undo what it applied. No Pod matches, no endpoints. A rollback restores one consistent revision.", zoom=1.25),
])

scene(None, "Recorded · troubleshooting/11", "Helm 4 and server-side apply: a conflict", terminal(
    rec(TS["11-failed-helm-test"], "helm get manifest demo --namespace trouble", cmd="helm get manifest demo | kubectl diff --server-side ...",
        tones={"prod": "bad", "dev": "ok"})
    + rec(TS["11-failed-helm-test"], "helm upgrade demo charts/demo-app --namespace trouble -f troubleshooting/values-trouble.yaml --wait", step=1,
          out_has="conflict", tones={"conflict": "bad"}, drop="level=WARN", wrap=118)
    + rec(TS["11-failed-helm-test"], "--force-conflicts --wait", step=2, tones={"deployed": "ok"}),
    "bash (recorded)"), [
    S("Someone patched a ConfigMap with kubectl during debugging. The test fails; the diff of Helm's manifest against the "
      "cluster shows the drift: prod instead of dev.", zoom=1.35),
    S("The repair fails too. Helm four applies with server side apply, which records an owner for every field, and "
      "kubectl patch now owns this one. Helm refuses to overwrite it silently.", zoom=1.25),
    S("We know the manual change was wrong, so Helm takes the field back: dash dash force conflicts. A safety net, used "
      "deliberately.", zoom=1.35),
])

scene(None, "Recorded · troubleshooting/12", "A value that arrived and did nothing", terminal(
    rec(TS["12-values-conflict"], "helm get values demo --namespace trouble | grep", tones={"replicaCount: 5": "ok"})
    + rec(TS["12-values-conflict"], "helm get manifest demo --namespace trouble | grep", step=1, tones={"HorizontalPodAutoscaler": "warn", "minReplicas: 3": "warn"}),
    "bash (recorded)"), [
    S("Production, autoscaling, and a request for five replicas with dash dash set. Still three Pods. Did the value "
      "arrive? Yes: precedence worked.", zoom=1.35),
    S("But the rendered Deployment has no replicas field at all, and an autoscaler with a minimum of three. The template "
      "ignores replica count when autoscaling is on. Precedence decides a key's value; the chart decides whether it "
      "matters. Scale through the autoscaler's minimum, in a values file.", zoom=1.3),
])

scene(None, "Recorded · labs/15-troubleshooting.md", "Two faults, one method", terminal(
    rec(L["15-troubleshooting"], "bash troubleshooting/triage.sh mystery trouble", nth=0, grep="STATUS:|ErrImagePull|Failed to pull|tag:|containerPort",
        tones={"Err": "bad", "Failed": "bad", "failed": "bad"}, width=140)
    + rec(L["15-troubleshooting"], "bash troubleshooting/triage.sh mystery trouble | sed", step=1, grep="Running|probe failed",
          tones={"probe failed": "bad"}, width=140),
    "bash (recorded)"), [
    S("Lab fifteen: a release with more than one fault. The triage script prints Helm's view and Kubernetes' view in one "
      "screen. First anomaly: the image tag one point zero does not exist.", zoom=1.2),
    S("Fix it, triage again: now the Pod runs, but its probes fail on port three thousand. A second fault was hiding "
      "behind the first. One hypothesis, one fix, verify, repeat.", zoom=1.2),
])

# ---------------------------------------------------------------- 22. Production-style chart
scene("Production-Style Chart", "docs/16-production-style-chart.md", "Every technique answers a problem from chapter three", notes([
    (0, "range over services", "5 Deployments and Services from one template"),
    (1, "values-dev/staging/prod", "3, 9 and 32 lines instead of 458-line copies"),
    (2, "tpl + lookup + keep", "URLs from the release name · a password nobody types, stable across upgrades"),
    (3, "dependency + condition", "PostgreSQL bundled for dev, external in production"),
    (4, "hook · test · NOTES", "a report per deployment · a one-command check · what to do next"),
    (5, "HPA + PDB (prod only)", "autoscaling and safe node maintenance where it matters"),
]), [
    S("The production style chart reads like a list of answers. Five near-identical blocks become one template that "
      "ranges over the services."),
    S("The environment folders become values files: three, nine and thirty-two lines."),
    S("URLs that depend on the release are built with T P L; the database password is generated once, read back with "
      "lookup on every upgrade, and kept when the release is uninstalled, because the volume outlives it."),
    S("The database is a dependency with a condition."),
    S("A hook, a test and NOTES make it operable."),
    S("And production adds an autoscaler and disruption budgets."),
])

scene(None, "Recorded · docs/16-production-style-chart.md", "Three environments, one chart version", terminal(
    rec(PROD, "for env in dev staging prod; do\n  echo \"== $env", wrap=118, tones={"PodDisruptionBudget": "ok"})
    + rec(PROD, "echo \"$env: $(helm test", step=1, tones={"Succeeded": "ok"}),
    "bash (recorded)"), [
    S("Dev and staging: the same objects. Production adds the autoscaler and five disruption budgets.", zoom=1.2),
    S("And the gate a promotion pipeline uses: the test of every environment. Succeeded, succeeded, succeeded.", zoom=1.4),
])

# ---------------------------------------------------------------- 23. Capstone
scene("Capstone", "labs/16-capstone.md", "Nineteen steps, raw YAML to a managed platform", checklist([
    (0, "1-2", "Deploy with raw YAML", "find the duplication"),
    (1, "3-8", "Build the chart", "templates, values, dev / staging / prod files"),
    (2, "9-12", "Lint, render, install, verify", "the release shop in bookshop-staging"),
    (3, "13", "Upgrade", "node-api 1.1.0 through a reviewed overlay file"),
    (4, "14-16", "Break, troubleshoot, roll back", "a java-api tag that was never published"),
    (5, "17-19", "Test, history, clean up", "and promote the tested state to production"),
]), [
    S("The capstone runs the whole life cycle. Deploy staging with raw YAML and measure the duplication."),
    S("Build the chart, or study the reference one."),
    S("Lint and render for every environment, install, verify."),
    S("Upgrade node A P I to one point one point zero, through a small overlay file, reviewed as a diff."),
    S("Break the next upgrade, investigate it, roll back."),
    S("Test, read the history, clean up."),
])

scene(None, "Recorded · labs/16-capstone.md", "Upgrade, break, roll back, test", terminal(
    rec(L["16-capstone"], "helm template shop charts/bookshop --namespace bookshop-staging --skip-tests", cmd="helm template ... -f node-api-1.1.0.yaml | kubectl diff ...",
        grep="image:", tones={"+": "ok", "-": "bad"})
    + rec(L["16-capstone"], "--set services.java-api.image.tag=2.0.0", step=1, tones={"FAILED": "bad"}, drop="level=WARN|^\\.\\.\\.", wrap=118)
    + rec(L["16-capstone"], "helm test shop --namespace bookshop-staging --logs | sed", step=2, grep="java-api|node-api|passed",
          tones={"1.1.0": "ok", "passed": "ok"}),
    "bash (recorded)"), [
    S("The upgrade, previewed: only node A P I's image changes.", zoom=1.4),
    S("Then a java A P I tag that was never published: the upgrade fails, the old Pod keeps serving.", zoom=1.3),
    S("Roll back to revision two, and the test proves the state: java A P I back on one point zero, node A P I on one "
      "point one, all checks passed.", zoom=1.35),
])

scene(None, "Recorded · labs/16-capstone.md", "The story of the week, in four lines", terminal(
    rec(L["16-capstone"], "helm history shop --namespace bookshop-staging | cut -c1-120", width=130,
        tones={"failed": "bad", "Rollback to 2": "ok", "deployed": "ok"}),
    "bash (recorded)"), [
    S("Read the history as a story: installed, node A P I one point one, a failed java A P I promotion, rolled back to "
      "two. And production runs chart one point two point one, staging one point two point zero: the chart version "
      "tells you which package each environment runs. Nothing about this needs a meeting to reconstruct.", zoom=1.2),
])

# ---------------------------------------------------------------- 24. Cleanup
scene("Cleanup", "Recorded · labs/cleanup.md + challenges/README.md", "Clean up, then build your own", terminal(
    rec(CH, "helm test web --namespace challenges --filter name=web-test-health --logs", tail=3, nth=0, tones={"confirmed": "ok"})
    + rec(L["cleanup"], "kind delete cluster --name helm-lab", step=1, tones={"Deleted": "ok"}),
    "bash (recorded)"), [
    S("Twelve challenges build one chart from an empty folder: values, environments, a ConfigMap, an Ingress, a "
      "helper, an upgrade, a rollback, a dependency, a test, and a broken release to fix.", zoom=1.3),
    S("And the cleanup: uninstall, remove the repositories, delete the cluster.", zoom=1.4),
])

scene(None, "Final review", "You can now explain, and show", svg(
    box(0, 0, 0, 540, 170, "⎈", "Why Helm exists", ["one chart instead of copies"], "blue")
    + box(0, 590, 0, 540, 170, "📦", "How charts work", ["versions, values, templates"], "blue")
    + box(0, 1180, 0, 540, 170, "🔁", "Releases", ["install, upgrade, rollback"], "ok", "#0f2a22")
    + box(1, 0, 220, 540, 170, "🌍", "Environments", ["one version, many values"], "amber", "#2b2410")
    + box(1, 590, 220, 540, 170, "🧩", "Ecosystem", ["repositories, dependencies"], "violet", "#221a3a")
    + box(1, 1180, 220, 540, 170, "🧪", "Hooks and tests", ["used deliberately"], "ok", "#0f2a22")
    + box(2, 0, 440, 540, 170, "🔐", "Security", ["review, least privilege"], "bad", "#2a1520")
    + box(2, 590, 440, 540, 170, "🔧", "Troubleshooting", ["a method, twelve failures"], "bad", "#2a1520")
    + box(2, 1180, 440, 540, 170, "🏭", "Production chart", ["and a full lifecycle"], "ok", "#0f2a22")
), [
    S("You can now explain why Helm exists, how charts, values and templates work, and how to manage releases."),
    S("How to run many environments from one chart, use repositories and dependencies, and use hooks and tests "
      "deliberately."),
    S("And how to review a chart's security, troubleshoot with a method, and operate a production style chart through "
      "its whole life cycle. Everything is in the free repository. Thanks for watching."),
])
