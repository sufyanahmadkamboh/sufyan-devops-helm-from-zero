# 01 · Template syntax error

> No cluster needed. Time: 10 minutes.

## Break it

A teammate adds a TLS option to the Ingress template and opens a pull request. Their change, applied to a copy of
the chart:

<!-- test-run: rm -rf labs/work/ts01 && mkdir -p labs/work && cp -r charts/demo-app labs/work/ts01 -->

<!-- test: contains=tls -->
```bash
cat > labs/work/ts01/templates/ingress.yaml <<'EOF'
{{- if .Values.ingress.enabled -}}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "demo-app.fullname" . }}
  labels:
    {{- include "demo-app.labels" . | nindent 4 }}
spec:
  {{- with .Values.ingress.className }}
  ingressClassName: {{ . }}
  {{- end }}
  {{- if .Values.ingress.tls }}
  tls:
    {{- range .Values.ingress.tls }}
    - hosts:
        {{- range .hosts }}
        - {{ . | quote }}
        {{- end }}
      secretName: {{ .secretName }}
    {{- end }}
  rules:
    {{- range .Values.ingress.hosts }}
    - host: {{ .host | quote }}
      http:
        paths:
          {{- range .paths }}
          - path: {{ .path }}
            pathType: {{ .pathType }}
            backend:
              service:
                name: {{ include "demo-app.fullname" $ }}
                port:
                  number: {{ $.Values.service.port }}
          {{- end }}
    {{- end }}
{{- end }}
EOF
grep -n 'ingress.tls' labs/work/ts01/templates/ingress.yaml
```

## Problem

The CI pipeline for the pull request fails at the render step, and nobody can install the chart.

## Symptoms

<!-- test: fail; contains=unexpected EOF; output -->
```bash
helm template demo labs/work/ts01 -f charts/demo-app/values-dev.yaml
```

```text
Error: parse error at (demo-app/templates/ingress.yaml:37): unexpected EOF

Use --debug flag to render out invalid YAML
```

## Investigation

The error comes from the **template parser**, before any YAML exists: Helm could not even read the template. It
names the file and the line where parsing stopped. `unexpected EOF` (end of file) means a block was opened and never
closed: the parser was still looking for an `end` when the file ended.

## Commands

`helm lint` reports the same error together with any other problems of the chart:

<!-- test: fail; contains=ingress.yaml; output -->
```bash
helm lint labs/work/ts01 -f charts/demo-app/values-dev.yaml
```

```text
==> Linting labs/work/ts01
[INFO] Chart.yaml: icon is recommended
[ERROR] templates/: parse error at (demo-app/templates/ingress.yaml:37): unexpected EOF

Error: 1 chart(s) linted, 1 chart(s) failed
```

Count the openings and closings of blocks in the file:

<!-- test: output -->
```bash
echo "opened: $(grep -cE '\{\{-? *(if|range|with|define) ' labs/work/ts01/templates/ingress.yaml)"
echo "closed: $(grep -cE '\{\{-? *end' labs/work/ts01/templates/ingress.yaml)"
```

```text
opened: 7
closed: 6
```

## Output Interpretation

Seven blocks opened (`if ingress.enabled`, `with className`, `if tls`, `range tls`, the nested `range .hosts`,
`range hosts`, `range paths`), six `end`s: one is missing. Read the template top-down, pairing each block with its `end`: the
`{{- if .Values.ingress.tls }}` block has its `range ... end`, but no `end` of its own before `rules:` begins.

## Root Cause

A missing `{{- end }}` for `{{- if .Values.ingress.tls }}`. Go templates have no indentation rules: the parser only
knows a block ends when it sees `end`, so the error appears at the end of the file, not where the `end` is missing.

## Fix

Close the `if` right after the `range` that renders the `tls` entries:

<!-- test: contains=0 chart(s) failed -->
```bash
sed -i 's/^  rules:$/  {{- end }}\n  rules:/' labs/work/ts01/templates/ingress.yaml
helm lint labs/work/ts01 -f charts/demo-app/values-dev.yaml | tail -1
```

## Verification

Render with and without TLS: both must produce a valid Ingress.

<!-- test: contains=secretName: demo-tls; output -->
```bash
helm template demo labs/work/ts01 -f charts/demo-app/values-dev.yaml --show-only templates/ingress.yaml | grep -c 'kind: Ingress'
helm template demo labs/work/ts01 -f charts/demo-app/values-dev.yaml --show-only templates/ingress.yaml \
  --set 'ingress.tls[0].secretName=demo-tls' --set 'ingress.tls[0].hosts[0]=demo-dev.localhost' | sed -n '/tls:/,/rules:/p'
```

```text
1
  tls:
    - hosts:
        - "demo-dev.localhost"
      secretName: demo-tls
  rules:
```

<!-- test -->
```bash
rm -rf labs/work/ts01
```

## Lesson Learned

- `unexpected EOF` / `unexpected {{end}}` = unbalanced blocks. The reported line is where the parser gave up, not
  where the mistake is.
- Render every chart change in CI (`helm lint` + `helm template`), with every environment's values: a template
  branch that only renders with `tls` set can hide a bug from a render without it.
- Indent template blocks consistently: it makes missing `end`s visible in review.
