# GCP Infrastructure: Operations Analytics Pipeline

This repository contains the Terraform configuration for the Operations Analytics data pipeline. The infrastructure is serverless and event-driven, using Cloud Run, Workflows, and Eventarc.

## Architecture Overview
The pipeline follows this execution flow:
1.  **Extraction:** Cloud Scheduler triggers the `drive-extractor` Cloud Run job daily.
2.  **Archival:** The extractor saves raw data to the **Archival Bucket** (Coldline storage).
3.  **Dispatch:** An Eventarc trigger detects the new file and invokes a Google Workflow (`pipeline-dispatcher`).
4.  **Processing:** The Workflow triggers the main `operations-pipeline` Cloud Run job for data processing.
5.  **Transient Storage:** Intermediate files are stored in the **Pipeline Bucket** with a 7-day TTL on raw data.
6.  **Serving Layer:** Semantic models are published as **BigQuery External Tables** and accessed via **Authorized Views**.

## Prerequisites
*   **Terraform:** Version `~> 1.5.0`
*   **Provider:** `hashicorp/google` version `~> 7.0`
*   **Backend:** GCS bucket `operations-terraform-state-vault-2026` for state management.

## Post-Provisioning (CI/CD Setup)
Integrating GCP with GitHub Actions requires a bootstrap process to populate Repository Secrets and establish the trust relationship via Workload Identity Federation (WIF).

### Required GitHub Secrets
| GitHub Secret | Source | Purpose |
| :--- | :--- | :--- |
| `WIF_PROVIDER` | `terraform output -raw GITHUB_WIF_PROVIDER_NAME` | WIF identity provider path. |
| `DEPLOYER_SA_EMAIL` | `github-actions-deployer@...` | Identity for GitHub OIDC impersonation. |
| `GCP_PROJECT_ID` | `var.project_id` | GCP Project ID. |

### Provisioning Requirements
The initial infrastructure must be provisioned by a user with `Project IAM Admin` or `Owner` privileges to establish the WIF provider and assign roles to the `github-actions-deployer` service account. Subsequent updates are managed by the CI/CD pipeline.

## Infrastructure Components

### Compute & Jobs (`jobs.tf`)
| Resource Name | Type | Memory | Timeout | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `operations-pipeline` | Cloud Run Job | 8Gi | 30m | Processing engine. Includes 10Gi Local SSD mount at `/tmp`. |
| `drive-extractor` | Cloud Run Job | 1Gi | 15m | Pulls source data from external APIs. |
| `ops-repo` | Artifact Registry | n/a | n/a | Docker repository for pipeline images. |

### Storage & Lifecycle (`storage.tf`)
| Resource Name | Type | Policy / Details |
| :--- | :--- | :--- |
| `ops-archival-storage` | GCS Bucket | Move to Coldline after 400 days; Delete after 3 years. |
| `ops-pipeline-storage` | GCS Bucket | Delete files with prefix `raw/` after 7 days. |
| `seller_semantic` | BQ Dataset | Protected from destruction. |
| `customer_semantic` | BQ Dataset | Protected from destruction. |
| `product_semantic` | BQ Dataset | Protected from destruction. |

## Implementation Details

### Cloud Run Local SSD
The `operations-pipeline` uses a Local SSD mount at `/tmp` to offload memory pressure during joins.
*   **Constraint:** The Google Terraform provider does not natively support the `DISK` medium for `empty_dir` volumes (it defaults to `MEMORY`).
*   **Configuration:** Provision the SSD partition manually and use `ignore_changes` on the `medium` attribute in Terraform to prevent reversion to RAM-based storage.

### BigQuery Deletion Protection
To safeguard data, semantic datasets are configured with:
*   `delete_contents_on_destroy = false`: Ensures data and views persist if the resource is deleted.
*   `prevent_destroy = true`: Requires a manual override to destroy the dataset.

### Orchestration (`orchestration.tf`)
*   **Cloud Scheduler:** Triggers the Extractor daily at 12AM PHT.
*   **Eventarc:** Monitors `object.v1.finalized` events on the Archival bucket.
*   **Workflows:** `pipeline-dispatcher` triggers the main pipeline.

## IAM & Security (`iam_bindings.tf`, `wif.tf`)

This project uses Workload Identity Federation and granular Service Account permissions.

### Service Accounts
| Identity Name | Purpose |
| :--- | :--- |
| `github-actions-deployer` | CI/CD automation. |
| `drive-extractor-sa` | Data extraction and archival. |
| `ops-pipeline-sa` | Main processing pipeline. |
| `eventarc-invoker-sa` | Event routing and workflow triggers. |
| `job-invoker-sa` | Triggering Cloud Run jobs. |

### Permission Bindings
| Identity | Target | Roles | Rationale |
| :--- | :--- | :--- | :--- |
| **Github Deployer** | Project | `run.developer`, `workflows.editor`, `cloudscheduler.admin`, `artifactregistry.admin`, `eventarc.admin`, `storage.admin`, `resourcemanager.projectIamAdmin`, `iam.workloadIdentityPoolAdmin`, `monitoring.admin`, `iam.serviceAccountAdmin`, `iam.serviceAccountUser`, `iam.admin`, `logging.configWriter`, `bigquery.admin`| **Least Privilege:** Granular roles for managing the entire pipeline lifecycle, IAM bindings, state management, and BigQuery schemas. |
| **Drive Extractor** | Archival/Pipeline Buckets | `roles/storage.objectAdmin` | Full CRUD for data landing and archival. |
| **Ops Pipeline** | Pipeline Bucket | `roles/storage.objectAdmin` | Read raw data and write processed artifacts. |
| | Project | `roles/bigquery.dataEditor`, `roles/bigquery.jobUser` | Permission to create External Tables, swap Authorized Views, and execute queries. |
| **Event Invoker** | Project | `roles/eventarc.eventReceiver` | Receive GCS notifications. |
| | Project | `roles/workflows.invoker` | Permission to start workflow execution. |

### Workload Identity Federation
*   **Pool:** `github-pool`
*   **Trust Policy:** Restricted to `${var.github_repo}` to prevent unauthorized access.

## Inputs & Variables (`variables.tf`)
| Name | Type | Description |
| :--- | :--- | :--- |
| `project_id` | `string` | Target Google Cloud Project ID. |
| `region` | `string` | GCP region. |
| `environment` | `string` | Deployment environment (dev, prod). |
| `github_repo` | `string` | Format: `owner/repository`. |
| `bq_dataset_id` | `string` | BigQuery dataset ID. |
| `alert_email_map` | `map` | Monitoring notification recipients (Sensitive). |

## State Management
State is stored remotely in GCS.
```hcl
terraform {
  backend "gcs" {
    bucket = "operations-terraform-state-vault-2026"
    prefix = "terraform/state"
  }
}
```
