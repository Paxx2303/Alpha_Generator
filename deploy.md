# Deploy Guide — Alpha Generator v3

**GCP Project:** `project-d9243352-39fe-44a5-90d`  
**Project Number:** `939562981836`  
**Service Account:** `deploy-sa@project-d9243352-39fe-44a5-90d.iam.gserviceaccount.com`  
**GitHub Repo:** `Paxx2303/Alpha_Generator`

---

## Kiến trúc Deploy

```
git push main
  └─ GitHub Actions
       ├─ Job 1: Build Dockerfile.observation → gcr.io → Cloud Run (alpha-observation)
       └─ Job 2: SSH IAP → alpha-vm → git pull → docker compose up  [khi VM_READY=true]
```

---

## GCP Setup (chạy 1 lần trong Cloud Shell)

### 1. Enable APIs
```bash
gcloud services enable \
  artifactregistry.googleapis.com \
  run.googleapis.com \
  compute.googleapis.com \
  iam.googleapis.com \
  iamcredentials.googleapis.com \
  --project=project-d9243352-39fe-44a5-90d
```

### 2. Tạo WIF Pool + Provider
```bash
PROJECT_ID="project-d9243352-39fe-44a5-90d"
PROJECT_NUMBER="939562981836"
REPO="Paxx2303/Alpha_Generator"

gcloud iam workload-identity-pools create my-global-pool \
  --location=global --project=$PROJECT_ID

gcloud iam workload-identity-pools providers create-oidc my-github-provider \
  --workload-identity-pool=my-global-pool \
  --location=global \
  --issuer-uri=https://token.actions.githubusercontent.com \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository == '${REPO}'" \
  --project=$PROJECT_ID
```

### 3. Tạo Service Account + Grant Roles
```bash
SA="deploy-sa@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud iam service-accounts create deploy-sa \
  --display-name="GitHub Actions Deploy SA" \
  --project=$PROJECT_ID

# Project-level roles
gcloud projects add-iam-policy-binding $PROJECT_ID --role="roles/artifactregistry.writer" --member="serviceAccount:$SA"
gcloud projects add-iam-policy-binding $PROJECT_ID --role="roles/run.admin"               --member="serviceAccount:$SA"
gcloud projects add-iam-policy-binding $PROJECT_ID --role="roles/compute.admin"            --member="serviceAccount:$SA"

# SA-level roles
gcloud iam service-accounts add-iam-policy-binding $SA --role="roles/iam.serviceAccountUser"   --member="serviceAccount:$SA" --project=$PROJECT_ID
gcloud iam service-accounts add-iam-policy-binding $SA --role="roles/iam.workloadIdentityUser" --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/my-global-pool/attribute.repository/${REPO}" --project=$PROJECT_ID
```

### 4. Lấy giá trị để set GitHub Secrets
```bash
# GCP_WORKLOAD_IDENTITY_PROVIDER
gcloud iam workload-identity-pools providers describe my-github-provider \
  --workload-identity-pool=my-global-pool \
  --location=global \
  --project=$PROJECT_ID \
  --format="value(name)"

# GCP_SERVICE_ACCOUNT  → deploy-sa@project-d9243352-39fe-44a5-90d.iam.gserviceaccount.com
# GCP_PROJECT_ID       → project-d9243352-39fe-44a5-90d
```

---

## GitHub Secrets (Settings → Secrets → Actions)

| Secret | Value |
|---|---|
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | `projects/939562981836/locations/global/workloadIdentityPools/my-global-pool/providers/my-github-provider` |
| `GCP_SERVICE_ACCOUNT` | `deploy-sa@project-d9243352-39fe-44a5-90d.iam.gserviceaccount.com` |
| `GCP_PROJECT_ID` | `project-d9243352-39fe-44a5-90d` |

---

## Bug History & Fixes

| Run | Bước fail | Root cause | Fix |
|---|---|---|---|
| #1 | Build & push | Artifact Registry API chưa enable | `gcloud services enable artifactregistry.googleapis.com` |
| #2 | Build & push | IAM chưa sync sau khi enable API | Re-trigger sau khi grant xong |
| #3 | Build & push | `roles/artifactregistry.writer` chưa grant | Grant role + add `gcc` vào Dockerfile |
| #4 | Build & push | `gcloud auth configure-docker` không reliable với WIF | Đổi sang `docker login` trực tiếp |
| #5–6 | Authenticate to GCP | `token_format: access_token` cần `serviceAccountTokenCreator` grant cho `principalSet` — phức tạp | **Bỏ `token_format`, dùng `gcloud auth print-access-token`** |

---

## Workflow Auth — Cách hoạt động hiện tại (Run #7+)

```yaml
- uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: ...   # WIF exchange → ADC credential file
    service_account: ...

- uses: google-github-actions/setup-gcloud@v2

- run: |
    gcloud auth print-access-token \   # gcloud dùng ADC → lấy access token
      | docker login -u oauth2accesstoken --password-stdin gcr.io
```

**Tại sao `gcloud auth print-access-token` thay vì `token_format: access_token`:**  
`token_format: access_token` yêu cầu grant `serviceAccountTokenCreator` cho `principalSet://...` (WIF identity). `gcloud auth print-access-token` dùng ADC credential file do WIF action tạo ra — không cần permission thêm.

---

## Checklist Deploy Status

### Done ✓
- [x] WIF pool + provider tạo thành công
- [x] `principalSet` binding (`workloadIdentityUser`) 
- [x] Artifact Registry API enabled
- [x] `roles/artifactregistry.writer` granted
- [x] `roles/run.admin` granted
- [x] `roles/iam.serviceAccountUser` granted
- [x] `roles/compute.admin` granted
- [x] `Dockerfile.observation` với `gcc`/`build-essential` cho chromadb
- [x] `.dockerignore` ở project root
- [x] GitHub secrets set (3 secrets)
- [x] Workflow fix: `gcloud auth print-access-token` (run #7)

### Pending
- [ ] **Run #7: First successful Cloud Run deploy**
- [ ] Tạo VM `alpha-vm` + chạy `deploy/vm-setup.sh`
- [ ] Set GitHub var `VM_READY=true`
- [ ] GLM-5.2 Cloud Run GPU (cần GPU quota)
- [ ] GCS backup bucket

---

## Tạo VM (sau khi Cloud Run OK)

```bash
gcloud compute instances create alpha-vm \
  --project=project-d9243352-39fe-44a5-90d \
  --zone=us-central1-a \
  --machine-type=e2-standard-4 \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB \
  --scopes=cloud-platform

# Chạy setup script
gcloud compute ssh alpha-vm --zone=us-central1-a \
  -- 'bash -s' < deploy/vm-setup.sh
```

---

## Trigger Deploy Thủ Công

```bash
# Push commit rỗng để trigger Actions
git commit --allow-empty -m "ci: retrigger deploy" && git push origin main

# Hoặc re-run failed workflow trên GitHub Actions UI
```
