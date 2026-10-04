"""Chapters 12-15: install a release, upgrade, rollback, environment values."""

from __future__ import annotations

from components import arrow, box, code, label, notes, svg, terminal
from recordings import rec
from scenes_common import L, S, lines, scene, src

PROD = src("charts/demo-app/values-prod.yaml")

# ---------------------------------------------------------------- 12. Install release
scene("Install Release", "Recorded · labs/07-install-release.md", "A Helm installation creates a release", terminal(
    rec(L["07-install-release"], "helm install demo charts/demo-app", head=12, tones={"deployed": "ok"})
    + rec(L["07-install-release"], "kubectl get pods --namespace demo-dev -L", step=1, tones={"dev": "ok"}),
    "bash (recorded)"), [
    S("Install demo app as release demo, in namespace demo dev, with the dev values, and wait until it is ready. "
      "Revision one, deployed, and the NOTES: what runs, where to open it, how to check it.", zoom=1.15),
    S("Every Pod carries the chart's labels: which release, which version, which environment.", zoom=1.35),
])

scene(None, "Recorded · labs/07-install-release.md", "What did it get, what did Helm apply, where does it live?", terminal(
    rec(L["07-install-release"], "helm get values demo --namespace demo-dev")
    + rec(L["07-install-release"], "helm get metadata demo --namespace demo-dev", step=1, grep="CHART|VERSION|REVISION|STATUS|APPLY", tones={"server-side": "ok"})
    + rec(L["07-install-release"], "kubectl get secrets --namespace demo-dev -l owner=helm", step=2, width=150, tones={"sh.helm": "ok"}),
    "bash (recorded)"), [
    S("helm get values: exactly what this release was given.", zoom=1.3),
    S("helm get metadata: chart, versions, revision, status, and Helm four's apply method: server side apply.", zoom=1.3),
    S("And the release itself is a Secret in the namespace, one per revision, holding the chart, the values and the "
      "rendered manifest. That is why your teammates see the same releases, and why rollback can restore any revision.", zoom=1.3),
])

scene(None, "Recorded · labs/07-install-release.md", "Uninstall, and verify what is left", terminal(
    rec(L["07-install-release"], "helm uninstall tmp --namespace demo-tmp --wait", tones={"uninstalled": "ok"})
    + rec(L["07-install-release"], "helm list --namespace demo-tmp", step=1, tones={"No resources": "ok", "Active": "warn"}),
    "bash (recorded)"), [
    S("helm uninstall removes every object of the release and its history.", zoom=1.4),
    S("Verify: no release, no objects with its label. But the namespace is still there: it was never part of the "
      "release. Volumes of StatefulSets, objects marked keep, and hook objects stay too. After an uninstall, check the "
      "namespace, not just helm list.", zoom=1.3),
])

# ---------------------------------------------------------------- 13. Upgrade
scene("Upgrade", "Recorded · labs/08-upgrade.md", "Review the change before you apply it", terminal(
    rec(L["08-upgrade"], "--set replicaCount=2 --set config.adminUrl=http://admin.example.com \\\n  | kubectl diff",
        cmd="helm template demo ... --set replicaCount=2 --set config.adminUrl=... | kubectl diff --server-side ...",
        tones={"+": "ok", "-": "bad"}),
    "bash (recorded)"), [
    S("Before upgrading, render the new state and let the A P I server compare it with what runs. Three changes: two "
      "replicas, the admin link in the ConfigMap, and the checksum annotation, which tells you the Pods will be "
      "replaced so they pick up the new configuration. Review the result, not the values file.", zoom=1.45),
])

scene(None, "Recorded · labs/08-upgrade.md", "helm upgrade → rolling update", terminal(
    rec(L["08-upgrade"], "kubectl rollout status deployment/demo-demo-app --namespace demo-dev\nkubectl rollout history", tones={"successfully": "ok"})
    + rec(L["08-upgrade"], "helm history demo --namespace demo-dev", step=1, nth=0, tones={"deployed": "ok"}),
    "bash (recorded)"), [
    S("Helm updates the Deployment; Kubernetes does the rolling update: a new ReplicaSet, new Pods ready, old Pods "
      "removed. Two Deployment revisions on the Kubernetes side.", zoom=1.35),
    S("And on the Helm side, the release history: revision three, upgrade complete. Helm manages the release; "
      "Kubernetes manages the workload.", zoom=1.35),
])

scene(None, "Recorded · labs/08-upgrade.md", "The upgrade that succeeded and broke everything", terminal(
    rec(L["08-upgrade"], "curl -s http://demo-dev.localhost:8080/config.js; echo", nth=1, tones={"404": "bad"})
    + rec(L["08-upgrade"], "helm history demo --namespace demo-dev | tail -2", step=1, tones={"replicaCount: 3": "bad"}),
    "bash (recorded)"), [
    S("A colleague just wants three replicas, quickly: helm upgrade, set replica count three. Deployed. And the "
      "application is gone from its address.", zoom=1.4),
    S("Let's investigate this like we would in production. The latest revision's values contain only replica count. "
      "The dev file was not passed, so the release fell back to the chart's defaults: no Ingress, environment local. "
      "Helm upgrade uses only the values in this command. The values files are part of the deployment command: keep it "
      "in a script, not in someone's memory.", zoom=1.3),
])

