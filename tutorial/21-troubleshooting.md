# Chapter 21 · Troubleshooting

> Lessons: the [12 troubleshooting scenarios](../troubleshooting/README.md), then [lab 15](../labs/15-troubleshooting.md).
> Time: about 3 hours.

## Do

Each scenario in order. For each one, stop after **Symptoms** and write down your hypothesis before reading on. Then
lab 15: a release with two faults, solved with `troubleshooting/triage.sh`.

## Watch for

The scenarios that surprise most people:

- **04 · Wrong selector.** A failed upgrade that still broke the site: the Service got the new selector before the
  Deployment's immutable selector was rejected.

  ```text
  spec.selector: Invalid value: ...: field is immutable
  ```

- **11 · Failed Helm test.** The repair itself fails, because Helm 4 applies with server-side apply and `kubectl
  patch` now owns the field:

  ```text
  Apply failed with 1 conflict: conflict with "kubectl-patch" using v1: .data.APP_ENV
  ```

- **12 · Values conflict.** `--set replicaCount=5` arrived (precedence worked) and changed nothing, because the
  template ignores it when autoscaling is on.

## Think like an engineer

Let's investigate this like we would in production: render (is the chart valid?) → compare (is what Helm applied
what I meant?) → observe (what does Kubernetes say about the objects?) → fix in values or the chart, never only in
the cluster → verify. Change one thing at a time; a second fault can hide behind the first (lab 15).

## Checkpoint

- [ ] For each of the 12 scenarios, you can name the first command you would run.
- [ ] You can explain partial application of a failed upgrade, and how rollback restores consistency.
- [ ] You can decide when `--force-conflicts` is right.

Next: [22 · Production-style chart](22-production-chart.md).
