{{/* define: a named template. Written once here, used everywhere with include. */}}

{{/* The name of every resource: the release name, so two installs of this chart never collide. */}}
{{- define "basic.fullname" -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Selector labels: the ones a Service and a Deployment select Pods with. */}}
{{- define "basic.selectorLabels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/* All labels: selector labels + version + environment + who manages it. */}}
{{- define "basic.labels" -}}
{{ include "basic.selectorLabels" . }}
app.kubernetes.io/version: {{ .Values.image.tag | default .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
environment: {{ .Values.environment | quote }}
{{- with .Values.extraLabels }}
{{ toYaml . }}
{{- end }}
{{- end }}
