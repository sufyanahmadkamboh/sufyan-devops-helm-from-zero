# Lab 02 · Your first chart

> Level 4. Time: 25 minutes.

## Objective

Generate a chart with `helm create`, look at what it generated, install it as a release, test it, and turn it
into the start of a chart for our own application.

## Prerequisites

- [Lab 01](01-install-helm.md): Helm 4.3 and the `helm-lab` cluster.

## Task

1. Create a chart called `hello`.
2. Lint it, render it, install it into the namespace `lab-02`.
3. Run its test.
4. Point it at the Bookshop frontend image instead of the default nginx.

## Commands

### 1 · Create

All lab work happens in `labs/work/` (ignored by Git):

<!-- test-run: rm -rf labs/work/hello -->

<!-- test: contains=Creating labs/work/hello; output -->
```bash
mkdir -p labs/work
helm create labs/work/hello
```

```text
Creating labs/work/hello
```

<!-- test: contains=_helpers.tpl; output -->
```bash
find labs/work/hello | sort
```

```text
labs/work/hello
labs/work/hello/.helmignore
labs/work/hello/Chart.yaml
labs/work/hello/charts
labs/work/hello/templates
labs/work/hello/templates/NOTES.txt
labs/work/hello/templates/_helpers.tpl
labs/work/hello/templates/deployment.yaml
labs/work/hello/templates/hpa.yaml
labs/work/hello/templates/httproute.yaml
labs/work/hello/templates/ingress.yaml
labs/work/hello/templates/service.yaml
labs/work/hello/templates/serviceaccount.yaml
labs/work/hello/templates/tests
labs/work/hello/templates/tests/test-connection.yaml
labs/work/hello/values.yaml
```

```text
hello/
├── Chart.yaml              the chart's identity: name, description, chart version, app version
├── values.yaml             every setting the templates read, with its default and a comment
├── .helmignore             files NOT to put into the package (like .gitignore)
├── charts/                 dependencies (other charts) go here; empty for now
└── templates/              Kubernetes manifests with placeholders
    ├── deployment.yaml     the Pods: image, ports, probes, resources
    ├── service.yaml        a stable address for the Pods
    ├── serviceaccount.yaml the identity the Pods run as
    ├── ingress.yaml        HTTP routing from outside (off by default: ingress.enabled=false)
    ├── httproute.yaml      the same with the newer Gateway API (off by default)
    ├── hpa.yaml            a HorizontalPodAutoscaler (off by default: autoscaling.enabled=false)
    ├── _helpers.tpl        named templates (name, labels) shared by all the files above; renders nothing itself
    ├── NOTES.txt           the text Helm prints after install/upgrade
    └── tests/
        └── test-connection.yaml   a Pod that "helm test" runs: does the Service answer?
```

Don't delete what you don't understand yet: every file is explained in [lab 03](03-chart-structure.md). The
generated chart is a working, conventional chart; it deploys nginx.

<!-- test: contains=appVersion; output -->
```bash
grep -v '^#' labs/work/hello/Chart.yaml | grep -v '^$'
```

```text
apiVersion: v2
name: hello
description: A Helm chart for Kubernetes
type: application
version: 0.1.0
appVersion: "1.16.0"
```

`version: 0.1.0` is the chart's version, `appVersion: "1.16.0"` the version of the application, here nginx's image
tag. Two different versions: [lab 03](03-chart-structure.md) is about the difference.

### 2 · Lint, render, install

<!-- test: contains=0 chart(s) failed; output -->
```bash
helm lint labs/work/hello
```

```text
==> Linting labs/work/hello
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

`helm template` shows the YAML the chart produces, without touching the cluster:

<!-- test: contains=image: "nginx:1.16.0"; output=head:30 -->
```bash
helm template hello labs/work/hello --show-only templates/deployment.yaml
```

```text
---
# Source: hello/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hello
  labels:
    helm.sh/chart: hello-0.1.0
    app.kubernetes.io/name: hello
    app.kubernetes.io/instance: hello
    app.kubernetes.io/version: "1.16.0"
    app.kubernetes.io/managed-by: Helm
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: hello
      app.kubernetes.io/instance: hello
  template:
    metadata:
      labels:
        helm.sh/chart: hello-0.1.0
        app.kubernetes.io/name: hello
        app.kubernetes.io/instance: hello
        app.kubernetes.io/version: "1.16.0"
        app.kubernetes.io/managed-by: Helm
    spec:
      serviceAccountName: hello
      containers:
        - name: hello
...
```

The image is `nginx:1.16.0`: `values.yaml` has `tag: ""`, and the template falls back to the chart's `appVersion`.
Now install it. A Helm installation creates a **release**:

<!-- test: timeout=300; contains=STATUS: deployed; output=head:12 -->
```bash
helm install hello labs/work/hello --namespace lab-02 --create-namespace --wait --timeout 3m
```

```text
NAME: hello
LAST DEPLOYED: Sun Oct  4 23:18:57 2026
NAMESPACE: lab-02
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
NOTES:
1. Get the application URL by running these commands:
  export POD_NAME=$(kubectl get pods --namespace lab-02 -l "app.kubernetes.io/name=hello,app.kubernetes.io/instance=hello" -o jsonpath="{.items[0].metadata.name}")
  export CONTAINER_PORT=$(kubectl get pod --namespace lab-02 $POD_NAME -o jsonpath="{.spec.containers[0].ports[0].containerPort}")
  echo "Visit http://127.0.0.1:8080 to use your application"
  kubectl --namespace lab-02 port-forward $POD_NAME 8080:$CONTAINER_PORT
