# =============================================================================
# Google Cloud Storage path adapter
# =============================================================================

from data_pipeline.shared.run_context import RunContext
from pathlib import Path
from google.cloud import storage
import shutil


def _split_gcs_path(path: str):
    """
    Convert gs://bucket/path → (bucket, path)
    """

    path = path.replace("gs://", "")
    bucket, *rest = path.split("/", 1)
    prefix = rest[0] if rest else ""

    return bucket, prefix


def download_raw_snapshot(run_context: RunContext) -> None:
    """
    Download raw snapshot from storage to workspace.
    Supports local filesystem or GCS source.
    """

    source = run_context.storage_raw_path
    destination = run_context.raw_snapshot_path

    # Local filesystem case
    if not str(source).startswith("gs://"):
        shutil.copytree(source, destination, dirs_exist_ok=True)
        return

    # GCS case
    client = storage.Client()

    bucket_name, prefix = _split_gcs_path(source)

    bucket = client.bucket(bucket_name)

    for blob in bucket.list_blobs(prefix=prefix):
        if blob.name.endswith("/"):
            continue

        target = destination / Path(blob.name).name
        target.parent.mkdir(parents=True, exist_ok=True)

        blob.download_to_filename(target)


def upload_publish_artifacts(run_context: RunContext) -> None:
    """
    Upload semantic artifacts to storage publish directory.

    Uploads:
    - _latest.json
    - semantic directory

    Destination:
    version_path/v{run_id}/

    Supports local filesystem or GCS destination.
    """

    source = run_context.semantic_path
    destination = run_context.version_path

    # Local filesystem case
    if not str(destination).startswith("gs://"):
        shutil.copytree(source, destination)
        return

    # GCS case
    client = storage.Client()

    bucket_name, prefix = _split_gcs_path(destination)

    bucket = client.bucket(bucket_name)

    for file in source.rglob("*"):
        if file.is_file():
            blob = bucket.blob(f"{prefix}/{file.relative_to(source)}")
            blob.upload_from_filename(file)


def upload_run_artifacts(run_context: RunContext) -> None:
    """
    Persist run audit artifacts to storage.

    Uploads:
    - metadata.json
    - logs directory

    Destination:
    storage_runs_path/{run_id}/

    Supports local filesystem or GCS destination.
    """

    destination = run_context.storage_runs_path
    logs_path = run_context.logs_path
    metadata_path = run_context.metadata_path

    # Local storage case
    if not str(destination).startswith("gs://"):

        target = Path(destination)
        target.mkdir(parents=True, exist_ok=True)

        if metadata_path.exists():
            shutil.copy2(metadata_path, target / "metadata.json")

        if logs_path.exists():
            shutil.copytree(logs_path, target / "logs", dirs_exist_ok=True)

        return

    # GCS storage case
    client = storage.Client()

    bucket_name, prefix = _split_gcs_path(destination)
    bucket = client.bucket(bucket_name)

    # Upload metadata
    if metadata_path.exists():
        blob = bucket.blob(f"{prefix}/metadata.json")
        blob.upload_from_filename(metadata_path)

    # Upload logs
    if logs_path.exists():
        for file in logs_path.rglob("*"):
            if file.is_file():
                blob = bucket.blob(f"{prefix}/logs/{file.relative_to(logs_path)}")
                blob.upload_from_filename(file)


def upload_contracted_directory(run_context: RunContext) -> None:
    """
    Persist contracted datasets to storage.

    Uploads:
    - semantic directory

    Destination:
    storage_contracted_path/

    Supports local filesystem or GCS destination.
    """

    source = run_context.contracted_path
    destination = run_context.storage_contracted_path

    # Local filesystem case
    if not str(destination).startswith("gs://"):

        Path(destination).mkdir(parents=True, exist_ok=True)

        for file in source.iterdir():
            if file.is_file():
                target_file = f"{destination}/{file.name}"

                shutil.copyfile(file, target_file)

        return

    # GCS case
    client = storage.Client()

    bucket_name, prefix = _split_gcs_path(destination)
    bucket = client.bucket(bucket_name)

    for file in source.rglob("*"):
        if file.is_file():

            blob = bucket.blob(f"{prefix}/{file.relative_to(source)}")
            blob.upload_from_filename(file)


def download_contracted_datasets(run_context: RunContext) -> None:
    """
    Download contraced from storage to workspace.
    Supports local filesystem or GCS source.
    """

    source = run_context.storage_contracted_path
    destination = run_context.contracted_path

    # Local filesystem case
    if not str(source).startswith("gs://"):
        shutil.copytree(source, destination, dirs_exist_ok=True)
        return

    # GCS case
    client = storage.Client()

    bucket_name, prefix = _split_gcs_path(source)

    bucket = client.bucket(bucket_name)

    for blob in bucket.list_blobs(prefix=prefix):
        if blob.name.endswith("/"):
            continue

        target = destination / Path(blob.name).name
        target.parent.mkdir(parents=True, exist_ok=True)

        blob.download_to_filename(target)
