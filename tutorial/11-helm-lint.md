# Chapter 11 · Helm lint

> Lesson: [lab 06](../labs/06-rendering.md), section 3 to the end. Time: 20 minutes.

## Do

Lint demo-app with each environment, then the Break It: one chart, three mistakes. Fix them one at a time as the lab
shows. Finish with the render-check challenge.

## Watch for

The first lint reports only one problem:

```text
Error: failed to parse labs/work/lint-me/values-dev.yaml: ... yaml: line 12: found character that cannot start any token
```

Fix it, and the next one appears:

```text
[ERROR] Chart.yaml: version 'latest' is not a valid SemVer
```

then:

```text
[ERROR] templates/: parse error at (demo-app/templates/deployment.yaml:47): unexpected "}" in operand
```

## Think like an engineer

Lint stops at the first blocking problem of each stage, and the stages run in order: values files, then Chart.yaml,
then templates. So "fix one, run again" is not impatience, it is the method. Don't stack three fixes and hope.

Lint every environment's values, not just the defaults: a mistake may exist only in `values-prod.yaml`, or only in a
template branch that prod switches on.

## Checkpoint

- [ ] You know the order in which lint reports problems.
- [ ] Your render-check script fails on any lint or render error for any environment.
- [ ] You can explain why "latest" can never be a chart version.

Next: [12 · Install a release](12-install-release.md).
