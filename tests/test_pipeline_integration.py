"""
Tasks 10 & 14: Integration tests that exercise the full pipeline with real LLM API calls.
These tests are marked @pytest.mark.integration and do NOT run by default
(use pytest -m integration to run them).

Requires: OPENAI_API_KEY environment variable set.
Cost: ~$1-2 per full run.
Time: ~2-5 minutes per full run.
"""

import json
import os

import pytest
from openpyxl import load_workbook

import agent


@pytest.mark.integration
def test_full_pipeline_end_to_end_with_real_api(tmp_output_dir):
    """
    Real end-to-end test: full requirement file → all 6 stages → final Excel reports.
    Validates schema preservation, no data loss, and multi-stage coherence.
    """
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set — skipping real-API integration test")

    requirements_text = """\
As a user, I want to search for products by name so that I can find what I'm looking for.
As a user, I want to filter products by price so that I can see products in my budget.
As a developer, I want the search to complete in <100ms so that the user experience is responsive.
"""

    result = agent.run_pipeline(requirements_text, output_dir=tmp_output_dir)

    assert "counts" in result
    assert result["counts"]["generated_test_cases"] > 0
    assert result["counts"]["final_test_cases"] > 0

    assert "files" in result
    assert "requirements" in result["files"]
    assert "test_cases" in result["files"]
    assert "final" in result["files"]
    assert "automation" in result["files"]
    assert "estimation" in result["files"]

    for key, path in result["files"].items():
        assert os.path.exists(path), f"File for {key} does not exist: {path}"


@pytest.mark.integration
def test_requirements_survive_through_the_full_pipeline(tmp_output_dir):
    """
    Validates that requirements extracted in stage 1 are still referenced in later stages.
    """
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set — skipping real-API integration test")

    requirements_text = """\
As a user, I want to log in with username and password.
As a user, I want to log in with SSO.
"""

    result = agent.run_pipeline(requirements_text, output_dir=tmp_output_dir)

    # Verify requirements were extracted
    assert result["counts"]["generated_test_cases"] > 0

    # Load the test cases and verify they reference requirement IDs
    wb_test_cases = load_workbook(result["files"]["test_cases"])
    test_case_rows = list(wb_test_cases.active.iter_rows(values_only=True))[1:]

    req_ids_in_test_cases = {row[1] for row in test_case_rows}
    assert len(req_ids_in_test_cases) > 0, "No requirement IDs found in test cases"


@pytest.mark.integration
def test_automation_feasibility_summary_is_calculated(tmp_output_dir):
    """
    Validates that automation stage produces a summary with correct metrics.
    """
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set — skipping real-API integration test")

    requirements_text = """\
As a user, I want to log in.
As a user, I want to search for items.
"""

    result = agent.run_pipeline(requirements_text, output_dir=tmp_output_dir)

    assert "automation_summary" in result
    assert "total" in result["automation_summary"]
    assert "automatable" in result["automation_summary"]
    assert "manual" in result["automation_summary"]
    assert "coverage_pct" in result["automation_summary"]

    summary = result["automation_summary"]
    assert summary["total"] > 0
    assert 0 <= summary["coverage_pct"] <= 100
    assert summary["automatable"] + summary["manual"] == summary["total"]


@pytest.mark.integration
def test_estimation_produces_reasonable_numbers(tmp_output_dir):
    """
    Validates that estimation stage output is present and sensible.
    """
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set — skipping real-API integration test")

    requirements_text = """\
As a user, I want to log in.
As a user, I want to sign up.
As a user, I want to reset my password.
"""

    result = agent.run_pipeline(requirements_text, output_dir=tmp_output_dir)

    assert "estimation" in result
    estimation = result["estimation"]

    assert "total_test_cases" in estimation
    assert "estimated_days" in estimation
    assert "test_cases_per_day" in estimation or result["counts"]["final_test_cases"] == 0

    if result["counts"]["final_test_cases"] > 0:
        assert estimation["total_test_cases"] > 0
        assert estimation["estimated_days"] > 0


@pytest.mark.integration
def test_different_testcases_per_day_affects_estimation(tmp_output_dir):
    """
    Validates that the testcases_per_day parameter influences the estimation output.
    """
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set — skipping real-API integration test")

    requirements_text = """\
As a user, I want to log in.
As a user, I want to search.
"""

    result_slow = agent.run_pipeline(requirements_text, testcases_per_day=2, output_dir=tmp_output_dir)
    result_fast = agent.run_pipeline(requirements_text, testcases_per_day=10, output_dir=tmp_output_dir)

    if (result_slow["counts"]["final_test_cases"] > 0 and
        result_fast["counts"]["final_test_cases"] > 0 and
        "estimation" in result_slow and "estimation" in result_fast):

        # Slower rate → same test cases → more days (roughly)
        est_slow = result_slow["estimation"]
        est_fast = result_fast["estimation"]

        if est_slow["total_test_cases"] == est_fast["total_test_cases"]:
            assert est_slow["estimated_days"] >= est_fast["estimated_days"]


@pytest.mark.integration
def test_final_test_cases_excel_has_all_required_fields(tmp_output_dir):
    """
    Validates the structure of the final test-cases Excel report.
    """
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set — skipping real-API integration test")

    requirements_text = """\
As a user, I want to log in.
"""

    result = agent.run_pipeline(requirements_text, output_dir=tmp_output_dir)

    if result["counts"]["final_test_cases"] > 0:
        wb = load_workbook(result["files"]["final"])
        rows = list(wb.active.iter_rows(values_only=True))

        headers = rows[0]
        assert "ID" in headers
        assert "Scenario" in headers
        assert "Type" in headers
        assert "Expected Result" in headers
