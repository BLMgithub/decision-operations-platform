# =============================================================================
# UNIT TESTS FOR loader_exporter.py
# =============================================================================

import pandas as pd
import pytest
from data_pipeline.shared.loader_exporter import (
    load_single_delta,
    load_historical_table,
    export_file,
)


# ------------------------------------------------------------
# FIXTURES (SHARED TEST DATA)
# ------------------------------------------------------------


@pytest.fixture
def sample_df():
    return pd.DataFrame({"a": [1, 2], "b": [3, 4]})


# ------------------------------------------------------------
# LOAD SINGLE DELTA
# ------------------------------------------------------------


def test_load_single_delta_success(tmp_path, sample_df):
    # Setup: Create multiple files with different dates
    sample_df.to_csv(tmp_path / "df_test_2023_01_01.csv", index=False)

    newer_df = pd.DataFrame({"a": [10], "b": [20]})
    newer_df.to_parquet(tmp_path / "df_test_2023_01_02.parquet", index=False)

    log_messages = []

    def logger(msg):
        log_messages.append(msg)

    df, file_name = load_single_delta(tmp_path, "df_test", log_info=logger)

    # Should pick the latest one (alphabetically/chronologically sorted)
    assert file_name == "df_test_2023_01_02"
    assert len(df) == 1
    assert df["a"].iloc[0] == 10
    assert any("Loaded: df_test_2023_01_02.parquet" in msg for msg in log_messages)


def test_load_single_delta_no_files(tmp_path):
    with pytest.raises(FileNotFoundError, match="No file found for df_missing"):
        load_single_delta(tmp_path, "df_missing")


# ------------------------------------------------------------
# LOAD HISTORICAL TABLE
# ------------------------------------------------------------


def test_load_historical_table_success(tmp_path):
    # Setup: Create multiple parquet files
    df1 = pd.DataFrame({"id": [1], "val": ["a"]})
    df2 = pd.DataFrame({"id": [2], "val": ["b"]})

    df1.to_parquet(tmp_path / "table_2023_01_01.parquet")
    df2.to_parquet(tmp_path / "table_2023_01_02.parquet")

    log_messages = []

    def logger(msg):
        log_messages.append(msg)

    df_total = load_historical_table(tmp_path, "table", log_info=logger)

    assert len(df_total) == 2
    assert set(df_total["id"]) == {1, 2}
    assert any("Loaded unified: table (2 rows)" in msg for msg in log_messages)


def test_load_historical_table_no_files(tmp_path):
    with pytest.raises(
        FileNotFoundError, match="No Parquet files found for table_missing"
    ):
        load_historical_table(tmp_path, "table_missing")


# ------------------------------------------------------------
# EXPORT FILE
# ------------------------------------------------------------


def test_export_file_parquet_success(tmp_path, sample_df):
    output_path = tmp_path / "output" / "data.parquet"

    log_messages = []

    def logger(msg):
        log_messages.append(msg)

    success = export_file(sample_df, output_path, log_info=logger)

    assert success is True
    assert output_path.exists()
    assert any("Exported .parquet file: data.parquet" in msg for msg in log_messages)

    # Verify content
    read_df = pd.read_parquet(output_path)
    pd.testing.assert_frame_equal(read_df, sample_df)


def test_export_file_csv_success(tmp_path, sample_df):
    output_path = tmp_path / "data.csv"
    success = export_file(sample_df, output_path)
    assert success is True
    assert output_path.exists()


def test_export_file_unsupported_extension(tmp_path, sample_df):
    output_path = tmp_path / "data.txt"

    error_messages = []

    def error_logger(msg):
        error_messages.append(msg)

    success = export_file(sample_df, output_path, log_error=error_logger)

    assert success is False
    assert not output_path.exists()
    assert any("Unsupported file extension" in msg for msg in error_messages)


def test_export_file_handles_io_error(tmp_path, sample_df, monkeypatch):
    # Try to write to a path that is actually a directory
    bad_path = tmp_path / "is_a_dir.parquet"
    bad_path.mkdir()

    error_messages = []

    def error_logger(msg):
        error_messages.append(msg)

    # In some OS/Python versions this might raise different things,
    # but export_file catches Exception and returns False.
    success = export_file(sample_df, bad_path, log_error=error_logger)

    assert success is False
    assert any("Failed to export file" in msg for msg in error_messages)
