# =============================================================================
# UUIDs to Integers Mappings Implementation
# =============================================================================

import polars as pl
from pathlib import Path
import shutil

ID_COLUMNS_TO_MAP = {
    "df_orders": ["order_id", "customer_id"],
    "df_customers": ["customer_id"],
    "df_order_items": ["order_id", "product_id", "seller_id"],
    "df_products": ["product_id"],
    "df_payments": ["order_id"],
}


def map_uuid_to_int(
    df: pl.DataFrame, mapping_file_path: Path, id_column: str
) -> pl.DataFrame:
    """
    Enforces a deterministic 1-to-1 mapping between UUID strings and UInt32 integers.

    Contract:
    - Hydrate: Loads existing mapping registry from Parquet if present.
    - Discover: Identifies new UUIDs in the input 'df' that are missing from the registry.
    - Generate: Assigns incrementing UInt32 values to new UUIDs, starting from max(existing_id) + 1.
    - Persist: Updates the mapping registry on disk immediately upon discovery of new keys.

    Invariants:
    - Referential Integrity: Guarantees that a UUID always maps to the same integer across runs.
    - Uniqueness: Enforces strict 1-to-1 parity between strings and integers.

    Outputs:
    - Joined DataFrame containing both the original 'id_column' and the new '{id_column}_int'.

    Failures:
    - [Operational] Crashes if the mapping file is corrupted or disk I/O fails.
    """

    int_col_name = f"{id_column}_int"

    if mapping_file_path.exists():
        mapping_df = pl.read_parquet(mapping_file_path)
        max_id = int(mapping_df.get_column(int_col_name).max() or 0)  # type: ignore

    else:
        mapping_df = pl.DataFrame(
            {id_column: [], int_col_name: []},
            schema={id_column: pl.String, int_col_name: pl.UInt32},
        )
        max_id = 0

    # The "anti" returns new UUIDs that are not yet in mapping_df
    unique_new_uuid = (
        df.select(id_column).unique().join(mapping_df, on=id_column, how="anti")
    )

    if unique_new_uuid.height > 0:
        start_val = max_id + 1

        new_mappings = unique_new_uuid.with_columns(
            pl.int_range(start_val, pl.len() + start_val, dtype=pl.UInt32).alias(
                int_col_name
            )
        )

        mapping_df = pl.concat([mapping_df, new_mappings])
        mapping_df.write_parquet(mapping_file_path)

    df_mapped = df.join(mapping_df, on=id_column, how="left")

    return df_mapped


def id_mapping(
    df: pl.DataFrame,
    table_name: str,
    mapping_dict: dict,
    source: Path,
    destination: Path,
) -> pl.DataFrame:
    """
    Orchestrates multi-column UUID-to-Integer transformation for a specific logical table.

    Contract:
    - Resolution: Identifies target ID columns (e.g., customer_id, order_id) based on 'mapping_dict'.
    - Isolation: Manages local temp paths vs. global storage paths for mapping registries.
    - Promotion: Synchronizes updated mapping files to the central storage destination.

    Optimization Logic:
    - Primitive Integer Pipeline: Converts high-cardinality strings to 4-byte integers to minimize downstream Hash Table memory.

    Invariants:
    - Traceability: All mapped files are promoted to 'destination' to ensure global consistency.

    Outputs:
    - DataFrame with all specified UUID columns supplemented by their integer counterparts.

    Failures:
    - [Structural] Skips mapping if the 'table_name' is not present in the 'mapping_dict'.
    """

    df_mapped = df
    cols_to_map = mapping_dict.get(table_name, [])

    for id_column in cols_to_map:
        mapping_filename = f"{id_column}_mapping.parquet"
        storage_path = destination / mapping_filename
        temp_path = source / mapping_filename

        # Check if mapping exists in storage else create
        if storage_path.exists():
            df_mapped = map_uuid_to_int(df_mapped, storage_path, id_column)
        else:
            source.mkdir(parents=True, exist_ok=True)
            df_mapped = map_uuid_to_int(df_mapped, temp_path, id_column)

    # Promote and overwrite mapping files in storage
    if source.exists():
        destination.mkdir(parents=True, exist_ok=True)
        for file in source.glob("*_mapping.parquet"):
            shutil.copy2(file, destination)

    return df_mapped