# ---------------------------------------------------------------- 14. Rollback
scene("Rollback", "Recorded · labs/09-rollback.md", "Deploy a bad version on purpose", terminal(
    rec(L["09-rollback"], "--set image.tag=1.0.1-hotfix \\\n  --wait --timeout 60s", cmd="helm upgrade demo ... --set image.tag=1.0.1-hotfix --wait --timeout 60s",
        tones={"FAILED": "bad"}, drop="level=WARN", wrap=118)
    + rec(L["09-rollback"], "kubectl get pods --namespace demo-rollback", step=1, nth=0, tones={"ErrImagePull": "bad", "ImagePullBackOff": "bad", "Running": "ok"})
    + rec(L["09-rollback"], "curl -s http://demo-rollback.localhost:8080/config.js; echo", step=2, nth=1, tones={"admin": "ok"}),
    "bash (recorded)"), [
    S("Revision three: an image tag that was never published. With dash dash wait, Helm watched for sixty seconds, the "
      "Deployment never became ready, and the revision is marked failed.", zoom=1.3),
    S("On the Kubernetes side: the new Pod cannot pull its image. The old Pod is still running.", zoom=1.35),
    S("And the application still answers. The rolling update never removes an old Pod before a new one is ready. "
      "Kubernetes protected the users; the release is still in a failed state.", zoom=1.35),
])

scene(None, "Recorded · labs/09-rollback.md", "This is where Helm history becomes useful", terminal(
    rec(L["09-rollback"], "helm rollback demo 2 --namespace demo-rollback", tones={"success": "ok"})
    + rec(L["09-rollback"], "helm history demo --namespace demo-rollback\nhelm status", step=1, drop=r"^(STATUS|REVISION):",
          tones={"failed": "bad", "Rollback to 2": "ok"}, width=130),
    "bash (recorded)"), [
    S("Back to the last good revision, two: rollback was a success.", zoom=1.4),
    S("History is never rewritten. The rollback is a new revision, four, a copy of revision two. The record shows "
      "exactly what happened, including the failure. And remember: a rollback restores objects and values, not data.", zoom=1.3),
])

scene(None, "Recorded · labs/09-rollback.md", "Automatic rollback, and a release that is stuck", terminal(
    rec(L["09-rollback"], "--rollback-on-failure --timeout 60s", cmd="helm upgrade demo ... --set image.tag=1.0.1-hotfix --rollback-on-failure",
        grep="rolled back", tones={"rolled back": "warn"}, wrap=118)
    + rec(L["09-rollback"], "helm upgrade demo charts/demo-app --namespace demo-rollback", step=1, out_has="another operation",
          cmd="helm upgrade demo ...      # after an upgrade was killed half-way", tones={"in progress": "bad"}, wrap=118)
    + rec(L["09-rollback"], "helm history demo --namespace demo-rollback | tail -3", step=2, out_has="Rollback to 6",
          cmd="helm rollback demo 6 ...; helm history demo | tail -3", tones={"pending-upgrade": "warn", "Rollback to 6": "ok"}, width=130),
    "bash (recorded)"), [
    S("dash dash rollback on failure does it automatically: the upgrade fails, Helm rolls back to the previous revision "
      "immediately.", zoom=1.3),
    S("And the one you will meet in real life: a deployment interrupted half-way, a cancelled pipeline. The next upgrade "
      "says another operation is in progress. It is not: the process that started it is dead.", zoom=1.3),
    S("Helm wrote the revision as pending upgrade before applying, and only that process could have completed it. The "
      "way out is a rollback to the last good revision. Check that nobody is really deploying first.", zoom=1.25),
])

# ---------------------------------------------------------------- 15. Environment values
scene("Environment Values", "charts/demo-app/values-prod.yaml", "Only what differs", code(
    "charts/demo-app/values-prod.yaml", PROD, "yaml", 21) + notes([
    (0, "values-dev.yaml", "9 lines: environment, 1 replica, dev host"),
    (0, "values-staging.yaml", "9 lines: 2 replicas, staging host"),
    (1, "values-prod.yaml", "22 lines: pinned tag, autoscaling, resources, host"),
]), [
    S("One chart, three environment files, each with only what differs from the defaults. Dev and staging: nine lines "
      "each."),
    S("Production pins the image tag explicitly, replaces the fixed replica count with an autoscaler between three and "
      "six, and gets more C P U and memory.", hl=lines(PROD, "image:", "memory: 256Mi")),
], layout="code")

scene(None, "Recorded · labs/10-environments.md", "One chart version, three environments", terminal(
    rec(L["10-environments"], "kubectl get deployments --all-namespaces -l app.kubernetes.io/name=demo-app",
        drop="demo-rollback", tones={"prod": "ok", "staging": "ok", " dev": "ok"}, width=140)
    + rec(L["10-environments"], "for host in demo-dev demo-staging demo; do", step=1, drop=r"^$", tones={"APP_ENV": "ok"})
    + rec(L["10-environments"], "diff <(helm get values demo --namespace demo-staging)", step=2, head=10),
    "bash (recorded)"), [
    S("helm upgrade dash dash install, the same command for every environment. Dev with one replica, staging with "
      "two, production with three, kept by the autoscaler.", zoom=1.25),
    S("Each environment answers with its own configuration.", zoom=1.35),
    S("And the differences between staging and production are exactly the values: nothing else. Every environment runs "
      "the same chart version, so a change is tested with the templates that will reach production.", zoom=1.3),
])
