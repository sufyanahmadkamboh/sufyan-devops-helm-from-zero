# Level 1 · The Kubernetes YAML problem

> Time: 20 minutes. Needs the cluster from [lab 00](../labs/00-setup.md). No Helm in this lesson, on purpose.

Before Helm, let's see the problem. This folder is the Bookshop platform (from the
[multi-stack project](https://github.com/sufyanahmadkamboh/sufyan-devops-multi-stack-kubernetes)), deployed the way
you already know: plain Kubernetes YAML and `kubectl apply`. Three environments, three folders:

```text
environments/
├── dev/                      ├── staging/                  ├── prod/
│   ├── namespace.yaml        │   ├── namespace.yaml        │   ├── namespace.yaml
│   ├── configmap.yaml        │   ├── configmap.yaml        │   ├── configmap.yaml
│   ├── secret.yaml           │   ├── secret.yaml           │   ├── secret.yaml
│   ├── database.yaml         │   ├── database.yaml         │   ├── database.yaml       (StatefulSet + volume)
│   ├── deployments.yaml      │   ├── deployments.yaml      │   ├── deployments.yaml    (5 services)
│   ├── services.yaml         │   ├── services.yaml         │   ├── services.yaml
│   └── ingress.yaml          │   └── ingress.yaml          │   └── ingress.yaml
```

```text
                     Ingress  dev.bookshop.localhost
                        │
        ┌───────────────┼───────────────┬───────────────┬───────────────┐
        ▼               ▼               ▼               ▼               ▼
    frontend         node-api        java-api       python-api      go-status
    (React)          /api/users      /api/books     /api/stats      /api/status
                        │               │               │
                        └───────────────┼───────────────┘
                                        ▼
                                   PostgreSQL
```

## Step 1 · Deploy dev, the way you know

The namespace first (the other files create objects inside it), then the whole folder:

<!-- test: contains=deployment.apps/node-api created; output=tail:6 -->
```bash
kubectl apply -f environments/dev/namespace.yaml
kubectl apply -f environments/dev/
```

```text
```

<!-- test: timeout=400; contains=successfully rolled out -->
```bash
for d in frontend node-api java-api python-api go-status; do
  kubectl -n bookshop-dev rollout status deployment/$d --timeout=300s
done
```

Verify, as you would for any deployment:

<!-- test: absent=0/1; output -->
```bash
kubectl -n bookshop-dev get deployments
kubectl -n bookshop-dev get pods
```

```text
```

<!-- test: contains=dev.bookshop.localhost; output -->
```bash
kubectl -n bookshop-dev get services
kubectl -n bookshop-dev get ingress
```

```text
```

<!-- test: retry=20; contains=APP_ENV: "dev"; contains=Ada Lovelace; output -->
```bash
curl -s http://dev.bookshop.localhost:8080/config.js; echo
curl -s http://dev.bookshop.localhost:8080/api/users | head -c 120; echo
```

```text
```

Open <http://dev.bookshop.localhost:8080/> in a browser: the Bookshop, with `dev` in its footer.

**What works:** everything. Plain YAML is explicit, reviewable, and `kubectl apply` is all you need. For one
application in one environment this is a perfectly good way to work.

## Step 2 · Now imagine staging and production

Staging and production run the same application. Same Deployments, same Services, same probes, same security
settings. How much of each folder is actually different?

<!-- test: output -->
```bash
wc -l environments/dev/*.yaml | tail -1
wc -l environments/staging/*.yaml | tail -1
wc -l environments/prod/*.yaml | tail -1
diff -r environments/dev environments/staging | grep -c '^[<>]'
```

```text
```

About 460 lines per environment; the `diff` counts the lines that differ between dev and staging (each changed
line counts twice: once `<`, once `>`). Everything else is a copy. What differs?

<!-- test: contains=replicas; output=head:40 -->
```bash
diff environments/dev/deployments.yaml environments/staging/deployments.yaml
```

```text
```

The namespace, the replica counts, the `APP_ENV` value and the namespace inside every service URL. In
`ingress.yaml` the host name; in `database.yaml` the volume size; in `secret.yaml` the password.

## Step 3 · A routine change

The node-api team released version `1.1.0`. Where do you change the image tag?

<!-- test: contains=environments/prod/deployments.yaml; output -->
```bash
grep -rn "bookshop-node-api:" environments/
```

```text
```

Three files, one per environment, and you must not forget one. The same is true for every probe setting, every
resource limit, every new environment variable: **one change = N edits**, where N is the number of environments.
Add a fourth environment (a load-test environment, a per-customer copy) and you copy 460 more lines.

## Step 4 · And the secret

<!-- test: contains=example-only-dev-password; output -->
```bash
grep -n -A1 "stringData" environments/dev/secret.yaml
```

```text
```

To make the folder applicable as-is, the password is written in a file. In a Git repository, that file is readable by
everyone who can read the repository, forever (Git keeps history). Base64 in a Secret is encoding, not encryption.

## What becomes difficult

| | Without a tool |
|---|---|
| Repetition | Every environment is a full copy; 90 % of the lines are identical |
| Changes | One change means N edits; a forgotten copy means environments silently drift apart |
| Differences | Hidden inside 460 lines: you find them only with `diff` |
| Versions | Which version is running in staging? You read the YAML, or the cluster |
| History | `kubectl apply` keeps no history of what you applied, and there is no "undo the whole application" |
| Removal | You must remember every object you created |
| Secrets | Tempting to commit them next to the rest |
| Sharing | Another team wants your app? They copy your files and edit them too |

What we want instead: **one** description of the application, with the differences between environments as a small
list of values, a record of every deployment, and a one-command rollback. That is Helm:

```text
                     Helm chart (templates: written once)
                                  │
           ┌──────────────────────┼──────────────────────┐
           ▼                      ▼                      ▼
     values-dev.yaml       values-staging.yaml     values-prod.yaml      (only the differences)
           │                      │                      │
           └──────────────────────┼──────────────────────┘
                                  ▼
                         Kubernetes resources
```

The chart that replaces these 1,374 lines is [charts/bookshop](../charts/bookshop): about 600 lines of templates and
defaults (with many comments), written once, plus a values file per environment: 3 lines for dev, 9 for staging, 32
for production (which adds autoscaling and disruption budgets the raw YAML doesn't even have). You will build up to it, starting in [lab 01](../labs/01-install-helm.md).

## Cleanup

```text
⚠️ DESTRUCTIVE COMMAND · deletes the namespace bookshop-dev and everything in it, including the database volume.
```

<!-- test: timeout=300; contains=namespace "bookshop-dev" deleted -->
```bash
kubectl delete namespace bookshop-dev
```

Even the cleanup shows the problem: it works because everything happened to be in one namespace. Objects outside it
(cluster-wide ones) you would have to remember yourself. Helm remembers what it created.

Next, Level 2: [What is Helm?](../docs/01-what-is-helm.md)
