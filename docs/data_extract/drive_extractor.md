# Data Extractor Stage

**Files:**
* **Executor:** [`run_extract.py`](../../data_extract/run_extract.py)
* **Logic:** [`extract_logic.py`](../../data_extract/shared/extract_logic.py)
* **Utilities:** [`utils.py`](../../data_extract/shared/utils.py)

**Role:** Source Ingestion and Storage Mirroring.

## System Contract

**Purpose**

Automates the transfer of source data from Google Drive to Google Cloud Storage (GCS). It preserves raw inputs in an archival zone and provides a trigger-point for the downstream data pipeline.

**Invariants**
* **Idempotency:** Each source folder is processed once. Re-execution is prevented by checking for a `.success` marker in the archival bucket.
* **Storage Mirroring:** Extracted files are written to both the **Archival Bucket** and the **Pipeline Bucket** for a transfer to be considered successful.
* **Access Scoping:** The extractor only operates on subfolders within the defined `PARENT_FOLDER`. It cannot access files outside this scope.
* **Metadata Logging:** Each extraction run generates a unique `execution_id` and a JSON manifest documenting file names, timestamps, and status.

**Inputs**
* `target_child_folder`: Identifier of the folder to ingest.
* **Drive Service Account**: Credentials with read-access to the source folder.

**Outputs**
* **Archival Artifacts:** Mirror of source files in the archival bucket.
* **Pipeline Artifacts:** Mirror of source files in the pipeline's raw landing zone.
* **Success Marker:** An empty `.success` file used for idempotency.
* **Extraction Log:** JSON metadata file summarizing the run.

## Execution Workflow

The extractor manages the ingestion lifecycle through these steps:

1.  **Duplicate Check:** Queries GCS for the success marker. If present, the job terminates with a "Skipped" status.
2.  **Path Resolution:** Uses the Drive API to locate the target folder ID and verifies its parent root.
3.  **File Discovery:** Lists files in the target folder, filtering out non-data files.
4.  **Extraction Loop:** For each file:
    * Downloads content from Google Drive to memory.
    * Uploads content to the archival and pipeline buckets.
5.  **Logging:** Generates and uploads the run metadata log.
6.  **Finalization:** Writes the `.success` file to GCS after all files are successfully processed.

## Boundaries

| This component | This component does NOT |
| :--- | :--- |
| Extracts files from Google Drive to GCS. | Modify or delete files in the source Drive. |
| Mirrors files across separate buckets. | Validate internal schemas or data quality. |
| Enforces folder-level idempotency. | Rename or transform file content. |
| Logs file transfer results. | Trigger the main pipeline directly. |
| Filters non-data files. | Handle multi-part Drive uploads. |

## Failure & Severity Model

### System Failures
* **Resolution Failure:** If folders cannot be identified, the orchestrator returns an error code.
* **API/Auth Failure:** If credentials fail, the process stops without writing a success marker, allowing for retries.

### Data Findings
* **Partial Extraction:** If any file in a batch fails to upload, the entire batch is marked as failed. The success marker is not written to ensure the entire folder is re-processed.
* **Empty Source:** If no valid data files are found, the extractor logs a warning and returns an error code to prevent triggering downstream processes.
