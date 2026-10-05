Most teams that run the same app in dev, staging and production keep three copies of the same Kubernetes YAML. One change means three edits, a forgotten copy means environments silently drift apart, and nothing records what was deployed or how to undo it. So I built a free, hands-on Helm lab that starts exactly there. ⎈👇

Think of a recipe. You don't rewrite the whole recipe for a dinner for 2 and a dinner for 20: you keep one recipe and change the quantities. A Helm chart is the recipe (templates, written once); a values file is the quantities for one environment.

That is "Helm From Zero", built on the Bookshop platform (React frontend, Node.js, Python, Go and Java APIs, PostgreSQL):

📁 Level 1: the Bookshop as raw YAML, three folders, 1,374 lines, mostly copies
⎈ one chart replaces them: 3 lines of values for dev, 9 for staging, 32 for production (which adds autoscaling and disruption budgets)
🔁 install, review the change as a diff, upgrade, test, roll back, read the history

The things that surprised me while building and testing it:
🔹 an unquoted appVersion: 1.10 becomes the number 1.1, and that is the image tag Helm deploys
🔹 a wrong nindent passes helm lint AND a server-side dry run, and creates a Deployment without labels
🔹 a failed upgrade can still take a site down: the Service took the new selector before the Deployment's immutable selector was rejected
🔹 Helm 4 uses server-side apply: after a kubectl patch, the next helm upgrade fails with "conflict with kubectl-patch" until you decide who is right
🔹 a password passed with --set is stored in Helm's release Secret, readable with plain kubectl
🔹 my own Helm test once passed with a service scaled to zero (a failure hidden inside $( )); tests need testing too

12 troubleshooting scenarios reproduce failures like these, each one: symptoms → investigation → root cause → fix → verification.

✅ Every command in 17 labs, the 12 scenarios, 12 challenges and the 19-step capstone runs automatically in GitHub Actions on a real kind cluster with Helm 4.3; the outputs in the docs are the real outputs.
✅ CI lints every chart with every values file, validates the rendered YAML with kubeconform, and publishes the charts to GHCR as OCI artifacts.

Study material: 16 concept pages (10 questions each), a cheat sheet, a 24-chapter guided course, a 24-chapter video (27 minutes, full and silent versions), a 74-page study guide PDF, a 71-term glossary and 25 interview questions.

🔗 Repository: https://github.com/sufyanahmadkamboh/sufyan-devops-helm-from-zero
🌐 All my projects: https://sufyanahmadkamboh.github.io/

How many copies of the same YAML does your team keep? 💬

#Helm #Kubernetes #DevOps #CloudNative #PlatformEngineering #GitOps #LearningDevOps #OpenSource
