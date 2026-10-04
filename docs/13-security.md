# Level 17 · Helm security

> Time: 30 minutes. Needs the `shop` release in `bookshop-dev` ([lab 12](../labs/12-dependencies.md)) and Traefik.
> The commands below are tested like the labs.

**Installing a Helm chart creates Kubernetes resources. Chart security is Kubernetes security.** A chart can create
anything your credentials allow: cluster-wide permissions, privileged Pods, webhooks that see every request. Helm adds
no sandbox. This lesson is a review routine you can apply to any chart, and the secret-handling rules that matter
most.

## 1 · Don't trust a chart you have not read

Before installing a third-party chart, render it and look for the objects with the widest reach:

<!-- test: contains=ClusterRole; output -->
```bash
helm get manifest traefik --namespace traefik | grep -E '^kind:' | sort | uniq -c
```

```text
      1 kind: ClusterRole
      1 kind: ClusterRoleBinding
      1 kind: Deployment
      1 kind: IngressClass
      1 kind: Service
      1 kind: ServiceAccount
```

Traefik, installed in lab 00, created a **ClusterRole** and a **ClusterRoleBinding**: permissions across the whole
cluster. For an ingress controller that is expected (it watches Ingresses and Services in every namespace), but read
what exactly it may do:

<!-- test: contains=secrets; output -->
```bash
kubectl get clusterrole traefik-traefik -o jsonpath='{range .rules[*]}{.resources}{"  "}{.verbs}{"\n"}{end}'
```

```text
["configmaps","nodes","services"]  ["get","list","watch"]
["endpointslices"]  ["list","watch"]
["pods"]  ["get"]
["secrets"]  ["get","list","watch"]
["ingressclasses","ingresses"]  ["get","list","watch"]
["ingresses/status"]  ["update"]
["namespaces"]  ["list","watch"]
["ingressroutes","ingressroutetcps","ingressrouteudps","middlewares","middlewaretcps","serverstransports","serverstransporttcps","tlsoptions","tlsstores","traefikservices"]  ["get","list","watch"]
```

It can read Secrets in every namespace (to load TLS certificates for Ingresses). Whoever controls that Pod can read
your Secrets. That is the kind of fact to know, and accept deliberately, before installing.

The review checklist for any chart:

| Look for | Why | How |
|---|---|---|
| `ClusterRole`, `ClusterRoleBinding`, `*Webhook*Configuration`, `CustomResourceDefinition` | cluster-wide power | `helm template ... \| grep -E '^kind:' \| sort \| uniq -c` |
| `privileged: true`, `hostNetwork`, `hostPath`, `runAsUser: 0`, added capabilities | node-level access | `helm template ... \| grep -nE 'privileged\|hostPath\|hostNetwork\|runAsUser'` |
| Every `image:` | what you will run, from where, which tag | `helm template ... \| grep 'image:' \| sort -u` |
| Hooks and tests | extra Jobs/Pods with their own images ([lab 11](../labs/11-repositories.md)) | `helm template ... \| grep -B3 'helm.sh/hook'` |
| Dependencies | charts inside the chart, with their own maintainers | `helm show chart`, `helm dependency list` |

## 2 · Images: pinned and known

<!-- test: contains=bookshop-node-api:1.0.0; absent=:latest; output -->
```bash
helm get manifest shop --namespace bookshop-dev | grep 'image:' | sort -u
```

```text
          image: "ghcr.io/sufyanahmadkamboh/bookshop-frontend:1.0.0"
          image: "ghcr.io/sufyanahmadkamboh/bookshop-go-status:1.0.0"
          image: "ghcr.io/sufyanahmadkamboh/bookshop-java-api:1.0.0"
          image: "ghcr.io/sufyanahmadkamboh/bookshop-node-api:1.0.0"
          image: "ghcr.io/sufyanahmadkamboh/bookshop-python-api:1.0.0"
          image: "postgres:18.6-alpine"
        # 70 = the "postgres" user of the alpine image: the server runs as it from the start, never as root
```

Every image has an explicit version; none is `latest`. Production goes further: pin by digest
(`image@sha256:...`), scan images in CI (Trivy, Grype), and only allow trusted registries (an admission policy
such as Kyverno or Gatekeeper).

## 3 · Least privilege for what the chart runs

