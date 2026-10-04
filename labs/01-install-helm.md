# Lab 01 · Install Helm

> Level 3 of the [roadmap](../README.md#learning-roadmap). Time: 15 minutes.

## Objective

Install the Helm CLI (the version this course is tested with: **v4.3.0**), check that it talks to your cluster, and
know where it keeps its configuration.

## Prerequisites

- The cluster from [lab 00](00-setup.md) (kubectl works: `kubectl get nodes`).
- [What is Helm?](../docs/01-what-is-helm.md) read.

## Task

1. Install Helm 4 with an official method for your system.
2. Check the version.
3. Check that Helm uses the same cluster as kubectl.
4. Find Helm's own files (repository list, cache).

## Commands

### Install

Helm is a single binary with no server component: Helm 2's in-cluster "Tiller" is long gone. Helm 4 talks directly to
the Kubernetes API with the credentials from your kubeconfig, exactly like kubectl. Pick **one** official method
([helm.sh/docs/intro/install](https://helm.sh/docs/intro/install/)):

<!-- test: skip -->
```bash
# Linux / macOS: the official install script for Helm 4 (downloads, verifies the checksum, installs to /usr/local/bin)
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-4
chmod 700 get_helm.sh
./get_helm.sh --version v4.3.0

# macOS
brew install helm

# Windows (one of)
winget install Helm.Helm
choco install kubernetes-helm
scoop install helm
```

Or download the archive for your platform from the [releases page](https://github.com/helm/helm/releases), check its
SHA-256 against the published one, and put the `helm` binary on your `PATH`. Read a script before you pipe it into
a shell: `get-helm-4` is short, and it is good practice.

### Verify

<!-- test: contains=v4.3; output -->
```bash
helm version
```

```text
version.BuildInfo{Version:"v4.3.0", GitCommit:"bec5b06ed841fe5269972d864d5177944fd5970f", GitTreeState:"clean", GoVersion:"go1.27.1", KubeClientVersion:"v1.37"}
```

`v4.3.0` is the Helm version; `GoVersion` is the Go compiler it was built with; `KubeClientVersion` is the Kubernetes
client library inside it. Which cluster versions a Helm release supports is listed in Helm's
[version skew policy](https://helm.sh/docs/topics/version_skew/).

Helm uses your kubeconfig and its **current context**, like kubectl. Same cluster?

<!-- test: contains=kind-helm-lab; contains=traefik; output -->
```bash
kubectl config current-context
helm list --all-namespaces
```

```text
kind-helm-lab
NAME   	NAMESPACE	REVISION	UPDATED                               	STATUS  	CHART         	APP VERSION
traefik	traefik  	1       	2026-10-04 22:21:36.5148655 +0200 CEST	deployed	traefik-41.6.1	v3.7.13    
```

`helm list` shows **releases**: installed charts. The one in the list is Traefik, installed in lab 00.

### Where Helm keeps its files

<!-- test: contains=HELM_REPOSITORY_CONFIG; output -->
```bash
helm env | grep -E '^HELM_(CACHE_HOME|CONFIG_HOME|DATA_HOME|REPOSITORY_CONFIG|NAMESPACE|KUBECONTEXT)='
```

```text
HELM_CACHE_HOME="~\AppData\Local\Temp\helm"
HELM_CONFIG_HOME="~\AppData\Roaming\helm"
HELM_DATA_HOME="~\AppData\Roaming\helm"
HELM_KUBECONTEXT=""
HELM_NAMESPACE="default"
HELM_REPOSITORY_CONFIG="~\AppData\Roaming\helm\repositories.yaml"
```

| Variable | What is there |
|---|---|
| `HELM_REPOSITORY_CONFIG` | `repositories.yaml`: the chart repositories you added (`helm repo add`) |
| `HELM_CACHE_HOME` | Downloaded repository indexes and charts |
| `HELM_DATA_HOME` | Plugins |
| `HELM_NAMESPACE` | The default namespace for Helm commands (empty = the kubeconfig's namespace, usually `default`) |
| `HELM_KUBECONTEXT` | A context to use instead of the current one |

Notice what is **not** there: the releases. Helm stores each release in the cluster, as a Secret in the release's
namespace (lab 07 shows it). That is why a teammate with access to the same cluster sees the same `helm list`.

## Expected Output

- `helm version` prints `v4.3.0` (or a newer 4.x).
- `helm list -A` shows the `traefik` release, status `deployed`.

## Explanation

```text
 helm (CLI on your computer)
   │  reads: ~/.kube/config (cluster address + credentials), the chart, the values
   │  renders the chart into YAML on your computer
   ▼
 Kubernetes API server  ──►  creates the objects, stores the release record (a Secret)
```

Helm has no permissions of its own: it can do exactly what your kubeconfig user can do. If `kubectl get pods -n x`
is forbidden for you, a Helm install into `x` is too.

## Break It

Point Helm at a context that does not exist, as happens after a typo or with an old kubeconfig:

<!-- test: fail; contains=does-not-exist; output -->
```bash
helm list --kube-context does-not-exist
```

```text
Error: kubernetes cluster unreachable: context "does-not-exist" does not exist
```

## Troubleshoot It

The error names the context it looked for. Is there a context with a similar name? (`kubectl config get-contexts`
lists them all; here we filter for the lab's.)

<!-- test: contains=kind-helm-lab; output -->
```bash
kubectl config get-contexts -o name | grep helm
```

```text
kind-helm-lab
```

Other first-day errors:

| Error | Cause | Check |
|---|---|---|
| `Kubernetes cluster unreachable` | Cluster stopped, or wrong kubeconfig | `kubectl get nodes`; `echo $KUBECONFIG` |
| `helm: command not found` | Binary not on `PATH` | `which helm` (Windows: `where helm`) |
| A different `helm version` than you installed | Two copies on `PATH`; the first one wins | `which -a helm` |
| `forbidden: User ... cannot list resource "secrets"` | Your user's RBAC; Helm reads release Secrets | `kubectl auth can-i list secrets -n <ns>` |

The third one is common on Windows, where package managers install into different folders. It is not just
cosmetic: while building this course, an older Helm 4.2.1 earlier on the `PATH` made every hook wait for its full
`--timeout` (a fixed upstream bug, [helm/helm#32214](https://github.com/helm/helm/issues/32214)). Always check which binary runs.

## Challenge

1. Print only the Helm version number, without the build details.
2. Run `helm list` against the `traefik` namespace without passing `--namespace`, using an environment variable.

## Solution

<details>
<summary>Open the solution</summary>

<!-- test: contains=v4.; output -->
```bash
helm version --short
helm version --template '{{ .Version }}'; echo
```

```text
v4.3.0+gbec5b06
v4.3.0
```

`--template` takes a Go template, the same language charts use (lab 05).

<!-- test: contains=traefik; output -->
```bash
HELM_NAMESPACE=traefik helm list
```

```text
NAME   	NAMESPACE	REVISION	UPDATED                               	STATUS  	CHART         	APP VERSION
traefik	traefik  	1       	2026-10-04 22:21:36.5148655 +0200 CEST	deployed	traefik-41.6.1	v3.7.13    
```

Every global flag has an environment variable (`--namespace` ↔ `HELM_NAMESPACE`, `--kube-context` ↔
`HELM_KUBECONTEXT`): useful in CI pipelines.

</details>

## Verification

<!-- test: contains=v4.3; contains=deployed -->
```bash
helm version --short
helm status traefik -n traefik | grep STATUS
```

## Cleanup

Nothing to clean up: the next labs use this Helm and this cluster.

Next: [lab 02 · Your first chart](02-first-chart.md).
