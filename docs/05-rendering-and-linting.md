# Rendering and linting

> Hands-on: [lab 06](../labs/06-rendering.md).

## 1 · What is it?

**Rendering** (`helm template`) turns a chart plus values into the plain YAML Helm would apply. **Linting** (`helm
lint`) checks a chart for errors and bad practices.

## 2 · Why do we need it?

Don't trust the template just because Helm accepted it: render it. Seeing the exact output is the only way to know
what will reach the cluster; lint catches broken charts in seconds, before a cluster does.

## 3 · How does it work?

Both run on your computer, without a cluster: defaults for `.Capabilities`, an empty `lookup`, no API validation.
`helm install/upgrade --dry-run=server` does the same with the real cluster: real capabilities, real `lookup`, and
the API server validates every object without creating it.

## 4 · What problem does it solve?

Late failures. Template syntax, values mistakes and malformed objects are found at review time, not at deploy time.

## 5 · How do I use it?

Lint and render for **every** environment's values in CI; render to a folder (`--output-dir`) or diff renders in code
review; `--dry-run=server` just before applying.

## 6 · What command should I run?

```bash
helm lint charts/demo-app -f charts/demo-app/values-prod.yaml [--strict]
helm template demo charts/demo-app -f charts/demo-app/values-prod.yaml [--show-only templates/x.yaml] [--output-dir DIR]
helm template demo charts/demo-app | kubeconform -strict -summary
helm install demo charts/demo-app --dry-run=server
```

## 7 · What output should I expect?

`1 chart(s) linted, 0 chart(s) failed`; `[INFO]`/`[WARNING]`/`[ERROR]` lines when not. `helm template` prints YAML.

## 8 · What can go wrong?

Lint stops at the first blocking error per stage: values files are parsed first, then `Chart.yaml`, then templates
([lab 06](../labs/06-rendering.md#troubleshoot-it)). Some mistakes pass both lint and server dry-run (wrong
indentation that still parses): only a strict schema check or a careful read catches them.

## 9 · How do I troubleshoot it?

Fix one error, lint again; `--debug` to see invalid output; `--show-only` to focus on one file.

## 10 · Where is it used in real DevOps work?

The "render check" job of every chart's CI pipeline ([this repository's](../.github/workflows/test.yaml)), and in
reviews: "show me the rendered diff".
