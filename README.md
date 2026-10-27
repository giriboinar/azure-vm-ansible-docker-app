# Service Health API on an Azure VM (Terraform + Ansible + Docker)

A small FastAPI service that keeps an in-memory registry of services a team
wants to watch, with a health endpoint and Prometheus metrics. It runs in a
Docker container on a single Azure VM, provisioned with Terraform and
deployed with Ansible — a realistic, low-cost pattern for a demo or an
internal tool.

> **No Docker daemon is available in the author's sandbox**, so the image is
> built in GitHub Actions CI, not locally. No Azure resources are created by
> this repository alone — `terraform apply` only runs when you choose to run
> it with your own Azure account.

## Features

- `GET /` — service info; `GET /health` — liveness check
- `GET /api/services`, `POST /api/services`, `GET /api/services/{id}`,
  `DELETE /api/services/{id}` — service registry (in-memory)
- `GET /metrics` — Prometheus metrics (`services_created_total`,
  `services_total`)
- Pydantic validation: empty names are rejected with HTTP 422
- Non-root container user, `HEALTHCHECK`, pinned Python dependencies

## Architecture

```
GitHub Actions CI (pytest, Trivy, Terraform validate, Ansible syntax check, Docker build)
        |
        v
Terraform (azurerm) -> Resource Group, VNet, Subnet, NSG, Public IP, NIC,
                       Linux VM (Standard_B1s, Ubuntu 22.04)
        |
Ansible playbook -> installs Docker + Compose plugin, runs
                    `docker compose up -d --build`, verifies /health
        |
Docker Compose -> FastAPI app on port 8000 (Prometheus scrapes /metrics)
```

## Technologies

| Piece | Choice | Why |
|---|---|---|
| App | FastAPI + Uvicorn | Small, typed, fast to test |
| Container | Docker + Compose | One command to run anywhere |
| Cloud | Azure VM (Standard_B1s) | Cheapest VM shape; no managed-service bill for a demo |
| IaC | Terraform (azurerm ~> 4.0) | Declarative, reviewable, destroyable |
| Config | Ansible | Idempotent Docker install + deploy, no agent needed |
| CI | GitHub Actions | Tests, Trivy scan, Terraform validate, Ansible syntax check, image build |
| Metrics | Prometheus client | Standard `/metrics` endpoint |

## Run locally (no Azure needed)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r app/requirements.txt
pip install pytest==9.0.3 httpx==0.28.1
python -m pytest tests/ -q
uvicorn app.main:app --port 8000
# or: docker compose up --build   (needs a Docker daemon)
```

## Deploy to Azure (your account, your decision)

```bash
cd terraform
terraform init
terraform apply \
  -var ssh_public_key="$(cat ~/.ssh/id_ed25519.pub)" \
  -var allowed_ssh_cidr="YOUR_PUBLIC_IP/32"
# note the api_url output, then:
git clone <this-repo> /opt/service-health-api   # on the VM, or copy it there
ansible-playbook -i ansible/inventory.ini.example ansible/playbook.yml
curl http://<VM_PUBLIC_IP>:8000/health
terraform destroy   # when finished — do not leave the VM running
```

**Cost warning:** Standard_B1s is eligible for the Azure free-tier allowance
(750 hours/month for the first 12 months of a new account), but a public IP
and disk still count toward your subscription. Always run
`terraform destroy` when you are done, and check the Azure cost view before
applying. No paid resource is created by CI or by cloning this repo.

## Security

- SSH only from the CIDR you pass in (`allowed_ssh_cidr`); key-only login,
  no password auth.
- NSG opens only ports 22 (your IP only) and 8000 (the app).
- No secrets in git: SSH keys and Azure credentials are variables/inputs,
  never committed. CI scans the tree with Trivy (HIGH/CRITICAL, unfixed
  ignored) and fails on findings.
- The app stores nothing on disk and holds no credentials.

## Testing

- `tests/test_main.py`: root, health, create/get, list, 404, delete,
  validation (422), metrics — run with `python -m pytest tests/ -q`.
- CI additionally runs Trivy, `terraform fmt -check` + `validate`, an
  Ansible syntax check, and a Docker image build (push disabled).

## Limitations (honest)

- The registry is in-memory: a container restart clears it. For real use,
  add a database (PostgreSQL or Azure Cosmos DB) behind the API.
- HTTP only — add a reverse proxy with TLS (Caddy/Nginx + Let's Encrypt)
  before exposing this beyond a demo.
- Single VM, no load balancer, no auto-scaling — that is the point of this
  project: the cheapest honest deployment, not a production topology.
