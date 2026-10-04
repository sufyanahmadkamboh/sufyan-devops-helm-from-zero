# Chapter 05 · Create your first chart

> Lesson: [lab 02](../labs/02-first-chart.md). Time: 30 minutes.

## Do

The whole lab: `helm create`, lint, render, install into `lab-02`, test, break `Chart.yaml`, then the challenge
(point the chart at the Bookshop frontend).

## Watch for

The scaffold's Deployment, rendered:

```text
          image: "nginx:1.16.0"
```

`values.yaml` says `tag: ""`, so the template falls back to `appVersion`. Then:

```text
TEST SUITE:     hello-test-connection
Phase:          Succeeded
```

## Think like an engineer

Don't delete what `helm create` generated just because you don't understand it yet: it is the convention most charts
in the world follow (helper names, labels, the `ingress.enabled` and `autoscaling.enabled` switches). When you open a
third-party chart, you will recognise this skeleton everywhere.

In the challenge, notice you changed the image **and** the port without touching a template: the scaffold reuses
`service.port` for `containerPort`. Useful, and also a design decision worth questioning (chapter 06 shows why
demo-app separates them).

## Checkpoint

- [ ] You can name the purpose of each generated file.
- [ ] The release `hello` showed `REVISION 2` after the challenge, running `bookshop-frontend:1.0.0`.
- [ ] You know what `helm lint` reports for a chart without a name, and that its exit code fails a pipeline.

Next: [06 · Understand chart structure](06-chart-structure.md).