The Bookshop chart runs every container as a non-root user, without privilege escalation, with all Linux
capabilities dropped and the default seccomp profile, and does not mount a Kubernetes API token into Pods that never
call the API:

<!-- test: contains=true; output -->
```bash
kubectl get pods --namespace bookshop-dev -l app.kubernetes.io/instance=shop \
  -o custom-columns='POD:.metadata.name,NON_ROOT:.spec.securityContext.runAsNonRoot,USER:.spec.securityContext.runAsUser,TOKEN:.spec.automountServiceAccountToken'
```

```text
POD                               NON_ROOT   USER    TOKEN
shop-frontend-5d865884c8-bxc5k    true       101     false
shop-go-status-6dc7845b99-tpns7   true       65532   false
shop-java-api-7ff96666d4-7znv8    true       10001   false
shop-node-api-fbb58c4c4-7hgsh     true       1000    false
shop-postgres-0                   true       70      false
shop-python-api-9f4bcbc58-wr65p   true       10001   false
shop-report-g8nqj                 true       1000    false
shop-test-services                true       65534   false
```

## 4 · Least privilege for who runs Helm

Helm has no permissions of its own: it uses the kubeconfig's identity. A CI pipeline that deploys one application
should use a ServiceAccount limited to that application's namespace (a Role, not a ClusterRole), not a cluster-admin
kubeconfig. Remember that Helm stores releases as Secrets: the deploying identity needs to read and write Secrets in
the target namespace, and **anyone who can read Secrets there can read every release's values** (section 5).

## 5 · Secrets: why values files are the wrong place

Three facts, demonstrated:

**Fact 1: values end up in Git.** A values file is meant to be committed and reviewed. A password in it is a password
in the repository history forever. This repository's values contain key names only:

<!-- test: absent=example-only; output -->
```bash
grep -rniE 'password|token|secret' charts/*/values*.yaml
```

```text
charts/bookshop/values-prod.yaml:2:# In a real production cluster also set database.existingSecret (and postgres.auth.existingSecret) to a Secret
charts/bookshop/values.yaml:2:# Never put real secrets here: see database.existingSecret.
charts/bookshop/values.yaml:87:  # Production: create the Secret yourself (or with an external secret manager) and name it here.
charts/bookshop/values.yaml:88:  # Empty: the chart creates "<release>-db" with a random password on first install and KEEPS it on upgrades.
charts/bookshop/values.yaml:89:  existingSecret: ""
charts/bookshop/values.yaml:94:  enabled: true                    # false = use an external database (set database.host and database.existingSecret)
charts/bookshop/values.yaml:98:    existingSecret: ""             # same as database.existingSecret
charts/demo-app/values.yaml:2:# (-f my-values.yaml, --set key=value). Values files hold configuration, NEVER real secrets.
charts/demo-app/values.yaml:80:  automount: false             # the app never calls the Kubernetes API: don't give it a token
charts/demo-app/values.yaml:94:imagePullSecrets: []
charts/postgres/values.yaml:10:  # Name of an existing Secret with the key below. Empty = "<release name>-db" (the parent chart creates it).
charts/postgres/values.yaml:11:  existingSecret: ""
charts/postgres/values.yaml:12:  passwordKey: DB_PASSWORD
```

**Fact 2: `--set` is not a safe alternative.** A value passed on the command line is stored in the release record,
inside the cluster, readable by anyone who can read Secrets in that namespace:

<!-- test: timeout=300; contains=example-not-a-real-token; output -->
```bash
helm install leaky examples/values-example --namespace sec-demo --create-namespace \
  --set apiToken=example-not-a-real-token > /dev/null
helm get values leaky --namespace sec-demo
```

```text
USER-SUPPLIED VALUES:
apiToken: example-not-a-real-token
```

And without Helm, with plain kubectl, from the release Secret (base64, base64 again, gzip: encoding, not encryption):

<!-- test: contains="apiToken":"example-not-a-real-token"; output -->
```bash
kubectl get secret sh.helm.release.v1.leaky.v1 --namespace sec-demo -o jsonpath='{.data.release}' \
  | base64 -d | base64 -d | gunzip | grep -o '"apiToken":"[^"]*"' | head -1
```

```text
"apiToken":"example-not-a-real-token"
```

It is also in your shell history and in CI logs if the command is printed.

**Fact 3: templating a Secret does not make it secret.** A chart's `secret.yaml` turns values into a Kubernetes
Secret: base64-encoded, readable by anyone with `get secrets` permission. Helm adds no encryption anywhere.

