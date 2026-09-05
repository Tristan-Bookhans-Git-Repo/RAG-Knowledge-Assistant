# Deployment Status

**State: infrastructure-as-code complete. Never deployed.**

The deployment path is specified as IaC:
- Terraform modules (VPC, RDS, ECR, EKS, secrets) with root wiring.
- Kubernetes manifests (namespace, deployment with readiness on `/ready`, service,
  ALB ingress, HPA, configmap, secrets).

Both pass static validation (`terraform validate`/`plan`, `kubectl apply --dry-run=client`).
The application runs locally via docker-compose.

A live AWS EKS apply was attempted on 28 Aug 2026 but did not succeed. The apply kept
failing and the effort was halted to avoid further spend. The service has never run on a
cluster. For a personal project, an always-on managed cluster is not a cost the project
justifies, so the deployment stops at validated IaC.

See `docs/05-runbook.md` for the intended apply/deploy procedure and `docs/adr/ADR-007-on-demand-infrastructure-lifecycle.md`
for the cost reasoning behind the on-demand model this was built around.
