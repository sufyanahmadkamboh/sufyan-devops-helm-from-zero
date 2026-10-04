# Chapter 20 · Secrets and security

> Lesson: [Level 17 · Security](../docs/13-security.md), then [ConfigMaps and Secrets](../docs/12-configmaps-and-secrets.md).
> Time: 35 minutes.

## Do

Run the security lesson: review Traefik's RBAC, audit the Bookshop's images and security contexts, then the three
secret facts and the existing-Secret pattern.

## Watch for

What an ingress controller may do:

```text
["secrets"]  ["get","list","watch"]
```

and a value passed with `--set`, read back from Helm's own record with nothing but kubectl:

```text
"apiToken":"example-not-a-real-token"
```

## Think like an engineer

Installing a chart creates Kubernetes resources: chart security is Kubernetes security. Read what a chart creates
(cluster-wide objects, privileged settings, images) before trusting it.

For secrets, three facts: values files end up in Git; `--set` ends up in the release Secret (and shell history, and
CI logs); a templated Secret is base64, not encryption. Safe patterns: generate in the cluster, reference an existing
Secret by name, sync from a secret manager, or encrypt in Git.

While writing this lesson, the security audit found something real: the PostgreSQL subchart's Pod ran without
`runAsNonRoot` and with an API token mounted. The fix (run as the image's `postgres` user, UID 70, drop
capabilities, no token) became postgres chart `0.1.1`. Audits are worth running on your own charts too.

## Checkpoint

- [ ] You can list five things to check before installing a third-party chart.
- [ ] You can explain why `--set password=...` is not safer than a values file.
- [ ] You can describe the existing-Secret pattern and what the chart renders with it (no Secret).

Next: [21 · Troubleshooting](21-troubleshooting.md).
