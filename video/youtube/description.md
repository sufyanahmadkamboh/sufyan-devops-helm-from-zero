Helm From Zero: start from an application deployed with plain Kubernetes YAML (1,374 lines copied across dev, staging and production), then replace it with one Helm chart and three short values files. Chart structure, chart version vs app version, values and precedence, templates and helpers, rendering and linting, releases, upgrades, rollbacks, multiple environments, repositories and OCI registries, dependencies, hooks, tests, secrets and security, twelve troubleshooting scenarios, a production-style chart and a capstone. Every terminal shows real output, recorded while the lessons ran with Helm 4.3 on a real kind cluster.

💻 The lab (free, open source): https://github.com/sufyanahmadkamboh/sufyan-devops-helm-from-zero
🌐 All my projects: https://sufyanahmadkamboh.github.io/

🧪 Do it yourself (Docker, kind, kubectl and Helm, no cloud account):
1. git clone https://github.com/sufyanahmadkamboh/sufyan-devops-helm-from-zero.git
2. Open tutorial/README.md and follow the 24 chapters (20 levels)
3. Break releases with the troubleshooting scenarios, then take the capstone

⏱️ Chapters
0:00 Introduction
1:34 Why Helm?
2:39 Kubernetes YAML Before Helm
3:36 Install Helm
4:31 Create First Chart
5:31 Chart Structure
6:16 Chart.yaml
7:08 values.yaml
8:19 Templates
9:50 Render Templates
10:24 Helm Lint
11:01 Install Release
12:13 Upgrade
13:30 Rollback
14:56 Environment Values
15:43 Repositories
17:02 Dependencies
18:04 Hooks
19:19 Tests
20:07 Secrets & Security
21:20 Troubleshooting
23:51 Production-Style Chart
24:47 Capstone
26:02 Cleanup

📊 What you will see (all recorded)
• the same five services copied into three environment folders, and the diff that proves it
• an unquoted appVersion 1.10 deploying image tag 1.1
• a wrong nindent that passes lint and a server dry run
• an upgrade that "succeeded" and deleted the Ingress (forgotten values)
• a bad image tag, rollback, --rollback-on-failure, and a release stuck in pending-upgrade
• a failed upgrade that still broke routing (immutable selector, partially applied)
• Helm 4 server-side apply: "conflict with kubectl-patch" and --force-conflicts
• a password passed with --set, read back from Helm's own release record

#Helm #Kubernetes #DevOps
