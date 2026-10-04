# Chapter 15 · Environment-specific values

> Lesson: [lab 10](../labs/10-environments.md). Time: 40 minutes.

## Do

Deploy staging and production next to dev with `helm upgrade --install`, compare them, then the Break It (the
defaults file passed last) and the qa challenge.

## Watch for

```text
demo-dev       window.APP_CONFIG = { ADMIN_URL: "", APP_ENV: "dev" };
demo-staging   window.APP_CONFIG = { ADMIN_URL: "", APP_ENV: "staging" };
demo           window.APP_CONFIG = { ADMIN_URL: "", APP_ENV: "prod" };
```

and the production HPA:

```text
demo-prod   demo-demo-app   Deployment/demo-demo-app   cpu: <unknown>/70%   3   6   ...
```

`<unknown>` because kind has no metrics-server; the HPA still enforces its minimum of 3.

## Think like an engineer

The point of the whole lab is the last row of its table: every environment runs **the same chart version**; only
values differ. A change is tested in dev and staging with exactly the templates that will reach production.

What belongs in an environment file: replicas, image pins, resources, hosts, configuration, autoscaling, volume sizes.
What does not: passwords. Production gets a **reference** to a Secret (chapter 20).

The Break It shows why the chart's own `values.yaml` is never passed with `-f`: it is always applied first, and
passing it last resets every environment setting.

## Checkpoint

- [ ] Three releases named `demo` run in three namespaces with different settings.
- [ ] You can diff two environments' values with `helm get values`.
- [ ] A new environment (qa) cost you one file and no template change.

Next: [16 · Helm repositories](16-repositories.md).
