# Chapter 09 · Helm templates

> Lesson: [lab 05](../labs/05-templates.md), with [examples/basic-chart](../examples/basic-chart) open. Time: 45 minutes.

## Do

Read the syntax table, render basic-chart, and match every output line to its template line. Then the Break It (two
mistakes) and the PodDisruptionBudget challenge.

## Watch for

```text
            - name: RELEASE
              value: "web rev 1 in lab-05"
```

`.Release.Name`, `.Release.Revision` and `.Release.Namespace` in one line. And the `if/else`:

```text
          imagePullPolicy: Always        (environment=prod)
```

## Think like an engineer

Don't trust the template just because Helm accepted it: let's render it. The second Break It proves the point: with
`nindent 2` instead of `4`, `helm lint` passes, rendering works, and the API server accepts the dry run, yet the
labels have moved from `metadata.labels` to unknown fields directly under `metadata`:

```text
  labels:
    # nindent 4: ...
  app.kubernetes.io/name: basic-chart
```

The Deployment would be created **without labels**. Only reading the output (or a strict schema validator like
kubeconform) catches it. Helm templates produce text; YAML structure is your responsibility.

## Checkpoint

- [ ] You can explain `{{-`, pipes, `default`, `quote`, `toYaml | nindent`, `include`, `with`, `range`, `.Capabilities`.
- [ ] You can read `unexpected EOF` and find the missing `end`.
- [ ] Your PDB template renders with 3 replicas and disappears with 1.

Next: [10 · Render and debug templates](10-render-and-debug.md).
