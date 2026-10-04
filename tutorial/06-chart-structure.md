# Chapter 06 · Understand chart structure

> Lesson: [lab 03](../labs/03-chart-structure.md), sections 1–4. Time: 25 minutes.

## Do

Inspect `charts/demo-app` with `helm show chart|values|readme`, list its templates, and diff its Deployment against a
fresh scaffold.

## Watch for

The scaffold-to-chart diff, three changes:

```text
>         checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
<               containerPort: {{ .Values.service.port }}
>               containerPort: {{ .Values.containerPort }}
>           envFrom:
>             - configMapRef:
```

## Think like an engineer

`helm show` is how you consume charts from other teams: what it is (`chart`), what you can configure (`values`), how
the author wants it used (`readme`). Read all three before installing anything.

The `checksum/config` annotation is a pattern worth memorising. A changed ConfigMap does not restart Pods by itself;
environment variables are read when a container starts. Hashing the rendered ConfigMap into the Pod template turns
"configuration changed" into "Pod template changed", which Kubernetes rolls out.

## Checkpoint

- [ ] You can explain each file in `charts/demo-app` and `templates/`.
- [ ] You can explain the three changes from the scaffold and why each was made.
- [ ] You know what a file starting with `_` in `templates/` is for.

Next: [07 · Chart.yaml](07-chart-yaml.md).
