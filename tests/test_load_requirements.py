"""
Task 3: load_requirements() across every supported file format (.txt, .pdf, .docx,
.xlsx), plus load_requirements_auto() and error handling for unsupported/missing/
corrupted files.
"""

import pytest
from docx.opc.exceptions import PackageNotFoundError
from pypdf.errors import PdfStreamError

import agent


class TestLoadRequirementsTxt:
    def test_reads_plain_text_file(self, sample_txt_file, sample_requirements_text):
        result = agent.load_requirements(sample_txt_file)
        assert result == sample_requirements_text
        assert result.strip() != ""

    def test_missing_txt_file_raises_file_not_found(self, tmp_path):
        missing = tmp_path / "does_not_exist.txt"
        with pytest.raises(FileNotFoundError):
            agent.load_requirements(str(missing))


class TestLoadRequirementsPdf:
    def test_reads_the_sample_requirements_pdf(self, test_config):
        if not test_config.SAMPLE_PDF_PATH.exists():
            pytest.skip("requirements.pdf not present in the project root")
        result = agent.load_requirements(str(test_config.SAMPLE_PDF_PATH))
        assert isinstance(result, str)
        assert result.strip() != ""

    def test_missing_pdf_file_raises_file_not_found(self, tmp_path):
        missing = tmp_path / "does_not_exist.pdf"
        with pytest.raises(FileNotFoundError):
            agent.load_requirements(str(missing))

    def test_corrupted_pdf_raises(self, tmp_path):
        bad_pdf = tmp_path / "corrupted.pdf"
        bad_pdf.write_bytes(b"this is not a real pdf")
        with pytest.raises(PdfStreamError):
            agent.load_requirements(str(bad_pdf))


class TestLoadRequirementsDocx:
    def test_reads_paragraphs_and_table_rows(self, sample_docx_file):
        result = agent.load_requirements(sample_docx_file)
        assert result.strip() != ""
        assert "Network Account Read-only User" in result
        # Table rows are joined with " | " and appended as their own line.
        assert "REQ_EXTRA | Requirement supplied via a table row" in result

    def test_missing_docx_file_raises(self, tmp_path):
        missing = tmp_path / "does_not_exist.docx"
        with pytest.raises(PackageNotFoundError):
            agent.load_requirements(str(missing))

    def test_corrupted_docx_raises(self, corrupted_docx_file):
        with pytest.raises(PackageNotFoundError):
            agent.load_requirements(corrupted_docx_file)


class TestLoadRequirementsXlsx:
    def test_reads_all_rows_from_all_sheets(self, sample_xlsx_file, sample_requirement_items):
        result = agent.load_requirements(sample_xlsx_file)
        assert result.strip() != ""
        # Header row and every data row should be present, pipe-joined.
        assert "Req ID | Requirement | Category | Priority" in result
        for r in sample_requirement_items:
            assert r["req_id"] in result
            assert r["requirement"] in result

    def test_missing_xlsx_file_raises_file_not_found(self, tmp_path):
        missing = tmp_path / "does_not_exist.xlsx"
        with pytest.raises(FileNotFoundError):
            agent.load_requirements(str(missing))

    def test_blank_cells_are_skipped(self, tmp_path):
        from openpyxl import Workbook

        path = tmp_path / "with_blanks.xlsx"
        wb = Workbook()
        ws = wb.active
        ws.append(["REQ_1", None, "Some requirement"])
        ws.append([None, None, None])  # fully blank row should not add a blank line
        wb.save(str(path))

        result = agent.load_requirements(str(path))
        assert "REQ_1 | Some requirement" in result
        assert "\n\n" not in result.strip()


class TestLoadRequirementsErrors:
    def test_unsupported_extension_raises_value_error(self, tmp_path):
        bad_file = tmp_path / "sample.csv"
        bad_file.write_text("req_id,requirement\nREQ_1,Do a thing\n")
        with pytest.raises(ValueError):
            agent.load_requirements(str(bad_file))

    def test_no_extension_raises_value_error(self, tmp_path):
        bad_file = tmp_path / "sample_without_extension"
        bad_file.write_text("some content")
        with pytest.raises(ValueError):
            agent.load_requirements(str(bad_file))


class TestLoadRequirementsAuto:
    def test_prefers_pdf_over_txt_when_both_present(self, tmp_path, monkeypatch):
        (tmp_path / "requirements.pdf").write_bytes(b"not read, just needs to exist for this test")
        (tmp_path / "qa_requirements.txt").write_text("fallback text")
        monkeypatch.chdir(tmp_path)

        # requirements.pdf here is a fake/corrupted PDF, so loading it should still be
        # *attempted* first and fail with a pypdf error rather than silently falling
        # back to the .txt file.
        with pytest.raises(PdfStreamError):
            agent.load_requirements_auto()

    def test_falls_back_to_txt_when_no_pdf_present(self, tmp_path, monkeypatch):
        (tmp_path / "qa_requirements.txt").write_text("fallback text")
        monkeypatch.chdir(tmp_path)
        assert agent.load_requirements_auto() == "fallback text"

    def test_raises_file_not_found_when_neither_file_exists(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(FileNotFoundError):
            agent.load_requirements_auto()
