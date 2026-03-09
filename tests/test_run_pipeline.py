# =============================================================================
# UNIT TESTS FOR run_pipeline.py
# =============================================================================

from data_pipeline.shared.run_context import RunContext
from data_pipeline.run_pipeline import (
    main,
    download_raw_snapshot,
    initiliaze_metadata,
    finalize_metadata,
)
import pytest
import json


def test_snapshot_raw_storage_raises_when_source_missing(tmp_path):

    run_context = RunContext.create(
        base=tmp_path, storage=tmp_path, run_id="20230101T000000_abc123"
    )

    with pytest.raises(FileNotFoundError):
        download_raw_snapshot(run_context)


def test_metadata_helpers(tmp_path):
    run_context = RunContext.create(
        base=tmp_path, storage=tmp_path, run_id="20230101T000000_abc123"
    )

    # test status: RUNNING and published: False
    initiliaze_metadata(run_context)

    assert run_context.metadata_path.exists()
    with open(run_context.metadata_path) as f:
        payload = json.load(f)
    assert payload["status"] == "RUNNING"
    assert payload["published"] is False

    # test status: SUCCESS and published: True
    finalize_metadata(run_context, status="SUCCESS")

    with open(run_context.metadata_path) as f:
        payload = json.load(f)
    assert payload["status"] == "SUCCESS"
    assert payload["published"] is True


def test_main_fails_on_initial_validation(monkeypatch, tmp_path):

    run_context = RunContext.create(
        base=tmp_path, storage=tmp_path, run_id="20230101T000000_abc123"
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.download_raw_snapshot",
        lambda *_: None,
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.RunContext.create",
        lambda: run_context,
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.apply_validation",
        lambda *args, **kwargs: {
            "errors": ["boom"],  # force to fail on initial validation
            "warnings": [],
        },
    )

    with pytest.raises(RuntimeError):
        main()

    with open(run_context.metadata_path) as f:
        payload = json.load(f)
    assert payload["status"] == "FAILED"
    assert payload["published"] is False

    for logs in ("validation_initial.json",):
        assert (run_context.logs_path / logs).exists()


def test_main_fails_on_post_contract_validation(monkeypatch, tmp_path):

    run_context = RunContext.create(
        base=tmp_path, storage=tmp_path, run_id="20230101T000000_abc123"
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.download_raw_snapshot",
        lambda *_: None,
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.RunContext.create",
        lambda: run_context,
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.TABLE_CONFIG",
        {"dummy": {}},
    )

    # execution count
    calls = {"count": 0}

    def fake_validation(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            return {"errors": [], "warnings": []}
        return {
            "errors": [],
            "warnings": ["warn"],
        }  # force to pass on post contract validation

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.apply_validation",
        fake_validation,
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.apply_contract",
        lambda *a, **k: ({}, set()),
    )

    with pytest.raises(RuntimeError):
        main()

    with open(run_context.metadata_path) as f:
        payload = json.load(f)
    assert payload["status"] == "FAILED"
    assert payload["published"] is False

    for logs in (
        "validation_initial.json",
        "contract_report.json",
        "validation_post_contract.json",
    ):
        assert (run_context.logs_path / logs).exists()


def test_main_fails_on_assemble_events(monkeypatch, tmp_path):

    run_context = RunContext.create(
        base=tmp_path, storage=tmp_path, run_id="20230101T000000_abc123"
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.download_raw_snapshot",
        lambda *_: None,
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.RunContext.create",
        lambda: run_context,
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.TABLE_CONFIG",
        {"dummy": {}},
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.apply_validation",
        lambda *a, **k: {
            "errors": [],
            "warnings": [],
        },  # Pass all validations
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.apply_contract",
        lambda *a, **k: ({}, set()),
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.assemble_events",
        lambda *a, **k: {
            "status": "failed",
            "error": ["boom"],
            "info": [],
        },  # Force to fail on assemble events
    )

    with pytest.raises(RuntimeError):
        main()

    with open(run_context.metadata_path) as f:
        payload = json.load(f)
    assert payload["status"] == "FAILED"
    assert payload["published"] is False

    for logs in (
        "validation_initial.json",
        "contract_report.json",
        "validation_post_contract.json",
    ):
        assert (run_context.logs_path / logs).exists()


