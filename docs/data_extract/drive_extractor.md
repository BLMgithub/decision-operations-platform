# **Data Extractor Stage**

**Files:**
* **Executor:** [`run_extract.py`](../../data_extract/run_extract.py)
* **Logic:** [`extract_logic.py`](../../data_extract/shared/extract_logic.py)
* **Utilities:** [`utils.py`](../../data_extract/shared/utils.py)

**Role:** Source Ingestion and Cloud Mirroring Gateway.

## **System Contract**

**Purpose**

Automates the secure transfer of source data from Google Drive to Google Cloud Storage (GCS). It ensures that raw inputs are preserved in an immutable archival zone while simultaneously providing a clean trigger-point for the downstream data pipeline.

**Invariants**
* **Folder-Level Deduplication:** Every source folder is processed exactly once. Re-execution is blocked by the existence of a `.success` marker in the archival bucket.
* **Dual-Mirroring Guarantee:** Every extracted file must be successfully written to both the **Archival Bucket** (compliance/audit) and the **Pipeline Bucket** (raw landing zone) before the extraction is considered successful.
* **Namespace Protection:** The extractor only operates on subfolders belonging to the strictly defined `PARENT_FOLDER`. It cannot "see" or extract files from the wider Drive environment.
* **Metadata Lineage:** Every extraction run generates a unique `execution_id` (UUID) and a JSON manifest documenting file names, timestamps, and status.

**Inputs**
* `target_child_folder`: `str` (The identifier of the operational batch to ingest).
* **Drive Service Account**: (Credentials with read-access to the `operations-upload-folder`).

**Outputs**
* **Archival Artifacts:** Mirror of source files in `gs://operations-archival-bucket/archive/{folder_name}/`.
* **Pipeline Artifacts:** Mirror of source files in `gs://operations-pipeline-bucket/raw/`.
* **Success Marker:** An empty `gs://.../{folder_name}.success` file used for idempotency.
* **Extraction Log:** A JSON metadata file summarizing the run.

## **Execution Workflow**

The **Extractor** manages the ingestion lifecycle through the following steps:

1.  **Deduplication Check:** Queries GCS for the success marker. If present, the job terminates immediately with a "Skipped" status.
2.  **Hierarchy Resolution:** Uses the Drive API to locate the `folder_id` of the target child, ensuring it resides strictly under the authorized parent root.
3.  **Manifest Fetching:** Retrieves a list of all files in the target folder, filtering out system-reserved files (e.g., `instruction.txt`).
4.  **Extraction Loop:** For each valid file:
    * Downloads the binary content from Google Drive into memory.
    * Uploads the content to the **Archival Bucket** (long-term persistence).
    * Uploads the content to the **Pipeline Bucket** (transient raw landing).
5.  **Audit Persistence:** Generates and uploads the run metadata log.
6.  **Marker Placement:** Upon 100% success of the file loop, writes the `.success` file to GCS.


## **Boundaries**

| This component **DOES** | This component **DOES NOT** |
| :--- | :--- |
| Extract files from Google Drive to GCS. | Modify or delete any files in the source Drive. |
| Mirror files across two separate administrative buckets. | Validate the internal schema or data quality of files. |
| Enforce folder-grain idempotency. | Rename or transform file content. |
| Log every file-level transfer result. | Trigger the main pipeline directly (Triggered via GCS events). |
| Filter out non-data files (instruction files). | Handle multi-part Drive uploads (expects completed files). |

## **Failure & Severity Model**

### **Operational Failures (System Level)**
* **Missing Hierarchy:** If the `PARENT_FOLDER` or `target_child_folder` cannot be resolved, the orchestrator returns `exit 1`.
* **API Throttling/Auth:** If Drive or GCS credentials fail, the process halts. No success marker is written, allowing for a clean retry.

### **Functional Findings (Data Level)**
* **Partial Extraction:** If a single file in a batch fails to upload to either bucket, the entire batch is marked as `failed`. The success marker is **not** written, ensuring that a subsequent run will attempt to re-process the *entire* folder.
* **Empty Source:** If the target folder contains no valid data files, the extractor logs a warning but terminates with `exit 1` (Failure) to prevent a "phantom" successful run from triggering downstream processes.