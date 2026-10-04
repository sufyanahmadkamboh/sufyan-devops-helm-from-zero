# Helm cheat sheet

Helm 4.3. `REL` = release name, `CHART` = folder, `.tgz`, `repo/chart` or `oci://...`, `NS` = namespace.

## Charts

| Command | Does |
|---|---|
| `helm create NAME` | new chart skeleton |
| `helm lint CHART [-f values.yaml] [--strict]` | validate |
| `helm template REL CHART [-f v.yaml] [--set k=v] [-n NS]` | render to YAML, no cluster |
| `helm template ... --show-only templates/x.yaml` | one file |
| `helm template ... --output-dir DIR` | one file per object |
| `helm template ... --debug` | render even invalid YAML |
| `helm package CHART [--version X] [--app-version Y] [-d DIR]` | → `NAME-X.tgz` |
| `helm show chart\|values\|readme\|all CHART [--version X]` | inspect any chart |
| `helm pull CHART --version X [--untar]` | download |
| `helm dependency list\|update\|build CHART` | subcharts, `Chart.lock`, `charts/` |

## Releases

| Command | Does |
|---|---|
| `helm install REL CHART -n NS --create-namespace -f v.yaml --wait --timeout 5m` | install |
| `helm upgrade --install REL CHART -n NS -f v.yaml --wait` | install or upgrade (pipelines) |
| `helm upgrade ... --rollback-on-failure` | roll back automatically if it fails |
| `helm upgrade ... --force-conflicts` | take over fields changed by other tools (server-side apply) |
| `helm install ... --dry-run=server` | render with the cluster, validate, create nothing |
| `helm list [-A] [--filter REGEX]` | releases |
| `helm status REL -n NS` | status + NOTES |
| `helm history REL -n NS` | revisions |
| `helm get values\|manifest\|notes\|hooks\|metadata\|all REL [--revision N] [--all]` | what a revision contains |
| `helm rollback REL N -n NS --wait` | back to revision N (as a new revision) |
| `helm test REL -n NS [--logs] [--filter name=POD]` | run the chart's tests |
| `helm uninstall REL -n NS --wait` | remove objects and history |

## Repositories and registries

| Command | Does |
|---|---|
| `helm repo add NAME URL` / `helm repo update [NAME]` / `helm repo list` / `helm repo remove NAME` | HTTP repositories |
| `helm search repo WORD [--versions]` | search added repos |
| `helm search hub WORD` | search Artifact Hub |
| `helm registry login HOST` | OCI login |
| `helm push NAME-X.tgz oci://HOST/PATH` | publish to OCI |
| `helm install REL oci://HOST/PATH/NAME --version X` | install from OCI |

## Values precedence

```text
 chart values.yaml  <  -f first.yaml  <  -f second.yaml  <  --set / --set-string / --set-json / --set-file
 maps merge · lists replace · null deletes · --reuse-values keeps the last release's values (prefer passing files)
```

## Templates

| Construct | Example |
|---|---|
| value | `{{ .Values.replicaCount }}` |
| release / chart | `{{ .Release.Name }}`, `{{ .Release.Namespace }}`, `{{ .Chart.AppVersion }}` |
| default | `{{ .Values.image.tag \| default .Chart.AppVersion }}` |
| quote | `{{ .Values.environment \| quote }}` |
| if / else | `{{- if .Values.ingress.enabled }} ... {{- else }} ... {{- end }}` |
| range | `{{- range $k, $v := .Values.config }}{{ $k }}: {{ $v \| quote }}{{- end }}` |
| with | `{{- with .Values.nodeSelector }}nodeSelector: {{- toYaml . \| nindent 2 }}{{- end }}` |
| helper | `{{- define "x.labels" -}}...{{- end }}` / `{{- include "x.labels" . \| nindent 4 }}` |
| map/YAML block | `{{- toYaml .Values.resources \| nindent 12 }}` |
| required | `{{ required "image.repository is required" .Values.image.repository }}` |
| values as templates | `{{ tpl .Values.url . }}` |
| restart on config change | `checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . \| sha256sum }}` |
| read from cluster | `{{ lookup "v1" "Secret" .Release.Namespace "name" }}` |
| stop with an error | `{{ fail "message" }}` |
| whitespace | `{{-` trims before, `-}}` trims after |

## Annotations

| Annotation | Effect |
|---|---|
| `helm.sh/hook: pre-install,post-upgrade,test,...` | run at that moment |
| `helm.sh/hook-weight: "-5"` | order among hooks (low first) |
| `helm.sh/hook-delete-policy: before-hook-creation\|hook-succeeded\|hook-failed` | cleanup of hook objects |
| `helm.sh/resource-policy: keep` | `helm uninstall` leaves this object |

## Troubleshooting

```bash
troubleshooting/triage.sh REL NS                                 # Helm + Kubernetes view in one screen
helm history REL -n NS                                           # what happened
diff <(helm get values REL -n NS --revision 2) <(helm get values REL -n NS --revision 3)
helm get manifest REL -n NS | kubectl diff --server-side --field-manager=helm -n NS -f -   # drift
kubectl get pods,endpointslices -n NS; kubectl describe pod POD -n NS; kubectl logs POD -n NS [--previous]
kubectl get events -n NS --sort-by=.lastTimestamp | tail
```

| Message | Usually |
|---|---|
| `unexpected EOF` | missing `{{ end }}` |
| `YAML parse error on ...` | indentation (`nindent`) |
| `cannot reuse a name that is still in use` | use `helm upgrade --install` |
| `another operation (install/upgrade/rollback) is in progress` | interrupted operation → `helm rollback REL LAST_GOOD` |
| `field is immutable` | changed selector → new release / recreate |
| `conflict with "kubectl-..."` | field changed outside Helm → decide, then `--force-conflicts` |
| `missing in charts/ directory` | `helm dependency build` |
| `context deadline exceeded` with `--wait` | Pods never Ready → `kubectl describe pod` |
| `ImagePullBackOff` | wrong image/tag, or no pull credentials |
| `CreateContainerConfigError` | missing ConfigMap/Secret/key |
