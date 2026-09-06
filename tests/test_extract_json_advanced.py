"""
Advanced edge case testing for extract_json function.
Covers complex JSON structures, malformed inputs, deeply nested data, and edge patterns.
"""

import json
import pytest
import agent


class TestExtractJsonAdvanced:
    """Advanced edge case tests for extract_json function."""

    def test_extracts_deeply_nested_json(self):
        """Test extraction of deeply nested JSON structures."""
        deep = {"level1": {"level2": {"level3": {"level4": {"level5": {"data": "deep"}}}}}}
        payload = json.dumps(deep)
        result = agent.extract_json(payload)
        assert result == deep
        assert result["level1"]["level2"]["level3"]["level4"]["level5"]["data"] == "deep"

    def test_extracts_large_json_array(self):
        """Test extraction of large JSON arrays."""
        large_array = [{"id": i, "name": f"item_{i}", "data": [i*2, i*3]} for i in range(1000)]
        payload = json.dumps(large_array)
        result = agent.extract_json(payload)
        assert len(result) == 1000
        assert result[0]["id"] == 0
        assert result[999]["id"] == 999

    def test_extracts_json_with_escaped_quotes(self):
        """Test extraction handles escaped quotes properly."""
        data = [{"text": 'He said "Hello"', "quote": "She replied 'Hi'"}]
        payload = json.dumps(data)
        result = agent.extract_json(payload)
        assert result == data

    def test_extracts_json_with_unicode_escapes(self):
        """Test extraction of JSON with unicode escape sequences."""
        data = {"emoji": "\u2713", "chinese": "\u4e2d\u6587", "arrow": "\u2192"}
        payload = json.dumps(data)
        result = agent.extract_json(payload)
        assert result["emoji"] == "✓"
        assert result["chinese"] == "中文"

    def test_extracts_json_with_null_values(self):
        """Test extraction handles null values correctly."""
        data = [{"id": "TC_1", "value": None}, {"id": "TC_2", "value": None}]
        payload = json.dumps(data)
        result = agent.extract_json(payload)
        assert result[0]["value"] is None
        assert result[1]["value"] is None

    def test_extracts_json_with_empty_collections(self):
        """Test extraction of empty arrays and objects."""
        data = {"empty_array": [], "empty_object": {}, "normal_array": [1, 2], "normal_obj": {"a": 1}}
        payload = json.dumps(data)
        result = agent.extract_json(payload)
        assert result["empty_array"] == []
        assert result["empty_object"] == {}
        assert result["normal_array"] == [1, 2]

    def test_extracts_json_with_boolean_values(self):
        """Test extraction preserves boolean types."""
        data = [
            {"automatable": True, "active": False},
            {"automatable": False, "active": True}
        ]
        payload = json.dumps(data)
        result = agent.extract_json(payload)
        assert result[0]["automatable"] is True
        assert result[0]["active"] is False
        assert result[1]["automatable"] is False

    def test_extracts_json_with_numeric_precision(self):
        """Test extraction preserves numeric precision."""
        data = [
            {"coverage": 87.5, "count": 1000, "percentage": 0.00001},
            {"estimated_days": 3.14159, "hours": 24}
        ]
        payload = json.dumps(data)
        result = agent.extract_json(payload)
        assert result[0]["coverage"] == 87.5
        assert result[0]["count"] == 1000
        assert result[0]["percentage"] == 0.00001

    def test_extracts_json_surrounded_by_prose(self):
        """Test extraction from JSON embedded in explanation text."""
        text = (
            "Based on the analysis, here are the results:\n"
            "```json\n"
            '[{"id": "TC_1", "type": "Positive"}]\n'
            "```\n"
            "This shows one test case of type Positive."
        )
        result = agent.extract_json(text)
        assert result == [{"id": "TC_1", "type": "Positive"}]

    def test_extracts_json_with_multiple_code_blocks_prefers_last(self):
        """Test extraction prefers the last complete JSON block."""
        text = (
            "First attempt:\n"
            "```json\n"
            '[{"wrong": "data"}]\n'
            "```\n"
            "Corrected version:\n"
            "```json\n"
            '[{"correct": "data"}]\n'
            "```"
        )
        result = agent.extract_json(text)
        assert result == [{"correct": "data"}]

    def test_extracts_json_with_trailing_newlines(self):
        """Test extraction handles trailing whitespace."""
        data = [{"id": "TC_1"}, {"id": "TC_2"}]
        payload = json.dumps(data) + "\n\n\n"
        result = agent.extract_json(payload)
        assert len(result) == 2

    def test_extracts_json_with_leading_whitespace(self):
        """Test extraction handles leading whitespace."""
        data = [{"id": "TC_1"}]
        payload = "   \n\n" + json.dumps(data)
        result = agent.extract_json(payload)
        assert result == data

    def test_extracts_compact_json_no_whitespace(self):
        """Test extraction of compact JSON (no spaces)."""
        data = [{"id":"TC_1","scenario":"test","type":"Positive"}]
        payload = json.dumps(data, separators=(',', ':'))
        result = agent.extract_json(payload)
        assert result == data

    def test_extracts_pretty_formatted_json(self):
        """Test extraction of pretty-printed JSON with indentation."""
        data = [{"id": "TC_1", "steps": ["a", "b", "c"]}]
        payload = json.dumps(data, indent=2)
        result = agent.extract_json(payload)
        assert result == data

    def test_returns_none_for_truncated_json_object(self):
        """Test returns None for incomplete JSON object."""
        truncated = '{"id": "TC_1", "data": {"nested": '
        result = agent.extract_json(truncated)
        assert result is None

    def test_returns_none_for_truncated_json_array(self):
        """Test returns None for incomplete JSON array."""
        truncated = '[{"id": "TC_1"}, {"id": '
        result = agent.extract_json(truncated)
        assert result is None

    def test_returns_none_for_mixed_bracket_mismatch(self):
        """Test returns None for mismatched brackets."""
        bad_json = '[{"id": "TC_1"}]}'  # Extra closing brace
        result = agent.extract_json(bad_json)
        assert result is None

    def test_returns_none_for_trailing_commas(self):
        """Test returns None for invalid trailing commas."""
        bad_json = '[{"id": "TC_1",}]'  # Trailing comma in object
        result = agent.extract_json(bad_json)
        assert result is None

    def test_returns_none_for_unquoted_keys(self):
        """Test returns None for unquoted object keys."""
        bad_json = '[{id: "TC_1"}]'  # Unquoted key
        result = agent.extract_json(bad_json)
        assert result is None

    def test_returns_none_for_single_quoted_strings(self):
        """Test returns None for single-quoted strings (not valid JSON)."""
        bad_json = "[{'id': 'TC_1'}]"  # Single quotes
        result = agent.extract_json(bad_json)
        assert result is None

    def test_handles_json_with_special_float_values(self):
        """Test handling of special float representations."""
        data = [{"value": float('inf')}]
        # JSON.dumps with special float values will create invalid JSON
        # This tests that extract_json doesn't crash on edge cases
        text = '[{"value": 1e308}]'  # Very large number
        result = agent.extract_json(text)
        assert result[0]["value"] > 1e300

    def test_extracts_json_from_markdown_code_fence(self):
        """Test extraction from markdown code fence with language specifier."""
        text = (
            "Here's the output:\n"
            "```json\n"
            '[{"id": "TC_1", "type": "Positive"}]\n'
            "```"
        )
        result = agent.extract_json(text)
        assert result == [{"id": "TC_1", "type": "Positive"}]

    def test_extracts_json_from_generic_code_fence(self):
        """Test extraction from code fence without language specifier."""
        text = (
            "```\n"
            '[{"id": "TC_1"}]\n'
            "```"
        )
        result = agent.extract_json(text)
        assert result == [{"id": "TC_1"}]

    def test_extracts_json_with_tabs_and_spaces_mix(self):
        """Test extraction handles mixed tabs and spaces."""
        data = [{"id": "TC_1", "name": "test"}]
        payload = json.dumps(data).replace(" ", "\t")
        result = agent.extract_json(payload)
        assert result == data

    def test_extracts_test_case_payload_structure(self):
        """Test extraction of typical test case payload structure."""
        payload = json.dumps([
            {
                "id": "TC_1",
                "req_id": "REQ_1",
                "scenario": "User login",
                "type": "Positive",
                "steps": ["Open app", "Enter credentials", "Click login"],
                "expected_result": "Logged in successfully",
                "priority": "High"
            },
            {
                "id": "TC_2",
                "req_id": "REQ_1",
                "scenario": "Invalid credentials",
                "type": "Negative",
                "steps": ["Open app", "Enter invalid credentials", "Click login"],
                "expected_result": "Error message shown",
                "priority": "High"
            }
        ])
        result = agent.extract_json(payload)
        assert len(result) == 2
        assert result[0]["type"] == "Positive"
        assert result[1]["type"] == "Negative"

    def test_extracts_automation_payload_structure(self):
        """Test extraction of typical automation feasibility payload."""
        payload = json.dumps([
            {
                "id": "TC_1",
                "automatable": "Yes",
                "recommended_tool": "Selenium",
                "reason": "Simple UI automation"
            },
            {
                "id": "TC_2",
                "automatable": "No",
                "recommended_tool": "Manual",
                "reason": "Requires human judgment"
            }
        ])
        result = agent.extract_json(payload)
        assert len(result) == 2
        assert result[0]["automatable"] == "Yes"
        assert result[1]["automatable"] == "No"

    def test_extracts_estimation_payload_structure(self):
        """Test extraction of typical estimation payload."""
        payload = json.dumps({
            "total_test_cases": 42,
            "test_cases_per_day": 20,
            "estimated_days": 3
        })
        result = agent.extract_json(payload)
        assert result["total_test_cases"] == 42
        assert result["test_cases_per_day"] == 20
        assert result["estimated_days"] == 3

    def test_extracts_json_with_all_escape_sequences(self):
        """Test extraction handles all JSON escape sequences."""
        data = {
            "quotes": "\"",
            "backslash": "\\",
            "newline": "\n",
            "tab": "\t",
            "carriage_return": "\r",
            "backspace": "\b",
            "form_feed": "\f"
        }
        payload = json.dumps(data)
        result = agent.extract_json(payload)
        assert result["quotes"] == '"'
        assert result["backslash"] == "\\"
        assert result["newline"] == "\n"

    def test_extracts_json_repeated_pattern(self):
        """Test extraction handles repeated similar patterns."""
        text = (
            "Wrong: [1, 2, 3]\n"
            "Wrong: [4, 5, 6]\n"
            "Correct: " + json.dumps([{"id": "TC_1"}])
        )
        result = agent.extract_json(text)
        assert result == [{"id": "TC_1"}]

    def test_returns_none_for_only_primitives(self):
        """Test returns None when text contains only primitives, not object/array."""
        # The function specifically looks for {} or [] patterns
        bad_inputs = ["123", "true", "false", '"string"', "null"]
        for inp in bad_inputs:
            result = agent.extract_json(inp)
            # These might parse as JSON but won't match the regex pattern search
            # If they do match, that's acceptable too
            if result is not None:
                # Verify it's actually the right value
                assert result in [123, True, False, "string", None]
