# Chapter 02 · The Kubernetes YAML problem

> Lesson: [Level 1 · The YAML problem](../environments/README.md). Time: 30 minutes.

## Before Helm, let's see the problem

Here is the Kubernetes application we already know how to deploy manually: the Bookshop, five services and a
database, as plain YAML. Now imagine maintaining it across development, staging and production.

## Do

Run the whole Level 1 lesson: deploy `environments/dev/` with `kubectl apply`, verify it, then measure the three
folders.

## Watch for

```text
  458 total            (dev)
  458 total            (staging)
  458 total            (prod)
74                     (diff lines between dev and staging; each changed line counts twice)
```

and the routine change:

```text
environments/dev/deployments.yaml:79:          image: ghcr.io/sufyanahmadkamboh/bookshop-node-api:1.0.0
environments/prod/deployments.yaml:79:          image: ghcr.io/sufyanahmadkamboh/bookshop-node-api:1.0.0
environments/staging/deployments.yaml:79:          image: ghcr.io/sufyanahmadkamboh/bookshop-node-api:1.0.0
```

## Think like an engineer

Raw YAML is not wrong. For one application in one environment it is the clearest thing there is. The problems
appear with **repetition**: one change becomes N edits, a forgotten edit becomes silent drift, and nothing records
what was applied or lets you undo the whole application. Look at the secret file too: the password is in the
repository, because the folder has to be applicable as-is.

Write down what differs between the environments (namespace, replicas, `APP_ENV`, host, volume size, password).
That list is exactly what will become **values**.

## Checkpoint

- [ ] The Bookshop opened at `http://dev.bookshop.localhost:8080/` with `dev` in its footer.
- [ ] You can name four kinds of differences between dev and prod.
- [ ] You can explain why `kubectl apply -f environments/dev/` alone fails (the namespace order).
- [ ] You deleted `bookshop-dev` at the end.

Next: [03 · What is Helm?](03-what-is-helm.md).
