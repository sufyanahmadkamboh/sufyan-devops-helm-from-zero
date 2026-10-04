"""Chapters 5-11: first chart, chart structure, Chart.yaml, values.yaml, templates, rendering, lint."""

from __future__ import annotations

from components import code, notes, terminal
from recordings import rec
from scenes_common import L, S, excerpt, lines, scene, src

CHART_YAML = src("charts/demo-app/Chart.yaml")
# the Deployment template without its comment lines (the comments explain each construct in the file itself)
BASIC = "\n".join(x for x in excerpt("examples/basic-chart/templates/deployment.yaml", "spec:", "imagePullPolicy: IfNotPresent")
                   .splitlines() if not x.strip().startswith("#"))

# ---------------------------------------------------------------- 5. Create first chart
scene("Create First Chart", "Recorded · labs/02-first-chart.md", "helm create, lint, install, test", terminal(
    rec(L["02-first-chart"], "find labs/work/hello | sort", drop=r"^labs/work/hello$")
    + rec(L["02-first-chart"], "helm install hello labs/work/hello", step=1, head=6, tones={"deployed": "ok"})
    + rec(L["02-first-chart"], "helm test hello --namespace lab-02", step=2, nth=0, grep="Phase|TEST SUITE", tones={"Succeeded": "ok"}),
    "bash (recorded)"), [
    S("helm create generates a complete, conventional chart: Chart.yaml, values.yaml, and templates for a Deployment, a "
      "Service, an Ingress, an autoscaler, a service account, helpers, NOTES, and a test. Don't delete what you don't "
      "understand yet: this skeleton is what most charts in the world look like.", zoom=1.1),
    S("Install it, and you have a release: name hello, revision one, status deployed. The NOTES come from a template "
      "too.", zoom=1.25),
    S("helm test runs the chart's test Pod: it calls the Service from inside the cluster. Succeeded.", zoom=1.35),
])

scene(None, "Recorded · labs/02-first-chart.md", "Break it, then make it ours", terminal(
    rec(L["02-first-chart"], "sed -i.bak 's/^name: hello/name:/'", grep="ERROR|failed", tones={"ERROR": "bad", "failed": "bad"}, wrap=118)
    + rec(L["02-first-chart"], "helm test hello --namespace lab-02 | grep Phase", step=1, tones={"Succeeded": "ok", "bookshop": "ok"}),
    "bash (recorded)"), [
    S("Now let's intentionally break it: a chart without a name. helm lint reports it, and exits with an error, so a "
      "pipeline would stop here.", zoom=1.25),
    S("The challenge: deploy our application instead of nginx, the Bookshop frontend on port eight thousand eighty, "
      "with values only, no template edits. The test passes against the new image.", zoom=1.3),
])

# ---------------------------------------------------------------- 6. Chart structure
scene("Chart Structure", "Recorded · labs/03-chart-structure.md", "Inspect it like a consumer", terminal(
    rec(L["03-chart-structure"], "helm show values charts/demo-app", head=12)
    + rec(L["03-chart-structure"], "grep -n 'define' charts/demo-app/templates/_helpers.tpl", step=1),
    "bash (recorded)"), [
    S("charts slash demo app is the Bookshop frontend packaged with Helm. Most of the time you will install charts other "
      "people wrote, so read them first: helm show chart, helm show values, helm show readme. The values are the "
      "chart's interface: every setting, its default, and a comment.", zoom=1.1),
    S("The helpers file defines named templates: the full name, and the labels every object will carry.", zoom=1.3),
])

scene(None, "Recorded · labs/03-chart-structure.md", "From scaffold to chart: three changes, three reasons", terminal(
    rec(L["03-chart-structure"], "helm create labs/work/scaffold/demo-app", tones={">": "ok", "<": "bad"}), "bash (recorded)"), [
    S("What changed compared with a fresh scaffold? A checksum of the ConfigMap as a Pod annotation: change the "
      "configuration, and the Pods are replaced. A separate container port. And the ConfigMap passed to the container "
      "as environment variables. Every change has a reason you can say out loud.", zoom=1.1),
])

# ---------------------------------------------------------------- 7. Chart.yaml
scene("Chart.yaml", "charts/demo-app/Chart.yaml", "The chart's identity card", code(
    "charts/demo-app/Chart.yaml", CHART_YAML, "yaml", 23) + notes([
    (0, "apiVersion v2", "the chart format of Helm 3 and 4"),
    (1, "version", "the chart: change it whenever the chart changes"),
    (2, "appVersion", "the application: the default image tag; quote it"),
]), [
    S("Chart.yaml. apiVersion v two is the chart format, not a Kubernetes A P I. The name becomes the default for "
      "resource names and labels. Type application means installable.", hl=lines(CHART_YAML, "apiVersion", "type:")),
    S("version is the chart's own version, semantic versioning.", hl=lines(CHART_YAML, "version: 1.0.0", "version: 1.0.0")),
    S("appVersion is the application it deploys by default: the image tag, unless values override it.",
      hl=lines(CHART_YAML, "appVersion", "appVersion")),
], layout="code")