<!-- test: timeout=300; contains=uninstalled -->
```bash
helm uninstall leaky --namespace sec-demo --wait
kubectl delete namespace sec-demo --wait=false > /dev/null
```

### Safe patterns

| Pattern | How it works | In this repository |
|---|---|---|
| **Generated in the cluster** | the chart creates a random value on first install, `lookup` keeps it on upgrades; it never exists outside the cluster | `charts/bookshop` without `database.existingSecret` (dev, CI) |
| **Existing Secret by name** | the Secret is created outside the chart (by an admin, a pipeline, an operator); the values file only holds its **name** | `database.existingSecret: shop-db-prod` |
| **External secret manager** | an operator syncs from AWS Secrets Manager, Vault, Azure Key Vault... into a Secret: External Secrets Operator, Secrets Store CSI Driver | (the existing-Secret pattern is what the chart needs to support it) |
| **Encrypted in Git** | the file is committed encrypted; decrypted at deploy time: SOPS (often with the helm-secrets plugin), Sealed Secrets | – |

The existing-Secret pattern in practice, with an example password typed by an operator (never committed):

<!-- test: timeout=300; contains=shop-db-external; output -->
```bash
kubectl create namespace sec-demo2 > /dev/null
kubectl create secret generic shop-db-external --namespace sec-demo2 --from-literal=DB_PASSWORD="$(head -c 18 /dev/urandom | base64)"
helm template shop charts/bookshop --namespace sec-demo2 \
  --set database.existingSecret=shop-db-external --set postgres.auth.existingSecret=shop-db-external \
  | grep -E 'kind: Secret|name: shop-db' | sort | uniq -c
kubectl delete namespace sec-demo2 --wait=false > /dev/null
```

```text
secret/shop-db-external created
      5                   name: shop-db-external
```

With `existingSecret` set, the chart renders **no** Secret at all; every Deployment and the database reference
`shop-db-external` by name. The password never passes through Helm.

## 6 · Supply chain: trusted sources, pinned versions

- Add repositories from the project's official documentation, over HTTPS; prefer the maintainer's own registry.
- Pin chart versions (`--version`, `Chart.lock`); upgrade deliberately and read the chart's changelog.
- Verify what you can: signed charts (`helm install --verify` with provenance files), signed OCI artifacts
  (cosign), digests (`oci://...@sha256:...`).
- Review dependencies like the chart itself: `helm dependency list`, then the dependency's templates.
- Scan rendered manifests for misconfigurations in CI (Trivy config, Checkov, kube-score) alongside `helm lint`.

## The 10 questions

**1. What is it?** The practices that keep installing and running charts from becoming an attack path or a leak.

**2. Why do we need it?** A chart is code that runs with your cluster credentials, written by someone else, and Helm
stores every value you give it.

**3. How does it work?** Review before install, restrict what runs (security contexts, RBAC) and who deploys
(least-privilege identities), keep secrets out of values and out of Helm's records.

**4. What problem does it solve?** Over-privileged third-party software, leaked credentials in Git or release
history, unpinned images changing under you.

**5. How do I use it?** Make the review checklist and the secret patterns a habit, and automate the checks in CI.

**6. What command should I run?** `helm template ... | grep -E '^kind:'`, `... | grep image:`, `helm get manifest`,
`helm get values`, `kubectl auth can-i`.

**7. What output should I expect?** No surprises: cluster-wide objects you can justify, pinned images, no secret
values in any values file or `helm get values` output.

**8. What can go wrong?** Charts granting cluster-admin, images from unknown registries, passwords in `--set` lines
and CI logs, `latest` tags, unreviewed upgrades of third-party charts.

**9. How do I troubleshoot it?** Render and grep (above); `kubectl auth can-i --list --as=system:serviceaccount:NS:SA`
to see what a chart's ServiceAccount may do; decode the release Secret to see what Helm stored.

**10. Where is it used in real DevOps work?** Platform teams reviewing every chart before it reaches a cluster,
security reviews of release pipelines, secret-management migrations (values files → external secret managers).

See also: [ConfigMaps and Secrets](12-configmaps-and-secrets.md), [best practices](15-best-practices.md).

Next, Level 18: [lab 15 · Troubleshooting](../labs/15-troubleshooting.md).
