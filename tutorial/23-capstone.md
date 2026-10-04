# Chapter 23 · Capstone

> Lesson: [lab 16](../labs/16-capstone.md). Time: 1 hour with the reference chart, up to 4 hours if you build your own
> (recommended).

## Do

The 19-step workflow: deploy staging with raw YAML, identify the duplication, build (or study) the chart, lint,
render, install, verify, upgrade node-api to 1.1.0 with a reviewed overlay, break the upgrade, troubleshoot, roll
back, test, read the history, clean up. Then the challenge: promote the tested state to production as chart 1.2.1.

## Watch for

The upgrade preview, limited to what you meant to change:

```text
-        image: ghcr.io/sufyanahmadkamboh/bookshop-node-api:1.0.0
+        image: ghcr.io/sufyanahmadkamboh/bookshop-node-api:1.1.0
```

The test after the rollback:

```text
java-api: {"status":"ready","service":"java-api","version":"1.0.0"}
node-api: {"status":"ready","service":"node-api","version":"1.1.0"}
```

And the history, which tells the story of your week:

```text
1   Install complete
2   Upgrade complete
3   Upgrade "shop" failed: resource Deployment/bookshop-staging/shop-java-api ...
4   Rollback to 2
```

## Think like an engineer

This is the workflow a team runs every week: a values change, reviewed as a diff, applied with `--wait`, verified by
a test, recorded in history, reversible in one command. Nothing in it required a meeting to reconstruct what
happened.

## Checkpoint

- [ ] Your chart (or the reference) meets every requirement in the capstone's table.
- [ ] You completed all 19 steps, and the challenge: production runs `bookshop-1.2.1`, staging `bookshop-1.2.0`.
- [ ] You can tell the capstone's history as a story to a colleague.

Next: [24 · Cleanup and final review](24-cleanup-and-review.md).
