# Challenges

> Twelve practical challenges, one per major section of the course. They build **one chart** step by step, from an
> empty folder to a tested, multi-environment chart with a dependency, so do them in order. Each has a task,
> requirements, hints, the expected result, a tested solution, and an explanation. Try before you open the solution.

Work folder: `labs/work/challenges/` (ignored by Git). Namespace: `challenges`. Host: `http://challenge.localhost:8080`.
The application: the Bookshop frontend image, `ghcr.io/sufyanahmadkamboh/bookshop-frontend:1.0.0`, listening on 8080,
health check `/health`.

<!-- test-run: rm -rf labs/work/challenges && mkdir -p labs/work/challenges -->

---

## Challenge 1 · Create a chart from scratch

**Task.** Without `helm create`, write the smallest chart that deploys the frontend: a Deployment and a Service.

**Requirements.** Folder `labs/work/challenges/shopfront`; chart name `shopfront`, chart version `0.1.0`, app version
`1.0.0`; the image tag comes from `appVersion`; `helm lint` passes.

**Hints.** A chart needs only `Chart.yaml` and `templates/`. `apiVersion: v2`. `{{ .Chart.AppVersion }}`,
`{{ .Release.Name }}`.

**Expected result.** `helm template` prints a Deployment and a Service named after the release.

<details>
<summary>Solution</summary>

<!-- test: contains=0 chart(s) failed; output -->
```bash
mkdir -p labs/work/challenges/shopfront/templates
cat > labs/work/challenges/shopfront/Chart.yaml <<'EOF'
apiVersion: v2
name: shopfront
description: The Bookshop frontend, a chart written from scratch
type: application
version: 0.1.0
appVersion: "1.0.0"
EOF
cat > labs/work/challenges/shopfront/templates/deployment.yaml <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {{ .Release.Name }}
  template:
    metadata:
      labels:
        app: {{ .Release.Name }}
    spec:
      containers:
        - name: web
          image: "ghcr.io/sufyanahmadkamboh/bookshop-frontend:{{ .Chart.AppVersion }}"
          ports:
            - name: http
              containerPort: 8080
          readinessProbe:
            httpGet: { path: /health, port: http }
EOF
cat > labs/work/challenges/shopfront/templates/service.yaml <<'EOF'
apiVersion: v1
kind: Service
metadata:
  name: {{ .Release.Name }}
spec:
  selector:
    app: {{ .Release.Name }}
  ports:
    - port: 8080
      targetPort: http
EOF
helm lint labs/work/challenges/shopfront
```

```text
==> Linting labs/work/challenges/shopfront
[INFO] Chart.yaml: icon is recommended
[INFO] values.yaml: file does not exist

1 chart(s) linted, 0 chart(s) failed
```

</details>

**Explanation.** Everything else `helm create` generates is convention, not requirement. Starting from nothing shows
the core: metadata plus templates.

---

## Challenge 2 · Move hard-coded replicas into values.yaml

**Task.** The Deployment says `replicas: 1`. Make it configurable.

**Requirements.** A `values.yaml` with `replicaCount: 1`; the template reads it; `--set replicaCount=3` renders 3.

**Hints.** `{{ .Values.replicaCount }}`.

**Expected result.** `replicas: 1` by default, `replicas: 3` with the override.

<details>
<summary>Solution</summary>

<!-- test: contains=replicas: 3; output -->
```bash
printf 'replicaCount: 1\n' > labs/work/challenges/shopfront/values.yaml
sed -i 's/replicas: 1/replicas: {{ .Values.replicaCount }}/' labs/work/challenges/shopfront/templates/deployment.yaml
helm template web labs/work/challenges/shopfront | grep replicas
helm template web labs/work/challenges/shopfront --set replicaCount=3 | grep replicas
```

```text
  replicas: 1
  replicas: 3
```

</details>

**Explanation.** The template now describes *how* to deploy; the value says *how many*. The same file serves every
environment.

---

## Challenge 3 · Create dev, staging and prod values

**Task.** Add an `environment` value (default `local`), passed to the app as `APP_ENV`, and three environment files.

**Requirements.** `values-dev.yaml` (1 replica), `values-staging.yaml` (2), `values-prod.yaml` (3); each sets
`environment`; each contains only what differs from `values.yaml`.

**Hints.** `env:` with `value: {{ .Values.environment | quote }}`.

**Expected result.** Rendering with `values-prod.yaml` gives 3 replicas and `APP_ENV` `"prod"`.

