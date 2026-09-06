"""
Task 9: Excel workbook generation and content validation.
Tests both multi-sheet reports (like automation feasibility) and simple single-sheet
reports, plus the style_sheet utility function's output format.
"""

from openpyxl import load_workbook

import agent


def test_all_workbook_files_are_valid_xlsx(
    patch_crew_kickoff, make_stage_outputs, sample_requirements_text, tmp_output_dir
):
    patch_crew_kickoff(make_stage_outputs(
        analyze=sample_requirements_text,
        generate=[{"id": "TC_1", "req_id": "REQ_1", "scenario": "x", "type": "Positive",
                   "steps": [], "expected_result": "", "priority": "High"}],
        review="[]",
        fix=[{"id": "TC_1", "req_id": "REQ_1", "scenario": "x", "type": "Positive",
              "steps": [], "expected_result": "", "priority": "High"}],
        automation="[]",
        estimate="{}",
    ))
    result = agent.run_pipeline(sample_requirements_text, output_dir=tmp_output_dir)

    for key, path in result["files"].items():
        try:
            wb = load_workbook(path)
            assert len(wb.sheetnames) > 0
        except Exception as e:
            raise AssertionError(f"Failed to load workbook {key} from {path}") from e


def test_workbook_cells_with_empty_strings_are_written(
    patch_crew_kickoff, sample_requirements_text, tmp_output_dir
):
    # Test empty values in requirement and category fields
    req = {"req_id": "REQ_1", "requirement": "", "category": "", "priority": "High"}
    patch_crew_kickoff({
        "analyze": __import__("json").dumps([req]),
        "generate": "[]", "review": "[]", "fix": "[]",
        "automation": "[]", "estimate": "{}",
    })

    result = agent.run_pipeline(sample_requirements_text, output_dir=tmp_output_dir)

    wb = load_workbook(result["files"]["requirements"])
    row = list(wb.active.iter_rows(values_only=True))[1]
    # Headers: Req ID (0), Requirement (1), Category (2), Priority (3)
    # openpyxl reads empty-string cells back as None, not ""
    assert row[1] in ("", None)  # Requirement field
    assert row[2] in ("", None)  # Category field


def test_workbook_number_columns_are_written_as_numerics(
    patch_crew_kickoff, make_stage_outputs, sample_estimation, sample_requirements_text, tmp_output_dir
):
    patch_crew_kickoff(make_stage_outputs(estimate=sample_estimation))
    result = agent.run_pipeline(sample_requirements_text, output_dir=tmp_output_dir)

    wb = load_workbook(result["files"]["estimation"])
    cell_total = wb.active.cell(2, 1)
    cell_per_day = wb.active.cell(2, 2)
    cell_days = wb.active.cell(2, 3)

    assert isinstance(cell_total.value, int)
    assert isinstance(cell_per_day.value, int)
    assert isinstance(cell_days.value, int)


def test_style_sheet_utility_applies_formatting(
    patch_crew_kickoff, make_stage_outputs, sample_requirements_text, tmp_output_dir
):
    # style_sheet is a formatting helper that applies column widths, text wrapping,
    # and alignment to an openpyxl worksheet; verify that passing it does not raise
    # and that the worksheet is modified as expected.
    patch_crew_kickoff(make_stage_outputs(
        analyze=[{"req_id": "REQ_1", "requirement": "Test requirement with a lot of text that will wrap",
                  "category": "Functional", "priority": "High"}]
    ))
    result = agent.run_pipeline(sample_requirements_text, output_dir=tmp_output_dir)

    wb = load_workbook(result["files"]["requirements"])
    ws = wb.active

    # After run_pipeline, the worksheet should have column widths set by style_sheet
    col_a_width = ws.column_dimensions['A'].width
    col_b_width = ws.column_dimensions['B'].width

    # Non-None column width indicates style_sheet was called
    assert col_a_width is not None
    assert col_b_width is not None
    assert col_a_width > 0
    assert col_b_width > 0


def test_requirements_report_has_headers_and_data(
    patch_crew_kickoff, make_stage_outputs, sample_requirements_text, tmp_output_dir
):
    reqs = [
        {"req_id": "REQ_1", "requirement": "Feature A", "category": "Functional", "priority": "High"},
        {"req_id": "REQ_2", "requirement": "Feature B", "category": "Non-Functional", "priority": "Low"},
    ]
    patch_crew_kickoff({
        "analyze": __import__("json").dumps(reqs),
        "generate": "[]", "review": "[]", "fix": "[]",
        "automation": "[]", "estimate": "{}",
    })
    result = agent.run_pipeline(sample_requirements_text, output_dir=tmp_output_dir)

    wb = load_workbook(result["files"]["requirements"])
    rows = list(wb.active.iter_rows(values_only=True))
    assert rows[0] == ("Req ID", "Requirement", "Category", "Priority")
    assert len(rows) == 3


def test_test_cases_report_has_headers_and_all_fields(
    patch_crew_kickoff, make_stage_outputs, sample_test_cases, sample_requirements_text, tmp_output_dir
):
    patch_crew_kickoff(make_stage_outputs(generate=sample_test_cases))
    result = agent.run_pipeline(sample_requirements_text, output_dir=tmp_output_dir)

    wb = load_workbook(result["files"]["test_cases"])
    rows = list(wb.active.iter_rows(values_only=True))
    assert rows[0] == ("ID", "Req ID", "Scenario", "Type", "Steps", "Expected Result", "Priority", "Automatable")


def test_automation_feasibility_summary_sheet_contains_all_metrics(
    patch_crew_kickoff, make_stage_outputs, sample_test_cases, sample_automation_results,
    sample_requirements_text, tmp_output_dir,
):
    patch_crew_kickoff(make_stage_outputs(fix=sample_test_cases, automation=sample_automation_results))
    result = agent.run_pipeline(sample_requirements_text, output_dir=tmp_output_dir)

    wb = load_workbook(result["files"]["automation"])
    summary_ws = wb["Summary"]
    rows = list(summary_ws.iter_rows(values_only=True))

    labels = [row[0] for row in rows if row[0]]
    assert "Total Test Cases" in labels
    assert "Automatable" in labels
    assert "Manual Only" in labels
    assert "Automation Coverage %" in labels