scene(None, "Recorded · labs/03-chart-structure.md", "Package it twice, then break it", terminal(
    rec(L["03-chart-structure"], "helm show chart labs/work/demo-app-1.0.1.tgz", tones={"1.1.0": "ok"})
    + rec(L["03-chart-structure"], "sed -i.bak 's/^appVersion", step=1, grep="ERROR", tones={"ERROR": "bad"}, wrap=118)
    + rec(L["03-chart-structure"], "helm template demo labs/work/broken", step=2, tones={"1.1\"": "bad"}),
    "bash (recorded)"), [
    S("helm package with dash dash version and dash dash app version: chart one point zero point one, application one "
      "point one point zero, and the rendered image follows the app version. That is how pipelines release charts.", zoom=1.3),
    S("Now an unquoted app version, one point ten. YAML reads it as a number.", zoom=1.3),
    S("One point one: the image tag that would have been deployed. Quote anything that looks like a number but is a "
      "string.", zoom=1.3),
])

# ---------------------------------------------------------------- 8. values.yaml
scene("values.yaml", "Recorded · labs/04-values.md", "Hard-coded vs configurable", terminal(
    rec(L["04-values"], "grep -nE 'replicas|image:|value:' examples/basic-chart/raw/deployment.yaml")
    + rec(L["04-values"], "helm template web examples/basic-chart --set replicaCount=3 --set environment=prod", step=1,
          tones={"replicas: 3": "ok", "prod": "ok"}),
    "bash (recorded)"), [
    S("Before Helm, every value is fixed in the file: two replicas, one image tag, environment dev. Production means a "
      "copy of the file.", zoom=1.3),
    S("With a template, replicas comes from dot Values dot replica count. Production is no longer a copy: it is a "
      "different value.", zoom=1.3),
])

scene(None, "Recorded · labs/04-values.md", "Who wins? Predict, then render", terminal(
    rec(L["04-values"], "-f examples/values-example/values-prod.yaml", tail=6, cmd="helm template demo examples/values-example -f team-defaults.yaml -f values-prod.yaml --set replicaCount=5",
        tones={"error": "warn", "\"5\"": "ok"}),
    "bash (recorded)"), [
    S("Values come from four places: the chart's values.yaml, then each dash f file in order, the later one winning, "
      "then dash dash set, which wins over everything. Log level is set three times: info, warn, error. The last file "
      "wins. Replica count is three in the prod file, five on the command line: five. And features is a map: maps are "
      "merged key by key, so reviews survived from the defaults.", zoom=1.4),
])

scene(None, "Recorded · labs/04-values.md", "A value that does nothing, and a schema that stops it", terminal(
    rec(L["04-values"], "printf 'replicacount: 3\\n'", tones={"replicas: 1": "bad"})
    + rec(L["04-values"], "helm template demo labs/work/schema-demo --set replicaCount=0", step=1, tones={"minimum": "bad"}, wrap=118),
    "bash (recorded)"), [
    S("A teammate writes replica count with a lower case c. No error, no effect: still one replica. Helm passes any key "
      "to the templates; only the keys a template reads matter.", zoom=1.3),
    S("A values schema turns that into an error. With a minimum of one, replica count zero is rejected at lint, "
      "template and install time.", zoom=1.3),
])

# ---------------------------------------------------------------- 9. Templates
scene("Templates", "examples/basic-chart/templates/deployment.yaml", "Every construct, used once", code(
    "examples/basic-chart/templates/deployment.yaml", BASIC,
    "yaml", 19) + notes([
    (0, ".Values", "anything from values.yaml, -f files or --set"),
    (1, "default · quote", "fallback when empty · always a string"),
    (2, ".Release", "name, namespace, revision of this install"),
    (3, "if / else", "render one branch or the other"),
]), [
    S("Templates are Kubernetes YAML with placeholders. Double curly braces, dot Values for settings.",
      hl=lines(BASIC, "replicas:", "replicas:")),
    S("Pipes and functions: default falls back to the app version when the tag is empty; quote makes sure an "
      "environment variable is always a string.",
      hl=lines(BASIC, "image:", "value: {{ .Values.environment")),
    S("Dot Release tells the template about this installation: its name, its namespace, its revision.",
      hl=lines(BASIC, "name: RELEASE", "Release.Revision")),
    S("And if, else: production always pulls the image, the other environments only when it is missing.",
      hl=lines(BASIC, "if eq .Values.environment", "imagePullPolicy: IfNotPresent")),
], layout="code")

