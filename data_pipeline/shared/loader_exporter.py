# =============================================================================
# RAW DATA LOADER AND EXPORTER
# =============================================================================

from pathlib import Path
import polars as pl
from typing import Optional, Callable, Tuple, Any


def normalize_datetimes(lf: pl.LazyFrame) -> pl.LazyFrame:
    """
    Standardizes all Datetime columns to a unified resolution (microseconds).

    Contract:
    - Discovery: Scans the LazyFrame schema for all pl.Datetime fields.
    - Transformation: Forcefully casts identified columns to 'us' (microseconds) resolution.

    Invariants:
    - Zero-Failure: Returns the input 'lf' unchanged if no Datetime columns are found.
    - Environment Neutrality: Prevents 'Datetime(ns) != Datetime(us)' resolution mismatches
      between local development and cloud production environments.

    Outputs:
    - LazyFrame with resolution-standardized temporal fields.
    """

    schema = lf.collect_schema()
    datetime_cols = [
        col for col, dtype in schema.items() if isinstance(dtype, pl.Datetime)
    ]
    if not datetime_cols:
        return lf

    return lf.with_columns([pl.col(c).dt.cast_time_unit("us") for c in datetime_cols])


FILE_LOADERS = {
    ".csv": lambda path: pl.read_csv(path),
    ".parquet": lambda path: pl.read_parquet(path),
}


def load_single_delta(
    base_path: Path | str,
    table_name: str,
    log_info: Optional[Callable[[str], None]] = None,
) -> Tuple[Any, str]:
    """
    Loads the chronologically most recent delta for a logical table.

    Contract:
    - Discovery: Scans 'base_path' for files matching the 'table_name' prefix.
    - Selection: Identifies the target file via alphanumeric sorting of the date suffix (YYYY_MM_DD).
    - Normalization: Automatically applies 'normalize_datetimes' to enforce microsecond resolution.

    Invariants:
    - Recency: Only the latest snapshot is returned; historical deltas are ignored.
    - Format Support: Handles .csv and .parquet (prioritizing Parquet).
    - Source Integrity: Operates on a lazy scan to minimize memory footprint during initial load.

    Outputs:
    - Tuple containing (pl.DataFrame, str: file_name).

    Failures:
    - [Operational] Raises FileNotFoundError if no matching artifacts are found.
    """

    base_path = Path(base_path)

    # Find files matching the table prefix
    files = [
        file
        for file in base_path.iterdir()
        if file.is_file()
        and (file.stem == table_name or file.name.startswith(f"{table_name}_"))
        and file.suffix.lower() in FILE_LOADERS
    ]

    if not files:
        raise FileNotFoundError(f" No file found for {table_name} in {base_path}")

    # Read only recent date suffix
    files = sorted(files)
    target_file = files[-1]

    file_name = target_file.stem
    loader = FILE_LOADERS[target_file.suffix.lower()]

    df = loader(target_file)
    df = normalize_datetimes(df.lazy()).collect()

    if log_info:
        log_info(f"Loaded: {target_file.name} ({len(df)} rows)")

    return df, file_name


def load_historical_table(
    base_path: Path | str,
    table_name: str,
    log_info: Optional[Callable[[str], None]] = None,
) -> pl.LazyFrame:
    """
    Aggregates matching artifacts into a single cumulative LazyFrame.

    Contract:
    - Heterogeneous Scan Fix: Scans and normalizes resolution for every file individually before concatenation.
    - Discovery: Performs a multi-file scan of all Parquet artifacts matching 'table_name'.

    Optimization Logic:
    - Normalize-at-Source Strategy: Standardizes Datetime resolution at the point of ingestion to prevent
      downstream merge crashes caused by mixed local/cloud environments.

    Invariants:
    - Schema Stability: Returns a unified LazyFrame ready for streaming evaluation.

    Outputs:
    - Returns a pl.LazyFrame ready for downstream transformations.

    Failures:
    - [Operational] Raises FileNotFoundError if no Parquet files match the table name.
    """
    base_path = Path(base_path)

    files = [str(f) for f in base_path.glob(f"{table_name}*.parquet")]

    if not files:
        raise FileNotFoundError(f"No Parquet files found for {table_name}")

    # Scan and normalize each file individually before concatenating
    # This prevents 'incoming Datetime(ns) != target Datetime(us)' errors
    # when historical files have mixed resolutions due to different environments.
    lfs = []
    for f in files:
        lf = pl.scan_parquet(f)
        lf = normalize_datetimes(lf)
        lfs.append(lf)

    lf_unified = pl.concat(lfs)

    if log_info:
        log_info(
            f"Scanned: {table_name} ({len(files)} files queued for lazy evaluation)"
        )

    return lf_unified


def export_file(
    df: Any,
    output_path: Path,
    log_info: Optional[Callable[[str], None]] = None,
    log_error: Optional[Callable[[str], None]] = None,
    index: bool = False,
) -> bool:
    """
    Persists DataFrames or LazyFrames to disk using standardized formats.

    Contract:
    - Hydrate: Automatically ensures parent directories for 'output_path' exist.
    - Persist: Enforces Parquet with compression as the internal standard.

    Optimization Logic:
    - Streaming Sink: If 'df' is a LazyFrame, uses 'sink_parquet()' to execute 
      non-blocking writes directly from the query plan to disk.

    Invariants:
    - Compression: Utilizes 'brotli' for DataFrames and 'snappy' for LazyFrame streaming sinks.

    Outputs:
    - Boolean: True if write succeeded, False on I/O exception.

    Failures:
    - [Operational] Returns False and logs to 'log_error' if disk I/O fails or permissions are denied.
    """

    output_path = Path(output_path)

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        row_count = 0

        if isinstance(df, pl.DataFrame):
            df.write_parquet(output_path, compression="brotli")
            row_count = len(df)

        elif isinstance(df, pl.LazyFrame):
            df.sink_parquet(output_path, compression="snappy")
            row_count = "streaming"

        else:
            raise TypeError(f"Unsupported DataFrame type provided: {type(df)}")

        if log_info:
            log_info(f"Exported file: {output_path.name} ({row_count} rows)")

        return True

    except Exception as e:
        if log_error:
            log_error(f"Failed to export file {output_path}: {e}")

        return False
