# Chapter 08 · values.yaml

> Lesson: [lab 04](../labs/04-values.md). Time: 35 minutes.

## Do

The whole lab: hard-coded vs templated Deployment, the values-example renders, demo-app's prod file, the silent typo,
and the schema challenge.

## Watch for

The precedence render:

```text
  environment: "prod"
  replicaCount: "5"
  logLevel: "error"
  features: "{\"recommendations\":true,\"reviews\":true}"
```

Predict each line before you run the command. `replicaCount` 5 (`--set` wins), `logLevel` error (the **later** file
wins), `features.reviews` true (maps merge).

## Think like an engineer

The typo exercise is the important one: `replicacount: 3` produced no error and no effect. Helm passes any key to
the templates; only the keys a template reads matter. That is why reviewers ask "does this key exist?" and why charts
ship a `values.schema.json`. After the challenge, `--set replicaCount=0` fails with:

```text
- at '/replicaCount': minimum: got 0, want 1
```

Rule of thumb: values files for anything that should still be true tomorrow; `--set` for one-off experiments only.

## Checkpoint

- [ ] You can state the precedence order and the merge rules (maps merge, lists replace, `null` removes).
- [ ] You can show all values a release would get with `--dry-run=client --debug`.
- [ ] You can write a minimal `values.schema.json`.

Next: [09 · Helm templates](09-templates.md).