<details>
<summary>Solution</summary>

<!-- test: contains=value: "prod"; contains=replicas: 3; output -->
```bash
cd labs/work/challenges/shopfront
printf 'environment: local\n' >> values.yaml
cat > templates/deployment.yaml <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: {{ .Release.Name }}
  template:
    metadata:
      labels:
        app: {{ .Release.Name }}
    spec:
      containers:
        - name: web
          image: "ghcr.io/sufyanahmadkamboh/bookshop-frontend:{{ .Chart.AppVersion }}"
          ports:
            - name: http
              containerPort: 8080
          env:
            - name: APP_ENV
              value: {{ .Values.environment | quote }}
          readinessProbe:
            httpGet: { path: /health, port: http }
EOF
for e in dev:1 staging:2 prod:3; do
  printf 'environment: %s\nreplicaCount: %s\n' "${e%%:*}" "${e##*:}" > "values-${e%%:*}.yaml"
done
helm template web . -f values-prod.yaml | grep -E 'replicas|value:'
cd - > /dev/null
```

```text
  replicas: 3
              value: "prod"
```

</details>

**Explanation.** Defaults in `values.yaml`, differences in small files, one `-f` per environment (lab 10).

---

## Challenge 4 · Change the image using values

**Task.** Make the image repository and tag values, with the tag defaulting to `appVersion`.

**Requirements.** `image.repository` and `image.tag` (empty) in `values.yaml`; `--set image.tag=1.0.0` and an empty
tag both render `...:1.0.0`; another repository can be set without touching the template.

**Hints.** `{{ .Values.image.tag | default .Chart.AppVersion }}`.

**Expected result.** The image line is fully driven by values.

<details>
<summary>Solution</summary>

<!-- test: contains=example.com/mirror/bookshop-frontend:1.0.0; output -->
```bash
cat >> labs/work/challenges/shopfront/values.yaml <<'EOF'
image:
  repository: ghcr.io/sufyanahmadkamboh/bookshop-frontend
  tag: ""
EOF
sed -i 's#image: "ghcr.io/sufyanahmadkamboh/bookshop-frontend:{{ .Chart.AppVersion }}"#image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"#' \
  labs/work/challenges/shopfront/templates/deployment.yaml
helm template web labs/work/challenges/shopfront | grep image:
helm template web labs/work/challenges/shopfront --set image.repository=example.com/mirror/bookshop-frontend | grep image:
```

```text
          image: "ghcr.io/sufyanahmadkamboh/bookshop-frontend:1.0.0"
          image: "example.com/mirror/bookshop-frontend:1.0.0"
```

</details>

**Explanation.** A mirror registry or a new version becomes a values change, reviewable and per environment.

---

## Challenge 5 · Add a ConfigMap

**Task.** Move `APP_ENV` into a ConfigMap, and make Pods restart when the ConfigMap changes.

**Requirements.** `templates/configmap.yaml` with `APP_ENV`; the Deployment reads it with `envFrom`; a
`checksum/config` Pod annotation.

**Hints.** `{{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}`.

**Expected result.** Changing `environment` changes the checksum.

<details>
<summary>Solution</summary>

<!-- test: contains=differ; output -->
```bash
cd labs/work/challenges/shopfront
cat > templates/configmap.yaml <<'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ .Release.Name }}-config
data:
  APP_ENV: {{ .Values.environment | quote }}
EOF
cat > templates/deployment.yaml <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: {{ .Release.Name }}
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
      labels:
        app: {{ .Release.Name }}
    spec:
      containers:
        - name: web
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          ports:
            - name: http
              containerPort: 8080
          envFrom:
            - configMapRef:
                name: {{ .Release.Name }}-config
          readinessProbe:
            httpGet: { path: /health, port: http }
EOF
a=$(helm template web . | grep checksum); b=$(helm template web . --set environment=qa | grep checksum)
[ "$a" != "$b" ] && echo "checksums differ: the Pods would restart"
cd - > /dev/null
```

```text
checksums differ: the Pods would restart
```

</details>

**Explanation.** Environment variables are read at container start; the checksum turns "config changed" into "Pod
template changed", which Kubernetes rolls out.

---

## Challenge 6 · Add an Ingress

**Task.** Expose the chart through Traefik at `challenge.localhost`, switchable.

**Requirements.** `ingress.enabled` (default false) and `ingress.host`; nothing rendered when disabled; install the
chart into namespace `challenges` with the Ingress on and reach it.

**Hints.** `{{- if .Values.ingress.enabled }}` around the whole file.

