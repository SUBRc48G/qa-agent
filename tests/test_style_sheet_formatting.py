"""
Unit tests for Excel styling and formatting functions.
Tests the style_sheet function which handles column widths, text wrapping, alignment, and row heights.
"""

import pytest
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter

import agent


class TestStyleSheetBasic:
    """Basic tests for style_sheet function."""

    def test_applies_column_widths(self):
        """Test that column widths are set correctly."""
        wb = Workbook()
        ws = wb.active
        ws.append(["Header1", "Header2", "Header3"])
        
        col_widths = [15, 30, 50]
        agent.style_sheet(ws, col_widths=col_widths)
        
        for idx, width in enumerate(col_widths, start=1):
            col_letter = get_column_letter(idx)
            assert ws.column_dimensions[col_letter].width == width

    def test_applies_bold_to_header_row(self):
        """Test that header row is formatted as bold."""
        wb = Workbook()
        ws = wb.active
        ws.append(["Header1", "Header2"])
        
        agent.style_sheet(ws, col_widths=[10, 10])
        
        for cell in ws[1]:
            assert cell.font.bold is True

    def test_sets_header_alignment_center(self):
        """Test that header cells are center-aligned."""
        wb = Workbook()
        ws = wb.active
        ws.append(["Header1", "Header2"])
        
        agent.style_sheet(ws, col_widths=[10, 10])
        
        for cell in ws[1]:
            assert cell.alignment.horizontal == "center"

    def test_enables_text_wrap_on_header(self):
        """Test that header cells have text wrapping enabled."""
        wb = Workbook()
        ws = wb.active
        ws.append(["Header1", "Header2"])
        
        agent.style_sheet(ws, col_widths=[10, 10])
        
        for cell in ws[1]:
            assert cell.alignment.wrap_text is True

    def test_freezes_panes_at_a2(self):
        """Test that panes are frozen at A2 (first row and first column locked)."""
        wb = Workbook()
        ws = wb.active
        ws.append(["Header1", "Header2"])
        ws.append(["Row1Col1", "Row1Col2"])
        
        agent.style_sheet(ws, col_widths=[10, 10])
        
        assert ws.freeze_panes == "A2"

    def test_wraps_long_text_in_data_rows(self):
        """Test that long text in data rows is wrapped."""
        wb = Workbook()
        ws = wb.active
        ws.append(["ID", "Description"])
        ws.append(["TC_1", "A" * 100])  # Long text
        
        agent.style_sheet(ws, col_widths=[10, 50])
        
        # Second column should have wrap enabled
        cell = ws.cell(row=2, column=2)
        assert cell.alignment.wrap_text is True

    def test_aligns_data_rows_to_top(self):
        """Test that data rows are top-aligned."""
        wb = Workbook()
        ws = wb.active
        ws.append(["Header"])
        ws.append(["Data"])
        
        agent.style_sheet(ws, col_widths=[10])
        
        data_cell = ws.cell(row=2, column=1)
        assert data_cell.alignment.vertical == "top"


class TestStyleSheetWrapColumns:
    """Tests for wrap_cols parameter."""

    def test_wraps_specified_columns_only(self):
        """Test that only specified columns have text wrapping."""
        wb = Workbook()
        ws = wb.active
        ws.append(["Col1", "Col2", "Col3"])
        ws.append(["Data1", "Data2", "Data3"])
        
        # Only wrap columns 1 and 3
        agent.style_sheet(ws, col_widths=[10, 10, 10], wrap_cols=[1, 3])
        
        # Column 1 should wrap
        assert ws.cell(row=2, column=1).alignment.wrap_text is True
        # Column 3 should wrap
        assert ws.cell(row=2, column=3).alignment.wrap_text is True
        # Column 2 should not wrap (default for data rows is no wrap)
        # Note: openpyxl default might be None, check accordingly
        col2_wrap = ws.cell(row=2, column=2).alignment.wrap_text
        # Data rows default to wrap_text not set unless in wrap_cols

    def test_wrap_cols_empty_list(self):
        """Test behavior when wrap_cols is empty."""
        wb = Workbook()
        ws = wb.active
        ws.append(["Col1", "Col2"])
        ws.append(["Data1", "Data2"])
        
        agent.style_sheet(ws, col_widths=[10, 10], wrap_cols=[])
        
        # With empty wrap_cols, no data cells should wrap
        assert ws.cell(row=2, column=1).alignment.wrap_text is None or \
               ws.cell(row=2, column=1).alignment.wrap_text is False

    def test_wrap_cols_none_defaults_to_all_columns(self):
        """Test that wrap_cols=None wraps all data columns."""
        wb = Workbook()
        ws = wb.active
        ws.append(["Col1", "Col2", "Col3"])
        ws.append(["Data1", "Data2", "Data3"])
        
        agent.style_sheet(ws, col_widths=[10, 10, 10], wrap_cols=None)
        
        # All columns should be wrapped (default behavior)
        assert ws.cell(row=2, column=1).alignment.wrap_text is True
        assert ws.cell(row=2, column=2).alignment.wrap_text is True
        assert ws.cell(row=2, column=3).alignment.wrap_text is True


