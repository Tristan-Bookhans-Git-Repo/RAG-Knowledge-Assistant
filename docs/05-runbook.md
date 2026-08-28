# Deployment Runbook

This is the step-by-step for E10 (`US-10.1`): taking the infrastructure-as-code from E9 and actually standing it up in AWS. Everything up to this point (`infra/terraform/`, `infra/k8s/`, `.github/workflows/cd.yml`) is written and validated, but nothing has been applied. This document is what turns it into a real, running deployment.

**Read this whole document before running anything.**

## Cost model: apply on demand, destroy after

This deployment is **not** meant to run continuously. Left up, it costs roughly $198/month even completely idle:

| Resource | Cost/month |
|---|---|
| EKS control plane (flat fee, independent of node count/size) | ~$72 |
| 2× `t3.medium` nodes (min/desired size) | ~$60 |
| NAT Gateway (hourly charge alone, before data processing) | ~$32 |
| RDS `db.t4g.micro` + 20GB storage | ~$13 |
| ALB (once the Ingress provisions one) | ~$18 |
| ECR storage + Secrets Manager | ~$3 |

The EKS control plane fee alone ($72/month, flat, regardless of node count) makes "just run it all the time" incompatible with a lightweight budget. No amount of instance-size tuning changes that number.

**The actual operating model: `terraform apply` before you need to show it, `terraform destroy` when you're done.** A few hours a month of actual runtime costs a few dollars, not two hundred. The tradeoffs that come with this, worth knowing before you rely on it:

- **No always-on link.** You can't casually drop a URL in an interview and expect it to load. You spin it up ahead of time (EKS cluster creation alone takes 10–15 minutes, budget 20–30 minutes total before you need it live).
- **Data doesn't survive a destroy.** `terraform destroy` tears down RDS along with everything else, so any documents/users from a previous demo session are gone. Plan to re-run the migration (step 4) and re-seed a document or two each time you spin it up, or see the note at the end of step 2 if you'd rather keep the database persistent for a small ongoing cost instead.
- **Discipline matters.** Nothing in this setup stops the meter automatically. If you `apply` and forget to `destroy`, it bills like a permanent deployment. Set a calendar reminder if you're not going to destroy it the same day.

---

## 0. Prerequisites checklist

Confirm each of these before starting. Several were set up earlier in the project but are easy to lose track of.

- [ ] Terraform Cloud workspace variable `jwt_secret` set (Terraform variable, sensitive): required, `plan` fails without it
- [ ] Terraform Cloud workspace variable `openai_api_key` set (Terraform variable, sensitive): only if using OpenAI; safe to leave blank otherwise
- [ ] Terraform Cloud workspace variable `github_org` set (Terraform variable): your **exact** GitHub username/org, no default on purpose since a wrong value silently misconfigures the OIDC trust policy
- [ ] Terraform Cloud workspace variables `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` set (Environment variable, sensitive): the IAM user Terraform Cloud itself uses to run `plan`/`apply`. This is a *different* identity from the OIDC role `github_oidc` creates: this one is for TFC to provision things, the OIDC role is for `cd.yml` to deploy things after they exist.
- [ ] `terraform init` / `validate` run locally at least once (see `infra/terraform/`): confirms the config is internally consistent before spending real `plan`/`apply` runs on TFC

---

## 1. AWS credentials + OIDC trust for GitHub Actions

This is mostly already done by `infra/terraform/modules/github_oidc`. Terraform creates the OIDC identity provider and IAM role, you just need to confirm the trust scope and wire the result into GitHub.

1. Double check `github_org`/`github_repo` (prerequisites above) are exactly correct: case-sensitive, matches your repo's actual `owner/repo` on GitHub.
2. Run `terraform apply` (step 2 below covers this properly). This creates the role.
3. After apply, get the role ARN: `terraform output github_actions_role_arn`.
4. In GitHub: repo `Settings → Secrets and variables → Actions → New repository secret`, name it `AWS_CD_ROLE_ARN`, paste the ARN.
5. `cd.yml` already uses `role-to-assume: ${{ secrets.AWS_CD_ROLE_ARN }}`. No `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` secrets needed for this workflow at all.

---

## 2. `terraform apply`: provision all infra

```bash
cd infra/terraform
terraform init      # re-run if you haven't since the last module/provider change
terraform plan       # review carefully, should show only "+ create", nothing unexpected
terraform apply       # type "yes" when prompted
```

This creates, in order of dependency: the VPC, the RDS instance, the ECR repository, the EKS cluster (control plane + managed node group), the OIDC provider/role, and the Secrets Manager entries. Expect this to take a while: EKS cluster creation alone commonly takes 10–15 minutes.

> **Optional: keeping the database persistent between demo sessions.** The default model destroys RDS along with everything else, simplest, but you lose demo data every time. If re-seeding gets old, you can instead only tear down the EKS cluster between sessions and leave RDS (and the VPC it lives in) running:
> ```bash
> terraform destroy -target=module.eks
> # ...later, to bring it back:
> terraform apply
> ```
> Note this only removes the EKS control plane + node group (~$132/month of the ~$198 total). The VPC can't be targeted on its own, since RDS's subnet group still depends on it; Terraform would refuse or cascade in ways you don't want. So this leaves the NAT Gateway (~$32/month) and RDS (~$13/month) running continuously, ~$45/month baseline, not free. `-target` is a blunt instrument Terraform's own docs caution against for routine use, fine for this one deliberate, occasional operation, but don't reach for it as a general habit. Full `terraform destroy` (no `-target`, step 7) is the default and safer choice.

Once it finishes, capture the outputs you'll need for the next steps:

```bash
terraform output
```

You'll specifically need: `ecr_repository_url`, `eks_cluster_name`, `github_actions_role_arn`.