```

`hello` is the release name, `labs/work/hello` the chart, `--wait` waits until the Pods are ready. The text after
`NOTES:` comes from `templates/NOTES.txt`.

<!-- test: contains=deployed; contains=hello-; output -->
```bash
helm list --namespace lab-02
kubectl get pods,svc --namespace lab-02
```

```text
NAME 	NAMESPACE	REVISION	UPDATED                               	STATUS  	CHART      	APP VERSION
hello	lab-02   	1       	2026-10-04 23:18:57.8006954 +0200 CEST	deployed	hello-0.1.0	1.16.0     
NAME                         READY   STATUS    RESTARTS   AGE
pod/hello-5d65b49b89-gr6n4   1/1     Running   0          6s

NAME            TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
service/hello   ClusterIP   10.96.159.180   <none>        80/TCP    6s
```

### 3 · Test

<!-- test: timeout=180; contains=Succeeded; output -->
```bash
helm test hello --namespace lab-02
```

```text
NAME: hello
LAST DEPLOYED: Sun Oct  4 23:18:57 2026
NAMESPACE: lab-02
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE:     hello-test-connection
Last Started:   Sun Oct  4 23:19:04 2026
Last Completed: Sun Oct  4 23:19:08 2026
Phase:          Succeeded
```

The chart's test Pod ran `wget hello:80` from inside the cluster and exited with 0: the Service answers.

## Expected Output

- `helm lint`: `1 chart(s) linted, 0 chart(s) failed`.
- `helm list -n lab-02`: release `hello`, revision 1, `deployed`, chart `hello-0.1.0`, app version `1.16.0`.
- `helm test`: `Phase: Succeeded`.

## Explanation

`helm create` gave you the conventions most charts in the world follow: the same helper names, the same label set
(`app.kubernetes.io/name`, `.../instance`, ...), the same switches (`ingress.enabled`, `autoscaling.enabled`). When you
open a third-party chart later, you will recognise this skeleton.

The release name matters: it is in every object's name (`hello`, `hello-...` Pods) and in the label
`app.kubernetes.io/instance=hello`, so two releases of the same chart never collide.

## Break It

A chart without a name is not a chart. Break `Chart.yaml`:

<!-- test: fail; contains=name is required; output -->
```bash
sed -i.bak 's/^name: hello/name:/' labs/work/hello/Chart.yaml
helm lint labs/work/hello
```

```text
==> Linting labs/work/hello
[ERROR] Chart.yaml: name is required
[INFO] Chart.yaml: icon is recommended
[ERROR] templates/: validation: chart.metadata.name is required
[ERROR] : unable to load chart
	validation: chart.metadata.name is required

Error: 1 chart(s) linted, 1 chart(s) failed
```

## Troubleshoot It

`helm lint` reports `[ERROR] Chart.yaml: name is required` and the exit code is non-zero (a CI pipeline would stop
here). Read the error from top to bottom: the file (`Chart.yaml`), then the field. Restore it:

<!-- test: contains=0 chart(s) failed -->
```bash
mv labs/work/hello/Chart.yaml.bak labs/work/hello/Chart.yaml
helm lint labs/work/hello
```

Lint before every install: it is fast and catches broken charts before they reach a cluster.

## Challenge

Make the chart deploy our application instead of nginx: the Bookshop frontend,
`ghcr.io/sufyanahmadkamboh/bookshop-frontend:1.0.0`, which listens on port **8080** (not 80) and runs as a non-root
user. Upgrade the release `hello` with the new values, without editing any template. Prove it with `helm test`.

Hint: `helm show values labs/work/hello | grep -A3 '^image:'` and `... | grep -A3 '^service:'`. Which value does
the Deployment use for `containerPort`?

## Solution

<details>
<summary>Open the solution</summary>

In the generated deployment, `containerPort: {{ .Values.service.port }}`: one value sets both the Service port and
the container port. The probes use the port's name (`http`), so they follow.

<!-- test: timeout=300; contains=REVISION: 2 -->
```bash
helm upgrade hello labs/work/hello --namespace lab-02 \
  --set image.repository=ghcr.io/sufyanahmadkamboh/bookshop-frontend \
  --set image.tag=1.0.0 \
  --set service.port=8080 \
  --wait --timeout 3m | head -6
```

</details>

## Verification

<!-- test: timeout=180; contains=Succeeded; contains=bookshop-frontend:1.0.0; output -->
```bash
helm test hello --namespace lab-02 | grep Phase
kubectl get deployment hello --namespace lab-02 -o jsonpath='{.spec.template.spec.containers[0].image}'; echo
```

```text
Phase:          Succeeded
ghcr.io/sufyanahmadkamboh/bookshop-frontend:1.0.0
```

The test now calls `hello:8080`, and the frontend answers. This is exactly how `charts/demo-app` started: `helm
create`, then values and templates adapted to the application, step by step ([lab 03](03-chart-structure.md)).

## Cleanup

```text
⚠️ DESTRUCTIVE COMMAND · uninstalls the release hello and deletes the namespace lab-02 and the generated chart.
```

<!-- test: timeout=300; contains=uninstalled -->
```bash
helm uninstall hello --namespace lab-02 --wait
kubectl delete namespace lab-02 --wait=false
rm -rf labs/work/hello
```

Next: [lab 03 · Chart structure](03-chart-structure.md).