def test_main_fails_on_build_semantic_layer(monkeypatch, tmp_path):

    run_context = RunContext.create(
        base=tmp_path, storage=tmp_path, run_id="20230101T000000_abc123"
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.download_raw_snapshot",
        lambda *_: None,
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.RunContext.create",
        lambda: run_context,
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.TABLE_CONFIG",
        {"dummy": {}},
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.apply_validation",
        lambda *a, **k: {
            "errors": [],
            "warnings": [],
        },  # Pass all validations
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.apply_contract",
        lambda *a, **k: ({}, set()),
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.assemble_events",
        lambda *a, **k: {
            "status": "success",
            "error": [],
            "info": [],
        },  # Pass, status success
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.build_semantic_layer",
        lambda *a, **k: {
            "status": "failed",
            "error": ["boom"],
            "info": [],
        },  # Force to fail on build semantic layer
    )

    with pytest.raises(RuntimeError):
        main()

    with open(run_context.metadata_path) as f:
        payload = json.load(f)
    assert payload["status"] == "FAILED"
    assert payload["published"] is False

    for logs in (
        "validation_initial.json",
        "contract_report.json",
        "validation_post_contract.json",
        "assemble_report.json",
    ):
        assert (run_context.logs_path / logs).exists()


def test_main_fails_on_execute_publish_lifecycle(monkeypatch, tmp_path):

    run_context = RunContext.create(
        base=tmp_path, storage=tmp_path, run_id="20230101T000000_abc123"
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.download_raw_snapshot",
        lambda *_: None,
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.RunContext.create",
        lambda: run_context,
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.TABLE_CONFIG",
        {"dummy": {}},
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.apply_validation",
        lambda *a, **k: {
            "errors": [],
            "warnings": [],
        },  # Pass all validations
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.apply_contract",
        lambda *a, **k: ({}, set()),
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.assemble_events",
        lambda *a, **k: {
            "status": "success",
            "error": [],
            "info": [],
        },  # Pass, status success
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.build_semantic_layer",
        lambda *a, **k: {
            "status": "success",
            "error": [],
            "info": [],
        },  # Pass, status success
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.execute_publish_lifecycle",
        lambda *a, **k: {
            "status": "failed",
            "errors": ["boom"],
            "info": [],
        },  # Force to fail on publish lifecyle
    )

    with pytest.raises(RuntimeError):
        main()

    with open(run_context.metadata_path) as f:
        payload = json.load(f)
    assert payload["status"] == "FAILED"
    assert payload["published"] is False

    for logs in (
        "validation_initial.json",
        "contract_report.json",
        "validation_post_contract.json",
        "assemble_report.json",
        "semantic_report.json",
    ):
        assert (run_context.logs_path / logs).exists()


def test_main_success(monkeypatch, tmp_path):

    run_context = RunContext.create(
        base=tmp_path, storage=tmp_path, run_id="20230101T000000_abc123"
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.download_raw_snapshot",
        lambda *_: None,
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.RunContext.create",
        lambda: run_context,
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.TABLE_CONFIG",
        {"dummy": {}},
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.apply_validation",
        lambda *a, **k: {
            "errors": [],
            "warnings": [],
        },  # Pass all validations
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.apply_contract",
        lambda *a, **k: ({}, set()),
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.assemble_events",
        lambda *a, **k: {
            "status": "success",
            "error": [],
            "info": [],
        },  # Pass, status success
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.build_semantic_layer",
        lambda *a, **k: {
            "status": "success",
            "error": [],
            "info": [],
        },  # Pass, status success
    )

    monkeypatch.setattr(
        "data_pipeline.run_pipeline.execute_publish_lifecycle",
        lambda *a, **k: {
            "status": "success",
            "errors": [],
            "info": [],
        },  # Pass, status success
    )

    main()

    with open(run_context.metadata_path) as f:
        payload = json.load(f)
    assert payload["status"] == "SUCCESS"
    assert payload["published"] is True

    for logs in (
        "validation_initial.json",
        "contract_report.json",
        "validation_post_contract.json",
        "assemble_report.json",
        "semantic_report.json",
        "publish_report.json",
    ):
        assert (run_context.logs_path / logs).exists()


# =============================================================================
# UNIT TESTS END
# =============================================================================