**Expected result.** `curl http://challenge.localhost:8080/config.js` shows `APP_ENV: "dev"`.

<details>
<summary>Solution</summary>

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
cd labs/work/challenges/shopfront
printf 'ingress:\n  enabled: false\n  host: challenge.localhost\n' >> values.yaml
cat > templates/ingress.yaml <<'EOF'
{{- if .Values.ingress.enabled }}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ .Release.Name }}
spec:
  ingressClassName: traefik
  rules:
    - host: {{ .Values.ingress.host | quote }}
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {{ .Release.Name }}
                port:
                  number: 8080
{{- end }}
EOF
printf 'ingress:\n  enabled: true\n' >> values-dev.yaml
helm install web . --namespace challenges --create-namespace -f values-dev.yaml --wait --timeout 3m | grep STATUS
cd - > /dev/null
```

<!-- test: retry=20; contains=APP_ENV: "dev"; output -->
```bash
curl -s http://challenge.localhost:8080/config.js; echo
```

```text
window.APP_CONFIG = { ADMIN_URL: "", APP_ENV: "dev" };
```

</details>

**Explanation.** Optional resources are wrapped in `if`; the default is the safe one (no public exposure).

---

## Challenge 7 · Create a reusable helper

**Task.** Every object should carry the same labels: name, instance, version, environment, managed-by. Write them once.

**Requirements.** `templates/_helpers.tpl` with `shopfront.labels`; every template's `metadata` uses it; the selector
stays `app: <release>` (selectors must not change on an existing release).

**Hints.** `{{- define "shopfront.labels" -}}...{{- end }}`, `{{- include "shopfront.labels" . | nindent 4 }}`.

**Expected result.** `kubectl get all,configmap,ingress -l app.kubernetes.io/instance=web -n challenges` lists everything.

<details>
<summary>Solution</summary>

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
cd labs/work/challenges/shopfront
cat > templates/_helpers.tpl <<'EOF'
{{- define "shopfront.labels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Values.image.tag | default .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
environment: {{ .Values.environment | quote }}
{{- end }}
EOF
for f in deployment service configmap ingress; do
  sed -i '0,/^  name: .*/s//&\n  labels:\n    {{- include "shopfront.labels" . | nindent 4 }}/' templates/$f.yaml
done
helm lint . -f values-dev.yaml --quiet
helm upgrade web . --namespace challenges -f values-dev.yaml --wait --timeout 3m | grep STATUS
cd - > /dev/null
```

<!-- test: contains=ingress.networking.k8s.io/web; output -->
```bash
kubectl get deploy,svc,configmap,ingress --namespace challenges -l app.kubernetes.io/instance=web
```

```text
NAME                  READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/web   1/1     1            1           5s

NAME          TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)    AGE
service/web   ClusterIP   10.96.2.145   <none>        8080/TCP   5s

NAME                   DATA   AGE
configmap/web-config   1      5s

NAME                            CLASS     HOSTS                 ADDRESS   PORTS   AGE
ingress.networking.k8s.io/web   traefik   challenge.localhost             80      5s
```

</details>

**Explanation.** One helper, consistent metadata everywhere: selectors, dashboards and audits can rely on it.

---

## Challenge 8 · Perform an upgrade

**Task.** Run 2 replicas in dev, reviewing the change first, and show the history.

**Requirements.** The change goes into `values-dev.yaml` (not `--set`); a server-side diff before the upgrade;
`helm history` shows a new revision.

**Hints.** [Lab 08](../labs/08-upgrade.md).

