# 10 · Dependency problem

> No cluster needed. Time: 10 minutes.

## Break it

The database team releases a new version of their chart: `postgres` 0.2.0. The application team's chart, `bookshop`,
was not told. A copy of both charts, side by side as in the repository:

<!-- test-run: rm -rf labs/work/ts10 && mkdir -p labs/work/ts10 && cp -r charts/bookshop charts/postgres labs/work/ts10/ && rm -rf labs/work/ts10/bookshop/charts -->

<!-- test: contains=version: 0.2.0 -->
```bash
sed -i 's/^version: 0.1.1/version: 0.2.0/' labs/work/ts10/postgres/Chart.yaml
grep '^version' labs/work/ts10/postgres/Chart.yaml
```

## Problem

The bookshop pipeline fails at its first step, before linting.

## Symptoms

<!-- test: fail; contains=can't get a valid version; output -->
```bash
helm dependency build labs/work/ts10/bookshop
```

```text
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "podinfo" chart repository
...Successfully got an update from the "traefik" chart repository
Update Complete. ⎈Happy Helming!⎈
Saving 1 charts
Save error occurred:  can't get a valid version for dependency postgres
Error: can't get a valid version for dependency postgres
```

And anything that needs the chart fails too, because the dependency was never put in place:

<!-- test: fail; contains=missing in charts/ directory: postgres; output -->
```bash
helm template shop labs/work/ts10/bookshop
```

```text
Error: an error occurred while checking for chart dependencies. You may need to run 'helm dependency build' to fetch missing dependencies: found in Chart.yaml, but missing in charts/ directory: postgres
```

## Investigation

Three files have to agree: what the parent **asks for** (`Chart.yaml`), what it **locked** (`Chart.lock`), and what
the source **offers** (here the folder `../postgres`; for a repository, its index).

## Commands

<!-- test: contains=missing; output -->
```bash
helm dependency list labs/work/ts10/bookshop
```

```text
NAME    	VERSION	REPOSITORY        	STATUS 
postgres	0.1.1  	file://../postgres	missing
```

<!-- test: contains=0.2.0; output -->
```bash
echo "asks for:  $(sed -n '/dependencies:/,$p' labs/work/ts10/bookshop/Chart.yaml | grep version)"
echo "locked:    $(grep version labs/work/ts10/bookshop/Chart.lock)"
echo "available: $(grep '^version' labs/work/ts10/postgres/Chart.yaml)"
```

```text
asks for:      version: 0.1.1
locked:      version: 0.1.1
available: version: 0.2.0
```

## Output Interpretation

- `helm dependency list`: `postgres 0.1.1 ... missing`: the parent wants 0.1.1 and `charts/` does not have it.
- The parent asks for exactly `0.1.1` and locked `0.1.1`, but the source now only offers `0.2.0`. A `file://`
  dependency has exactly one version: whatever the folder currently contains.
- `dependency build` follows the lock file, so it looks for 0.1.1 and cannot find it: `can't get a valid version`.

## Root Cause

A dependency moved to a version the parent does not accept. The same happens with a repository when a version is
removed from its index, or when `Chart.yaml` is edited without running `helm dependency update` (then the error is
"the lock file (Chart.lock) is out of sync with the dependencies file").

## Fix

Decide deliberately to take the new version: read what changed in the dependency (0.1 → 0.2 may be breaking), then
update the requirement and re-lock:

<!-- test: timeout=120; contains=Saving 1 charts; output -->
```bash
sed -i '/- name: postgres/{n;s/version: 0.1.1/version: 0.2.0/}' labs/work/ts10/bookshop/Chart.yaml
helm dependency update labs/work/ts10/bookshop
```

```text
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "podinfo" chart repository
...Successfully got an update from the "traefik" chart repository
Update Complete. ⎈Happy Helming!⎈
Saving 1 charts
Deleting outdated charts
```

## Verification

<!-- test: contains=0.2.0; contains=ok; contains=0 chart(s) failed; output -->
```bash
helm dependency list labs/work/ts10/bookshop
grep version labs/work/ts10/bookshop/Chart.lock
helm lint labs/work/ts10/bookshop | tail -1
helm template shop labs/work/ts10/bookshop | grep 'helm.sh/chart: postgres' | sort -u
```

```text
NAME    	VERSION	REPOSITORY        	STATUS
postgres	0.2.0  	file://../postgres	ok    

  version: 0.2.0
1 chart(s) linted, 0 chart(s) failed
        helm.sh/chart: postgres-0.2.0
    helm.sh/chart: postgres-0.2.0
```

<!-- test -->
```bash
rm -rf labs/work/ts10
```

## Lesson Learned

- Dependency errors appear before any template is rendered: `dependency build/update` and `template` stop
  immediately. `helm dependency list` shows each dependency's status.
- `Chart.yaml` = what you accept, `Chart.lock` = what you tested, `charts/` = what will be packaged. Keep them in sync
  with `helm dependency update`, and commit `Chart.lock`.
- Pin exact versions for reproducible builds; ranges (`~0.2.0`, `^1.0.0`) accept new patch/minor versions
  automatically, which is convenient and less predictable.
- Taking a new dependency version is a change like any other: read its changelog, render the diff, test.
