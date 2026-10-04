{{/*
Named templates ("helpers"), shared by every template of this chart. Call them with include:
  {{ include "bookshop.labels" (dict "root" $ "name" "node-api") }}
Files starting with "_" render nothing on their own.
*/}}

{{/* The name of a component's resources: "<release>-<component>", e.g. "shop-node-api". Max 63 characters. */}}
{{- define "bookshop.name" -}}
{{- printf "%s-%s" .root.Release.Name .name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Labels the Service and the Deployment select on. Never change them after the first install: selectors are immutable. */}}
{{- define "bookshop.selectorLabels" -}}
app.kubernetes.io/name: {{ .name }}
app.kubernetes.io/instance: {{ .root.Release.Name }}
{{- end }}

{{/* All labels: who owns it (release, chart), what it is (name, version) and where it runs (environment). */}}
{{- define "bookshop.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .root.Chart.Name .root.Chart.Version }}
{{ include "bookshop.selectorLabels" . }}
app.kubernetes.io/version: {{ .version | default .root.Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .root.Release.Service }}
app.kubernetes.io/part-of: bookshop
environment: {{ .root.Values.environment | quote }}
{{- end }}

{{/* The image of a component: "<registry>/<name>:<tag>", the tag defaulting to the chart's appVersion. */}}
{{- define "bookshop.image" -}}
{{- printf "%s/%s:%s" .root.Values.imageRegistry .image.name (.image.tag | default .root.Chart.AppVersion) }}
{{- end }}

{{/* Where the database is: the bundled dependency, or database.host for an external one. */}}
{{- define "bookshop.dbHost" -}}
{{- if .Values.database.host }}{{ .Values.database.host }}
{{- else if .Values.postgres.enabled }}{{ printf "%s-postgres" .Release.Name }}
{{- else }}{{ fail "postgres.enabled is false: set database.host to an external PostgreSQL" }}
{{- end }}
{{- end }}

{{/* The Secret with DB_PASSWORD: an existing one (production) or the one this chart creates. */}}
{{- define "bookshop.dbSecret" -}}
{{- .Values.database.existingSecret | default (printf "%s-db" .Release.Name) }}
{{- end }}
