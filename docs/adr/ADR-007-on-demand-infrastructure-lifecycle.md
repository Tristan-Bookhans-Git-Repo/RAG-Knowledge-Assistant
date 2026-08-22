# ADR-007: On-demand infrastructure lifecycle (apply/destroy) over an always-on cluster

**Date:** 2026-08-22
**Status:** Accepted

## Context

E10 (`US-10.1`) stands up the full AWS deployment defined by E9's Terraform modules: VPC, RDS, ECR, EKS (control plane + managed node group), and the OIDC trust for GitHub Actions. The original expectation, going into this story, was a lightweight always-on deployment, roughly R100–200/month (~$5–11 USD), that could sit up indefinitely as a live portfolio link.

Pricing the actual resource set against that expectation surfaced a hard mismatch:

| Resource | Cost/month (running continuously) |
|---|---|
| EKS control plane (flat fee, independent of node count/size) | ~$72 |
| 2× `t3.medium` nodes (min/desired size) | ~$60 |
| NAT Gateway (hourly charge alone, before data processing) | ~$32 |
| RDS `db.t4g.micro` + 20GB storage | ~$13 |
| ALB (once the Ingress provisions one) | ~$18 |
| ECR storage + Secrets Manager | ~$3 |
| **Total, idle** | **~$198** |

The EKS control plane fee is flat and unavoidable at $72/month regardless of node size or count: it is not a tunable line item. No combination of smaller instances, fewer nodes, or spot pricing brings a continuously-running EKS cluster within reach of a ~$10/month budget. The next-cheapest architecture that could hit that number would mean dropping EKS/Kubernetes entirely (e.g. ECS Fargate or a single EC2 box), which would undercut the actual purpose of this story: Kubernetes was named directly in the PRD's skill-gap analysis (9/15 target postings) as one of the three gaps this project exists to close. Downgrading the architecture to fit the budget would solve the cost problem by discarding the reason E9/E10 exist.

Three options were considered:

1. **Always-on, as originally planned.** Rejected on cost; ~$198/month indefinitely is not sustainable for a personal portfolio project with no revenue.
2. **Drop EKS for a cheaper always-on architecture** (ECS Fargate, single EC2 instance). Rejected because it removes the Kubernetes claim this project is meant to substantiate. Would require rewriting E9 and misrepresenting the stack on the CV.
3. **Apply on demand, destroy after.** Provision the full stack only when actively needed (interview, demo, portfolio walkthrough), tear it down afterward. Chosen.

## Decision

Operate the AWS deployment as ephemeral infrastructure, not a standing service:

- `terraform apply` is run shortly before the infrastructure is needed (budget 20–30 minutes lead time: EKS cluster creation alone commonly takes 10–15 minutes)
- `terraform destroy` is run when the demo/interview window ends
- The one exception is a documented, deliberate `-target=module.eks`-only teardown for keeping RDS (and the VPC it depends on) alive between sessions at ~$45/month baseline, when avoiding data loss matters more than avoiding that cost. Never `-target=module.vpc`, since RDS's subnet group dependency on the VPC makes that fail or cascade
- The Kubernetes Ingress must be deleted (`kubectl delete -f infra/k8s/ingress.yaml`) and its ALB confirmed gone in the AWS Console *before* `terraform destroy`, because the AWS Load Balancer Controller, not Terraform, creates that ALB dynamically; destroying the cluster out from under a live Ingress orphans it as an untracked, still-billing resource
- The full procedure, including this ordering, is documented in `docs/05-runbook.md`

This is recorded here rather than left implicit in the runbook because it changes what the deployment *is* architecturally, not just how it's operated: there is no persistent public URL, and anyone using this project as a reference (an interviewer clicking a link cold, a future contributor) needs to understand up front that "deployed" means "deployable and demonstrated," not "always reachable."

## Consequences

- **No always-on link.** The project cannot be dropped into a CV or portfolio page as a live URL that works at arbitrary times; it must be spun up ahead of a specific interview or demo window.
- **Data does not survive a destroy.** A full `terraform destroy` removes RDS with everything else; documents and users from a prior session are gone. The migration (`alembic upgrade head`) and a document upload need to be re-run each time the stack comes back up, unless the RDS-persistent `-target` exception is used.
- **`cd.yml`'s auto-deploy only functions while the cluster exists.** A push to `main` while the stack is torn down fails at the `kubectl` steps, expected, not a bug. `KUBE_CONFIG_DATA` goes stale on every teardown/recreate cycle and must be regenerated.
- **Requires operator discipline.** Nothing in AWS stops the meter automatically; forgetting to `destroy` after a demo bills like a permanent deployment. There is no automated shutdown safeguard as of this writing; a manual calendar reminder is the only current mitigation.
- **The CV/README claim this licenses is "deployed and demonstrable on AWS EKS," not "live in production."** Consistent with this project's standing rule against overclaiming production status: this is a personal project run on demand, not a system serving continuous real traffic.
- **Future hardening option, not required for v1:** a scheduled Lambda or GitHub Actions cron that force-destroys infra past a time budget, as a backstop against forgotten teardowns. Noted here as a known gap, not built.
