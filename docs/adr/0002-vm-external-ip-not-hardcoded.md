# VM external IP is resolved at deploy time, not hardcoded

The deploy workflow looks up `alpha-vm`'s current external IP with `gcloud compute instances describe` and injects it (`BETTER_AUTH_URL`, `VM_EXTERNAL_IP` → `DEER_FLOW_TRUSTED_ORIGINS`). Nothing in the repo hardcodes the IP. The IP itself is pinned by **reserving a static external IP** on GCP so it survives a VM stop/start.

## Context

The IP `34.81.142.38` was hardcoded in `deploy.yml` (`BETTER_AUTH_URL`) and `docker-compose.override.yml` (`DEER_FLOW_TRUSTED_ORIGINS`). When the VM was stopped and restarted it received a new ephemeral IP (`104.199.179.72`); the hardcoded value went stale, DeerFlow's auth origin no longer matched the real URL, and a deploy run failed because the VM was unreachable during the window. This is issue C1 from the system review.

## Decision

Two complementary changes:
1. **Dynamic injection** — deploy.yml resolves the live IP each run, so the config self-heals even if the IP changes. `docker-compose.override.yml` reads `${VM_EXTERNAL_IP}` via compose `--env-file` interpolation.
2. **Static reservation** — promote the in-use IP to a reserved static address so it stops changing at all:
   `gcloud compute addresses create alpha-vm-ip --addresses=<CURRENT_IP> --region=asia-east1`

## Consequences

- A stop/start no longer breaks auth or trusted origins.
- `BETTER_AUTH_SECRET` stays stable across deploys, so browser sessions survive — but only if the IP (hence `BETTER_AUTH_URL`) is also stable, which the static reservation guarantees.
- If the static IP is ever released, the dynamic lookup still prevents a hard break; it just may change the login URL.
