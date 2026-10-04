# Chapter 24 · Cleanup and final review

> Lessons: the [challenges](../challenges/README.md), then [cleanup](../labs/cleanup.md). Time: 60 minutes.

## Do

1. The 12 [challenges](../challenges/README.md): they build one chart from an empty folder to a tested,
   multi-environment chart with a dependency. Do them without opening the solutions first.
2. [Cleanup](../labs/cleanup.md): remove Traefik, the repositories, and the cluster.

## Skills checklist

Tick only what you could do without looking at the lessons.

| Level | I can... |
|---|---|
| 1–2 | explain the YAML duplication problem and what Helm does about it |
| 3–5 | install Helm, create a chart, explain every file in it |
| 5 | explain chart version vs app version and package with any versions |
| 6 | predict the result of several `-f` files and `--set`; write a values schema |
| 7 | write templates with `if`, `range`, `with`, `default`, `quote`, `toYaml`, `nindent`, `include` |
| 8 | render and lint for every environment; use `--dry-run=server` |
| 9 | install a release and answer "what did it get, what did Helm apply, where is it stored" |
| 10 | review an upgrade with a diff; avoid the forgotten-values trap |
| 11 | roll back; recover a stuck release; explain `--rollback-on-failure` |
| 12 | run three environments from one chart version |
| 13 | review, install and upgrade a third-party chart; publish to OCI |
| 14 | add a dependency; explain `Chart.lock`; repair a dependency problem |
| 15 | use hooks sparingly and explain a failing hook |
| 16 | write a test that really fails; detect drift |
| 17 | review a chart's security; keep secrets out of values and release history |
| 18 | troubleshoot with a method; explain partial upgrades and server-side apply conflicts |
| 19–20 | design a production-style chart and operate it through a full lifecycle |

## Self-test

1. A teammate says "I set `replicaCount: 5` and nothing changed". Name three possible causes.
2. Why does a chart's version change when only `appVersion` changes?
3. What is stored in `sh.helm.release.v1.shop.v4`?
4. What does `helm uninstall` leave behind?
5. Why should `helm template | kubectl apply` never be used to upgrade a Helm release?
6. A failed upgrade broke the site. How can that be, if it failed?
7. When would you use `--force-conflicts`?
8. Name two cases where a hook is the right tool and two where it is not.
9. Your test passes but the app is broken. What do you check in the test?
10. How do you promote a tested release from staging to production?

Answers: the [interview questions](../study/interview-questions.md) and the linked lessons cover every one.

## Where to go next

- Package one of your own applications as a chart, with a values file per environment and a test.
- Add a GitOps tool (Argo CD or Flux) that deploys your chart from Git.
- The [cheat sheet](../docs/cheat-sheet.md) and [best practices](../docs/15-best-practices.md) are your reference.

Congratulations: you can now say, and show, that you understand why Helm exists, how charts, values and templates
work, how to manage, upgrade and roll back releases across environments, how to use repositories, dependencies,
hooks and tests, and how to troubleshoot Helm deployments.