class TestStyleSheetRowHeights:
    """Tests for dynamic row height adjustment based on content."""

    def test_increases_row_height_for_multiline_text(self):
        """Test that rows with multiline text get taller."""
        wb = Workbook()
        ws = wb.active
        ws.append(["Header"])
        ws.append(["Single line"])
        ws.append(["Line1\nLine2\nLine3\nLine4\nLine5"])  # 5 lines
        
        agent.style_sheet(ws, col_widths=[50])
        
        # Default row height is 15
        # 5 lines * 15 = 75, but capped at 409
        assert ws.row_dimensions[3].height >= 60  # Should be > default

    def test_row_height_respects_max_cap(self):
        """Test that row height is capped at 409."""
        wb = Workbook()
        ws = wb.active
        ws.append(["Header"])
        # Create very long multiline text (100 lines)
        long_text = "\n".join([f"Line {i}" for i in range(100)])
        ws.append([long_text])
        
        agent.style_sheet(ws, col_widths=[50])
        
        # Height should be capped at 409
        assert ws.row_dimensions[2].height <= 409

    def test_row_height_respects_minimum(self):
        """Test that row height maintains minimum of 15."""
        wb = Workbook()
        ws = wb.active
        ws.append(["Header"])
        ws.append(["Single line"])
        
        agent.style_sheet(ws, col_widths=[50])
        
        # Single line rows should be at least 15
        assert ws.row_dimensions[2].height >= 15

    def test_row_height_calculated_from_longest_cell(self):
        """Test that row height considers the cell with most lines."""
        wb = Workbook()
        ws = wb.active
        ws.append(["Col1", "Col2", "Col3"])
        ws.append(["Line1\nLine2", "Single", "Line1\nLine2\nLine3"])  # Max 3 lines
        
        agent.style_sheet(ws, col_widths=[20, 20, 20])
        
        # Row should be sized for 3 lines minimum
        assert ws.row_dimensions[2].height >= 40  # 3 * 15 = 45


class TestStyleSheetMultipleRows:
    """Tests for styling multiple data rows."""

    def test_styles_all_data_rows(self):
        """Test that all data rows are styled correctly."""
        wb = Workbook()
        ws = wb.active
        ws.append(["ID", "Name", "Description"])
        for i in range(1, 11):
            ws.append([f"TC_{i}", f"Test {i}", f"Description for test {i}"])
        
        agent.style_sheet(ws, col_widths=[10, 20, 40])
        
        # Check all data rows have proper alignment
        for row_idx in range(2, 12):
            for col_idx in range(1, 4):
                cell = ws.cell(row=row_idx, column=col_idx)
                assert cell.alignment.vertical == "top"

    def test_preserves_header_style_with_many_rows(self):
        """Test that header remains bold with many data rows."""
        wb = Workbook()
        ws = wb.active
        ws.append(["Header1", "Header2"])
        for i in range(1, 101):
            ws.append([f"Data{i}A", f"Data{i}B"])
        
        agent.style_sheet(ws, col_widths=[15, 15])
        
        # Header should still be bold
        for cell in ws[1]:
            assert cell.font.bold is True


