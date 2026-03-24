# =============================================================================
# RAW DATA LOADER AND EXPORTER
# =============================================================================

from pathlib import Path
import pandas as pd
from typing import Optional, Callable, Tuple


FILE_LOADERS = {
    ".csv": lambda path: pd.read_csv(path),
    ".parquet": lambda path: pd.read_parquet(path, engine="pyarrow"),
}


def load_single_delta(
    base_path: Path | str,
    table_name: str,
    log_info: Optional[Callable[[str], None]] = None,
) -> Tuple[pd.DataFrame, str]:
    """
    Loads the MOST RECENT delta file for a specific logical table.
    Relies on YYYY_MM_DD suffix for chronological sorting.
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

    if log_info:
        log_info(f"Loaded: {target_file.name} ({len(df)} rows)")

    return df, file_name


def load_historical_table(
    base_path: Path | str,
    table_name: str,
    log_info: Optional[Callable[[str], None]] = None,
) -> pd.DataFrame:
    """
    Loads and concatenates ALL Parquet files for a logical table.
    """
    base_path = Path(base_path)

    files = [
        f
        for f in base_path.iterdir()
        if f.is_file()
        and (f.stem == table_name or f.name.startswith(f"{table_name}_"))
        and f.suffix.lower() == ".parquet"
    ]

    if not files:
        raise FileNotFoundError(f"No historical Parquet files found for {table_name}")

    dfs = []

    for file_path in sorted(files):
        df = pd.read_parquet(file_path, engine="pyarrow")
        dfs.append(df)

        if log_info:
            log_info(f"Assembling: {file_path.name} ({len(df)} rows)")

    return pd.concat(dfs, ignore_index=True)


##

# def load_logical_table(
#     base_path: Path | str,
#     table_name: str,
#     log_info: Optional[Callable[[str], None]] = None,
#     log_error: Optional[Callable[[str], None]] = None,
# ) -> Tuple[pd.DataFrame, str]:
#     """
#     Load and concatenate all CSV/Parquet files belonging to a logical table.

#     Files are identified by filename prefix: <table_name>*.csv or <table_name>*.parquet

#     Returns:
#     - Concatinated Dataframes
#     - File name
#     """

#     base_path = Path(base_path)

#     # List valid files and check format with FILE_LOADERS
#     files = [
#         f
#         for f in base_path.iterdir()
#         if f.is_file()
#         and (f.stem == table_name or f.name.startswith(f"{table_name}_"))
#         and f.suffix.lower() in FILE_LOADERS
#     ]

#     if not files:
#         if log_error:
#             log_error(f"{table_name}: no files found in {base_path}")

#         raise FileNotFoundError(f"No files found for {table_name}")

#     # Prevent mixed file formats
#     extensions = {f.suffix.lower() for f in files}
#     if len(extensions) > 1:
#         if log_error:
#             log_error(f"Mixed file formats detected for {table_name}")

#         raise RuntimeError("Mixed or incorrect file format")

#     dfs = []
#     files = sorted(files)
#     file_name = None

#     # Route each file using it's format to its registered loader
#     for file_path in files:

#         file_name = file_path.stem
#         loader = FILE_LOADERS[file_path.suffix.lower()]

#         try:
#             df = loader(file_path)

#             if log_info:
#                 log_info(f"Loaded: {file_path.name} ({len(df)} rows)")

#             dfs.append(df)

#         except Exception as e:
#             if log_error:
#                 log_error(f"Failed loading: {file_path.name}: {e}")

#     if not dfs:
#         if log_error:
#             log_error(f"{table_name}: all matching files failed to load")

#         raise RuntimeError(f"Failed to load {table_name}")

#     return pd.concat(dfs, ignore_index=True), file_name


def export_file(
    df: pd.DataFrame,
    output_path: Path,
    log_info: Optional[Callable[[str], None]] = None,
    log_error: Optional[Callable[[str], None]] = None,
    index: bool = False,
) -> bool:
    """
    Export DataFrame based on file extension (.csv or .parquet).

    Returns True if successful, False otherwise.

    """
    output_path = Path(output_path)

    try:
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        ext = output_path.suffix.lower()

        if ext == ".csv":
            df.to_csv(output_path, index=index)

        elif ext == ".parquet":
            df.to_parquet(output_path, index=index, engine="pyarrow")

        else:
            raise ValueError(
                f'Unsupported file extension: "{ext}". ' "Supported: .csv, .parquet"
            )

        if log_info:
            log_info(
                f"Exported {ext} file: " f"{output_path.name} " f"({len(df)} rows)"
            )

        return True

    except Exception as e:
        if log_error:
            log_error(f"Failed to export file {output_path}: {e}")

        return False