scene(None, "Recorded · labs/05-templates.md", "Change values, watch the output", terminal(
    rec(L["05-templates"], "--set environment=prod --show-only templates/deployment.yaml", tones={"Always": "ok"})
    + rec(L["05-templates"], "--set config.CACHE_TTL=300", step=1, tail=4, tones={"CACHE_TTL": "ok"})
    + rec(L["05-templates"], "curl -s http://basic.localhost:8080/config.js", step=2, tones={"dev": "ok"}),
    "bash (recorded)"), [
    S("Environment prod: the else branch is gone, image pull policy Always.", zoom=1.35),
    S("range over a map: add a key in values, get a line in the ConfigMap, no template change. And quote turned the "
      "number three hundred into the string a ConfigMap requires.", zoom=1.35),
    S("Installed for real: the application received the environment, and every Pod carries the environment and team "
      "labels from one helper.", zoom=1.3),
])

scene(None, "Recorded · labs/05-templates.md", "Don't trust the template just because Helm accepted it", terminal(
    rec(L["05-templates"], "sed -i.bak '/{{- end }}/d'", tones={"EOF": "bad"}, drop=r"^$|debug flag")
    + rec(L["05-templates"], "helm template web labs/work/tpl --show-only templates/deployment.yaml | sed -n", step=1,
          tones={"  app.kubernetes.io": "bad", "  environment": "bad", "  team": "bad"}),
    "bash (recorded)"), [
    S("Two classic mistakes. A forgotten end: unexpected E O F, the parser reached the end of the file with a block "
      "still open.", zoom=1.35),
    S("The dangerous one: an indentation of two instead of four. helm lint passes. Rendering works. The A P I server "
      "accepts the dry run. But look: the labels are no longer under labels. They are unknown fields directly under "
      "metadata, and the Deployment would be created without them. Only reading the output, or a strict schema check "
      "like kube conform, catches this.", zoom=1.25),
])

# ---------------------------------------------------------------- 10. Render templates
scene("Render Templates", "Recorded · labs/06-rendering.md", "helm template: what Kubernetes will receive", terminal(
    rec(L["06-rendering"], "grep -E '^(# Source|kind):'")
    + rec(L["06-rendering"], "first=$(helm template shop", step=1, cmd="helm template shop charts/bookshop   # twice, compare DB_PASSWORD", tones={"different": "warn"})
    + rec(L["06-rendering"], "--dry-run=server", step=2, head=5, tones={"pending-install": "ok"}),
    "bash (recorded)"), [
    S("Helm is rendering templates into normal Kubernetes YAML before Kubernetes receives them. Each object comes with "
      "the template it came from.", zoom=1.2),
    S("helm template runs without a cluster. The bookshop chart reads its database password back from the cluster with "
      "lookup; with no cluster, each render generates a new one. Expected here, and the reason you never apply helm "
      "template output to upgrade a release.", zoom=1.3),
    S("dash dash dry run equals server renders with the real cluster and lets the A P I server validate every object, "
      "without creating anything: pending install.", zoom=1.3),
])

# ---------------------------------------------------------------- 11. Helm lint
scene("Helm Lint", "Recorded · labs/06-rendering.md", "Three mistakes, reported one at a time", terminal(
    rec(L["06-rendering"], "printf 'service:\\n\\tport", cmd="helm lint labs/work/lint-me -f labs/work/lint-me/values-dev.yaml",
        tones={"Error": "bad"}, wrap=118)
    + rec(L["06-rendering"], "sed -i 's/^\\tport: 8080$/", step=1, cmd="# fix 1: the tab → lint again", grep="ERROR\\] Chart", tones={"ERROR": "bad"}, wrap=118)
    + rec(L["06-rendering"], "sed -i 's/^version: latest/", step=2, cmd="# fix 2: the version → lint again", grep="ERROR", tones={"ERROR": "bad"}, wrap=118)
    + rec(L["06-rendering"], "sed -i 's/{{ .Values.containerPort }$/", step=3, cmd="# fix 3: the template → lint again", grep="linted", tones={"0 chart": "ok"}),
    "bash (recorded)"), [
    S("A chart with three mistakes: a tab in a values file, an invalid chart version, and an unclosed template action. "
      "Lint reports one: values files are parsed first.", zoom=1.2),
    S("Fix it, run again: now Chart.yaml. Latest is not a version.", zoom=1.2),
    S("Fix it: now the template, with the file and the line.", zoom=1.2),
    S("Fix it: zero charts failed. Read, fix one thing, run again. That loop is the method. And lint every environment's "
      "values, because a mistake may exist only in production's.", zoom=1.2),
])