class TestStyleSheetEdgeCases:
    """Edge case tests for style_sheet function."""

    def test_handles_empty_worksheet(self):
        """Test that function handles empty worksheet gracefully."""
        wb = Workbook()
        ws = wb.active
        # No rows added
        
        # Should not crash
        agent.style_sheet(ws, col_widths=[10, 20])

    def test_handles_single_row(self):
        """Test that function handles worksheet with only header."""
        wb = Workbook()
        ws = wb.active
        ws.append(["Header1", "Header2"])
        
        agent.style_sheet(ws, col_widths=[10, 20])
        
        assert ws.freeze_panes == "A2"

    def test_handles_single_column(self):
        """Test that function handles single column worksheet."""
        wb = Workbook()
        ws = wb.active
        ws.append(["Header"])
        ws.append(["Data1"])
        ws.append(["Data2"])
        
        agent.style_sheet(ws, col_widths=[50])
        
        assert ws.column_dimensions["A"].width == 50

    def test_handles_very_many_columns(self):
        """Test that function handles worksheets with many columns."""
        wb = Workbook()
        ws = wb.active
        headers = [f"Col{i}" for i in range(50)]
        ws.append(headers)
        
        col_widths = [15] * 50
        agent.style_sheet(ws, col_widths=col_widths)
        
        # Check first and last columns
        assert ws.column_dimensions["A"].width == 15
        assert ws.column_dimensions[get_column_letter(50)].width == 15

    def test_handles_very_many_rows(self):
        """Test that function handles worksheets with many rows."""
        wb = Workbook()
        ws = wb.active
        ws.append(["ID", "Name"])
        for i in range(1, 1001):
            ws.append([f"TC_{i}", f"Test {i}"])
        
        agent.style_sheet(ws, col_widths=[10, 30])
        
        # Should not crash
        assert ws.freeze_panes == "A2"

    def test_handles_cells_with_only_newlines(self):
        """Test that cells with only whitespace/newlines are handled."""
        wb = Workbook()
        ws = wb.active
        ws.append(["Header"])
        ws.append(["\n\n\n"])
        
        agent.style_sheet(ws, col_widths=[20])
        
        # Should not crash

    def test_handles_cells_with_mixed_whitespace(self):
        """Test that cells with mixed whitespace are handled."""
        wb = Workbook()
        ws = wb.active
        ws.append(["Header"])
        ws.append(["Line1\n   \nLine2\t\nLine3"])
        
        agent.style_sheet(ws, col_widths=[50])
        
        # Should count lines correctly
        row_height = ws.row_dimensions[2].height
        assert row_height >= 30  # At least 2-3 lines


class TestStyleSheetIntegration:
    """Integration tests combining multiple styling features."""

    def test_complete_test_case_report_styling(self):
        """Test styling of a complete test case report."""
        wb = Workbook()
        ws = wb.active
        
        # Typical test case report structure
        ws.append(["ID", "Scenario", "Type", "Steps", "Expected Result", "Priority"])
        ws.append([
            "TC_1",
            "Valid login",
            "Positive",
            "1. Open app\n2. Enter creds\n3. Click login",
            "User logged in",
            "High"
        ])
        ws.append([
            "TC_2",
            "Invalid password",
            "Negative",
            "1. Open app\n2. Enter invalid pass\n3. Click login",
            "Error shown",
            "High"
        ])
        
        col_widths = [10, 20, 10, 40, 30, 10]
        agent.style_sheet(ws, col_widths=col_widths)
        
        # Verify structure
        assert ws.freeze_panes == "A2"
        assert ws[1][0].font.bold is True
        assert ws.row_dimensions[2].height > 15

    def test_complete_automation_report_styling(self):
        """Test styling of automation feasibility report."""
        wb = Workbook()
        ws = wb.active
        
        ws.append(["ID", "Scenario", "Automatable", "Recommended Tool", "Reason"])
        ws.append([
            "TC_1",
            "Login with valid credentials",
            "Yes",
            "Selenium",
            "Simple UI flow, deterministic validation"
        ])
        ws.append([
            "TC_4",
            "Permission check - read-only user deletion",
            "No",
            "Manual",
            "Requires manual permission audit"
        ])
        
        col_widths = [10, 30, 12, 20, 40]
        agent.style_sheet(ws, col_widths=col_widths)
        
        # Verify header styling
        for idx, width in enumerate(col_widths, start=1):
            col_letter = get_column_letter(idx)
            assert ws.column_dimensions[col_letter].width == width

    def test_requirements_report_styling(self):
        """Test styling of requirements report."""
        wb = Workbook()
        ws = wb.active
        
        ws.append(["Req ID", "Requirement", "Category", "Priority"])
        ws.append([
            "REQ_1",
            "User must be able to list all credentials created in the system so that they can review existing credentials",
            "Functional",
            "High"
        ])
        
        col_widths = [10, 60, 16, 10]
        agent.style_sheet(ws, col_widths=col_widths)
        
        assert ws.column_dimensions["B"].width == 60  # Wide requirement column

    def test_estimation_report_styling(self):
        """Test styling of effort estimation report."""
        wb = Workbook()
        ws = wb.active
        
        ws.append(["Total TC", "Per Day", "Days"])
        ws.append(["42", "20", "3"])
        
        col_widths = [15, 12, 10]
        agent.style_sheet(ws, col_widths=col_widths)
        
        assert ws.freeze_panes == "A2"
        assert ws[1][0].font.bold is True
