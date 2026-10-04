# Chapter 19 · Helm tests

> Lesson: [lab 14](../labs/14-tests.md). Time: 35 minutes.

## Do

Run the Bookshop's test, read NOTES (with and without an Ingress), query the labels, then the Break It (a service
scaled to zero behind Helm's back) and the books-test challenge.

## Watch for

```text
POD LOGS: shop-test-services (check)
frontend: {"status":"ok","service":"frontend","version":"1.0.0"}
go-status: {"service":"go-status","status":"ok","version":"1.0.0"}
java-api: {"status":"ready","service":"java-api","version":"1.0.0"}
...
all checks passed
```

and, during the Break It, Helm still saying `STATUS: deployed` while the test fails at `java-api`.

## Think like an engineer

A test proves what a deployment can prove: Services route to Ready Pods, the APIs reach the database, the release's
configuration reached the application. It does not prove the application is correct.

A small true story from building this course: the first version of the Bookshop test printed each result with
`echo "name: $(wget ...)"`. A failing `wget` inside `$( )` does not stop a `set -e` script, so the test **passed** with
java-api scaled to zero. Test your tests: break the thing they guard and check that they fail.

Drift (a change made with kubectl) is invisible to Helm: `helm get manifest | kubectl diff ...` shows it,
`helm test` notices it, `helm upgrade` repairs it.

## Checkpoint

- [ ] You can write a test Pod that fails on any failed check.
- [ ] You can run one test by name.
- [ ] You can show the difference between a release's manifest and the live cluster.

Next: [20 · Secrets and security](20-security.md).
