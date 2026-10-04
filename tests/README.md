# tests · how the lessons are tested

Every command in this repository's lessons is executed automatically. The outputs under the commands are what they
printed in a real run.

## The runner: mdrun.py

`tests/mdrun.py` reads Markdown files and runs their ```bash blocks in order, on your computer, from the repository
root (a `cd` in one block carries over to the next, like in your terminal). An HTML comment right above a block (it
does not show on GitHub) says what to expect:

| Annotation | Meaning |
|---|---|
| `contains=TEXT` / `absent=TEXT` | the output must / must not contain TEXT (can repeat) |
| `fail` | the command is expected to fail (non-zero exit), e.g. when we break something on purpose |
| `retry=N` | repeat up to N times, 2 s apart (for things that become ready over time) |
| `timeout=S` | give up after S seconds (default 600) |
| `output`, `output=head:N`, `output=tail:N` | with `--update`, write the real output into the ```text block below |
| `skip` | never run (installers, optional plugins) |
| `<!-- test-run: command -->` | a hidden step that runs but is not shown (setup or cleanup) |

```text
python3 tests/mdrun.py [--update] [--record DIR] [--stop-on-failure] FILE.md [FILE.md ...]
```

`--record DIR` saves every command with its output, exit code and duration (the video's terminals are built from
these). Outputs are sanitised before they are written: your home and repository paths, your user name, e-mail
addresses (except the reserved `example.com/org/net`) and anything that looks like a cloud account ID are masked.

Run the whole course locally, in the same order as CI (about 60–90 minutes, most of it waiting for Pods):

```text
python3 tests/mdrun.py --update --stop-on-failure labs/00-setup.md environments/README.md \
  labs/0[1-9]-*.md labs/1[0-4]-*.md docs/13-security.md troubleshooting/[0-9]*.md \
  labs/15-troubleshooting.md docs/16-production-style-chart.md labs/16-capstone.md challenges/README.md labs/cleanup.md
```

(The runner can also execute blocks inside virtual machines; that feature comes from an earlier course and is not used
here.)

## In CI

[.github/workflows/test.yaml](../.github/workflows/test.yaml), on fresh GitHub-hosted Ubuntu machines, with Helm
4.3.0 (checksum verified):

| Job | What it proves |
|---|---|
| Static checks | every relative link resolves; every chart lints (`--strict`) and renders to valid Kubernetes objects (kubeconform, strict) with **each** of its values files; the raw YAML environments are valid; ShellCheck |
| Lessons | a kind cluster with Traefik; every lab, the security and production-chart lessons, the 12 troubleshooting scenarios, the capstone, the challenges and the cleanup, in course order |
| Publish (main) | `demo-app`, `postgres` and `bookshop` are packaged and pushed to `oci://ghcr.io/sufyanahmadkamboh/charts` |

The lessons job uploads its recordings and a patch with the real outputs as an artifact.

## Helpers

| File | Purpose |
|---|---|
| [check_links.py](check_links.py) | every relative link and `#anchor` in every Markdown file |
| [screenshot.py](screenshot.py) | headless browser screenshots for lesson images (skipped where no browser exists) |