---

## 3. First manual ECR push + `kubectl apply -f infra/k8s/`

This is a **manual** first deploy: proving the whole path works end to end before handing it to the automated `cd.yml`.

**Push the image:**

```bash
aws ecr get-login-password --region <your-region> | docker login --username AWS --password-stdin <ecr_repository_url>
docker build -t <ecr_repository_url>:manual-first-push .
docker push <ecr_repository_url>:manual-first-push
```

**Point kubectl at the new cluster:**

```bash
aws eks update-kubeconfig --name <eks_cluster_name> --region <your-region>
kubectl get nodes    # confirms you're actually talking to the real cluster
```

**Update the placeholder image reference**, then apply the manifests:

In `infra/k8s/deployment.yaml`, replace `PLACEHOLDER_ECR_REPOSITORY_URL:latest` with `<ecr_repository_url>:manual-first-push`.

Also replace the placeholder secret values in `infra/k8s/secrets.yaml`. Don't commit real values into this file; apply a locally-edited copy instead:

```bash
kubectl apply -f infra/k8s/namespace.yaml
kubectl apply -f infra/k8s/configmap.yaml
kubectl apply -f infra/k8s/secrets.yaml       # edited locally with real values, not committed
kubectl apply -f infra/k8s/deployment.yaml
kubectl apply -f infra/k8s/service.yaml
kubectl apply -f infra/k8s/hpa.yaml
kubectl apply -f infra/k8s/ingress.yaml       # needs the AWS Load Balancer Controller installed first, see note below
```

**Before the Ingress will do anything:** the AWS Load Balancer Controller isn't part of this manifest set. It's a cluster add-on that watches for `Ingress` resources with `ingressClassName: alb` and provisions the real ALB. Install it via Helm before applying `ingress.yaml`, or that resource will just sit there inert:

```bash
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=<eks_cluster_name>
```

Check pods are actually coming up:

```bash
kubectl get pods -n rag-assistant
kubectl logs -n rag-assistant deploy/rag-api
```

---

## 4. Migration against the prod DB

Once the pod is running and can reach RDS:

```bash
kubectl exec -it -n rag-assistant deploy/rag-api -- alembic upgrade head
```

If this fails on connectivity, check the RDS security group (`infra/terraform/modules/rds`) actually allows traffic from the EKS node/pod CIDR. It's currently scoped to the whole VPC CIDR, which should cover this, but worth confirming if it doesn't work first try.

---

## 5. Smoke test the public ALB URL

Once the AWS Load Balancer Controller has provisioned the ALB (check `kubectl get ingress -n rag-assistant` for the address, can take a few minutes to appear):

```bash
curl https://<alb-address>/health
curl https://<alb-address>/ready
```

Both should return `200` with a JSON body. If `/ready` reports `db: down` or `ollama: down`, check the relevant connectivity (RDS security group, or, expected, `ollama: n/a` if `LLM_PROVIDER=openai`, which is what `configmap.yaml` sets for this deployment).

Try the actual app in a browser too: register a user, upload a document, ask it a question.

---

## 6. Enable the CD workflow

Once steps 1–5 are confirmed working manually, replace the placeholders in `.github/workflows/cd.yml`'s `env:` block with the real values:

```yaml
env:
  AWS_REGION: <your-region>
  ECR_REPOSITORY: <repository name from ecr_repository_url>
  EKS_DEPLOYMENT: rag-api
  CONTAINER_NAME: rag-api
  APP_URL: https://<alb-address>
```

Also add the `KUBE_CONFIG_DATA` GitHub secret (base64-encoded kubeconfig for the cluster: `cat ~/.kube/config | base64` after step 3's `update-kubeconfig`, scoped ideally to a service account with limited permissions rather than your own admin kubeconfig, but your own is fine to get started).

From here, every push to `main` triggers `cd.yml`: build → push to ECR → `kubectl set image` → wait for rollout → smoke test `/health`.

**Given the on-demand operating model (see the cost note at the top), "auto-deploy" doesn't mean "always live."** `cd.yml` only succeeds while the cluster actually exists. If you push to `main` after tearing everything down, the workflow will fail at the `kubectl` steps (no cluster to reach), which is expected, not a bug. Its real use is redeploying a fix *during* a demo window if you spin the cluster up, notice something, and push again, not a permanent, continuously-live pipeline given the cost model chosen here. `KUBE_CONFIG_DATA` also goes stale every time you tear down and recreate the cluster (new cluster, new credentials); regenerate and re-save that secret each time you `apply` again.

---

## 7. Tearing down

**Delete the Ingress before destroying the cluster: this is the one step that's easy to skip and expensive to get wrong.** The ALB isn't a Terraform-managed resource at all; it's created dynamically by the AWS Load Balancer Controller running *inside* the cluster, in response to the `Ingress` manifest. If the cluster is destroyed while that Ingress still exists, the controller never gets the chance to clean up the real ALB it created. It becomes an orphaned AWS resource nothing in Terraform or Kubernetes knows about anymore, and it keeps billing until you find and delete it manually in the console.

```bash
kubectl delete -f infra/k8s/ingress.yaml
# give it a minute, check the ALB is actually gone before proceeding:
# AWS Console → EC2 → Load Balancers, confirm nothing's left over

cd infra/terraform
terraform destroy    # type "yes" when prompted
```

Afterwards, double check nothing was left behind: AWS Console, check EC2 (no stray load balancers or instances), RDS (no orphaned instance if you did a full destroy), and Secrets Manager (secrets are usually only soft-deleted with a recovery window by default, not an ongoing cost concern, but worth knowing they don't vanish immediately).

---

## 8. This document

Kept up to date as the deployment process actually changes. If a step above turns out wrong or incomplete once you run it for real, fix it here too, not just in your head.