**Expected result.** 2 Pods; revision 3 (after challenge 7's revision 2) `deployed`.

<details>
<summary>Solution</summary>

<!-- test: contains=+  replicas: 2; output -->
```bash
cd labs/work/challenges/shopfront
sed -i 's/^replicaCount: 1/replicaCount: 2/' values-dev.yaml
helm template web . --namespace challenges -f values-dev.yaml \
  | kubectl diff --server-side --field-manager=helm --namespace challenges -f - \
  | grep -E '^[-+] ' | grep -vE 'generation:|meta\.helm\.sh/|^-\s+annotations:$' || true
cd - > /dev/null
```

```text
-  replicas: 1
+  replicas: 2
```

<!-- test: timeout=300; contains=Upgrade complete; output -->
```bash
helm upgrade web labs/work/challenges/shopfront --namespace challenges \
  -f labs/work/challenges/shopfront/values-dev.yaml --wait --timeout 3m > /dev/null
helm history web --namespace challenges
```

```text
REVISION	UPDATED                 	STATUS    	CHART          	APP VERSION	DESCRIPTION     
1       	Mon Oct  5 00:43:35 2026	superseded	shopfront-0.1.0	1.0.0      	Install complete
2       	Mon Oct  5 00:43:39 2026	superseded	shopfront-0.1.0	1.0.0      	Upgrade complete
3       	Mon Oct  5 00:43:41 2026	deployed  	shopfront-0.1.0	1.0.0      	Upgrade complete
```

</details>

**Explanation.** Review, apply with `--wait`, read the history: the routine of every change.

---

## Challenge 9 · Break the upgrade and roll back

**Task.** Deploy a non-existent image tag with a 60-second limit, then return to the last good revision.

**Requirements.** The failed upgrade is visible in the history; the rollback is a new revision; the app answers again.

**Hints.** `--set image.tag=9.9.9 --wait --timeout 60s`, then `helm rollback web <N>`, where N is the last good revision in `helm history`.

**Expected result.** Revisions: 4 `failed`, 5 `Rollback to 3`.

<details>
<summary>Solution</summary>

<!-- test: fail; timeout=300; contains=UPGRADE FAILED -->
```bash
helm upgrade web labs/work/challenges/shopfront --namespace challenges \
  -f labs/work/challenges/shopfront/values-dev.yaml --set image.tag=9.9.9 --wait --timeout 60s
```

<!-- test: timeout=300; contains=Rollback to 3; output -->
```bash
helm rollback web 3 --namespace challenges --wait --timeout 3m > /dev/null
helm history web --namespace challenges | cut -c1-110
```

```text
REVISION	UPDATED                 	STATUS    	CHART          	APP VERSION	DESCRIPTION                          
1       	Mon Oct  5 00:43:35 2026	superseded	shopfront-0.1.0	1.0.0      	Install complete                     
2       	Mon Oct  5 00:43:39 2026	superseded	shopfront-0.1.0	1.0.0      	Upgrade complete                     
3       	Mon Oct  5 00:43:41 2026	superseded	shopfront-0.1.0	1.0.0      	Upgrade complete                     
4       	Mon Oct  5 00:43:42 2026	failed    	shopfront-0.1.0	1.0.0      	Upgrade "web" failed: resource Deploy
5       	Mon Oct  5 00:44:43 2026	deployed  	shopfront-0.1.0	1.0.0      	Rollback to 3                        
```

</details>

**Explanation.** The old Pods served throughout; the history records the incident; the rollback restored revision
3's objects and values (2 replicas).

---

## Challenge 10 · Create a chart dependency

**Task.** Ship a small status page with the shop: add podinfo (6.15.0, from its public repository) as an optional
dependency under the alias `status`.

**Requirements.** `dependencies:` in `Chart.yaml` with `alias` and `condition: status.enabled` (default false);
`Chart.lock` created; enabling it in dev adds a `web-status` Deployment.

**Hints.** [Lab 12](../labs/12-dependencies.md). `helm dependency update`.

**Expected result.** `helm dependency list` shows `ok`; with `status.enabled=true` the release has two Deployments.

<details>
<summary>Solution</summary>

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
cd labs/work/challenges/shopfront
cat >> Chart.yaml <<'EOF'
dependencies:
  - name: podinfo
    version: 6.15.0
    repository: https://stefanprodan.github.io/podinfo
    alias: status
    condition: status.enabled
EOF
printf 'status:\n  enabled: false\n' >> values.yaml
helm dependency update . > /dev/null
helm dependency list .
helm upgrade web . --namespace challenges -f values-dev.yaml --set status.enabled=true --wait --timeout 3m | grep STATUS
cd - > /dev/null
```

<!-- test: contains=web-status; output -->
```bash
kubectl get deployments --namespace challenges
```

```text
NAME         READY   UP-TO-DATE   AVAILABLE   AGE
web          2/2     2            2           81s
web-status   1/1     1            1           12s
```

</details>

**Explanation.** The condition keeps the dependency optional: environments that don't need it don't get it.

---

## Challenge 11 · Create a Helm test

**Task.** A test that proves the release answers `/health` and runs with the configured environment.

**Requirements.** `templates/tests/test-health.yaml`, annotation `helm.sh/hook: test`, a non-root busybox container,
non-zero exit on failure; `helm test web` passes.

**Hints.** Compare with [demo-app's test](../charts/demo-app/templates/tests/test-connection.yaml).

**Expected result.** `Phase: Succeeded` for `web-test-health`.

<details>
<summary>Solution</summary>

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
cd labs/work/challenges/shopfront
mkdir -p templates/tests
cat > templates/tests/test-health.yaml <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: {{ .Release.Name }}-test-health
  labels:
    {{- include "shopfront.labels" . | nindent 4 }}
  annotations:
    "helm.sh/hook": test
    "helm.sh/hook-delete-policy": before-hook-creation
spec:
  restartPolicy: Never
  securityContext:
    runAsNonRoot: true
    runAsUser: 65534
  containers:
    - name: check
      image: busybox:1.37
      command: ["sh", "-c"]
      args:
        - |
          set -e
          wget -qO- http://{{ .Release.Name }}:8080/health
          wget -qO- http://{{ .Release.Name }}:8080/config.js | grep -q 'APP_ENV: "{{ .Values.environment }}"'
          echo " - environment {{ .Values.environment }} confirmed"
EOF
helm upgrade web . --namespace challenges -f values-dev.yaml --set status.enabled=true --wait --timeout 3m | grep STATUS
cd - > /dev/null
```

<!-- test: timeout=300; contains=environment dev confirmed; output=tail:6 -->
```bash
helm test web --namespace challenges --filter name=web-test-health --logs
```

```text
...
Last Started:   Mon Oct  5 00:44:57 2026
Last Completed: Mon Oct  5 00:44:59 2026
Phase:          Succeeded

POD LOGS: web-test-health (check)
{"status":"ok","service":"frontend","version":"1.0.0"} - environment dev confirmed
```

</details>

**Explanation.** `--filter name=...` runs one test: podinfo, the dependency, brings tests of its own, which
`helm test web` would run too.

---

## Challenge 12 · Troubleshoot a broken release

**Task.** Someone "simplified" the Service: after their upgrade, the site is down while every Pod is healthy. Find
and fix it with the method from [lab 15](../labs/15-troubleshooting.md), changing the chart, not the cluster.

**Requirements.** Explain the root cause from command output; fix in the chart; the test passes again.

**Hints.** Healthy Pods + no traffic: where does a Service send traffic?

<!-- test: timeout=300; contains=STATUS: deployed -->
```bash
sed -i 's/      targetPort: http/      targetPort: 80/' labs/work/challenges/shopfront/templates/service.yaml
helm upgrade web labs/work/challenges/shopfront --namespace challenges \
  -f labs/work/challenges/shopfront/values-dev.yaml --set status.enabled=true --wait --timeout 3m | grep STATUS
```

**Expected result.** The test fails before your fix and passes after it.

<details>
<summary>Solution</summary>

The test fails, the Pods are Ready, the Service has endpoints. So the endpoints are right but the port is not:

<!-- test: fail; timeout=300; contains=Phase:          Failed -->
```bash
helm test web --namespace challenges --filter name=web-test-health
```

<!-- test: contains="targetPort":80; output -->
```bash
kubectl get service web --namespace challenges -o jsonpath='{.spec.ports[0]}'; echo
kubectl get pods --namespace challenges -l app=web -o jsonpath='{.items[0].spec.containers[0].ports}'; echo
```

```text
{"port":8080,"protocol":"TCP","targetPort":80}
[{"containerPort":8080,"name":"http","protocol":"TCP"}]
```

`targetPort: 80`, but the container listens on 8080 (named `http`). The Service forwards to a port nothing serves.
Fix the chart and upgrade:

<!-- test: timeout=300; contains=Phase:          Succeeded -->
```bash
sed -i 's/      targetPort: 80/      targetPort: http/' labs/work/challenges/shopfront/templates/service.yaml
helm upgrade web labs/work/challenges/shopfront --namespace challenges \
  -f labs/work/challenges/shopfront/values-dev.yaml --set status.enabled=true --wait --timeout 3m > /dev/null
helm test web --namespace challenges --filter name=web-test-health
```

</details>

**Explanation.** Endpoints prove the selector works; the port mapping is a separate link in the chain (Service
`port` → `targetPort` → `containerPort`). Named ports (`http`) keep the three in sync when one changes.

---

## Cleanup

```text
⚠️ DESTRUCTIVE COMMAND · uninstalls the release web and deletes the namespace challenges and your chart.
```

<!-- test: timeout=300; contains=uninstalled -->
```bash
helm uninstall web --namespace challenges --wait
kubectl delete namespace challenges --wait=false > /dev/null
rm -rf labs/work/challenges
```
