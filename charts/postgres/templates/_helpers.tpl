{{/* The name of the database Service and StatefulSet: "<release>-postgres". */}}
{{- define "postgres.fullname" -}}
{{- printf "%s-postgres" .Release.Name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "postgres.selectorLabels" -}}
app.kubernetes.io/name: postgres
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "postgres.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{ include "postgres.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: bookshop
{{- end }}

{{/* The Secret that holds the password. */}}
{{- define "postgres.secretName" -}}
{{- .Values.auth.existingSecret | default (printf "%s-db" .Release.Name) }}
{{- end }}
