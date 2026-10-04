# dependency-example · storefront

```text
storefront (parent chart)
 ├── templates/configmap.yaml       its own resources
 └── charts/podinfo-6.15.0.tgz      the dependency, downloaded by "helm dependency update" (alias: catalog)
```

```bash
helm dependency update examples/dependency-example     # downloads charts/podinfo-6.15.0.tgz, writes Chart.lock
helm install shopfront examples/dependency-example -n deps --create-namespace --wait
curl -s http://catalog.localhost:8080/
```

Used in [lab 12 · Dependencies](../../labs/12-dependencies.md). The downloaded `.tgz` is not committed (see
`.gitignore`); `Chart.lock` is, so everyone gets exactly the same dependency version.
