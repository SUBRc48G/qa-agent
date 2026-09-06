"""
Task 2: Unit tests for the small data-transformation helpers — normalize_req,
normalize_tc, extract_json, format_steps — including edge cases (None, empty
strings, nested lists, malformed JSON).
"""

import json

import pytest

import agent


# ---------------- extract_json ----------------

class TestExtractJson:
    def test_parses_plain_json_array(self):
        assert agent.extract_json('[{"a": 1}]') == [{"a": 1}]

    def test_parses_plain_json_object(self):
        assert agent.extract_json('{"a": 1}') == {"a": 1}

    def test_strips_markdown_fences(self):
        text = '```json\n[{"a": 1}]\n```'
        assert agent.extract_json(text) == [{"a": 1}]

    def test_extracts_json_with_leading_explanation_text(self):
        text = 'Sure, here is the JSON you asked for:\n[{"a": 1}, {"b": 2}]'
        assert agent.extract_json(text) == [{"a": 1}, {"b": 2}]

    def test_picks_the_last_valid_json_block_when_multiple_present(self):
        # Alternating bracket types (array, then object) split into two separate regex
        # matches; extract_json should prefer the later, real answer over the first.
        text = '[{"a": 1}]\nFinal answer: {"b": 2}'
        assert agent.extract_json(text) == {"b": 2}

    def test_returns_none_when_extra_text_sits_between_two_same_type_blocks(self):
        # A known limitation: greedy DOTALL matching spans from the first "{" to the
        # LAST "}" in the text when both blocks are objects, swallowing the text between
        # them into one unparseable match.
        text = 'Ignore this example: {"a": 1}\nFinal answer: {"b": 2}'
        assert agent.extract_json(text) is None

    @pytest.mark.parametrize("bad_input", ["", None, "not json at all", "   "])
    def test_returns_none_for_unparseable_input(self, bad_input):
        assert agent.extract_json(bad_input) is None

    def test_returns_none_for_malformed_json(self):
        assert agent.extract_json('[{"a": 1,}]') is None

    def test_handles_nested_structures(self):
        payload = [{"id": "TC_1", "steps": ["a", "b"], "meta": {"x": [1, 2, 3]}}]
        assert agent.extract_json(json.dumps(payload)) == payload


# ---------------- normalize_req ----------------

class TestNormalizeReq:
    def test_normalizes_a_complete_requirement(self):
        r = {"req_id": "REQ_1", "requirement": "Do the thing", "category": "Functional", "priority": "High"}
        assert agent.normalize_req(r) == r

    def test_fills_missing_fields_with_empty_string(self):
        assert agent.normalize_req({}) == {
            "req_id": "", "requirement": "", "category": "", "priority": "",
        }

    def test_none_values_become_empty_strings(self):
        r = {"req_id": None, "requirement": None, "category": None, "priority": None}
        assert agent.normalize_req(r) == {
            "req_id": "", "requirement": "", "category": "", "priority": "",
        }

    def test_non_string_values_are_stringified(self):
        r = {"req_id": 1, "requirement": "text", "category": "Functional", "priority": "High"}
        assert agent.normalize_req(r)["req_id"] == "1"


# ---------------- format_steps ----------------

class TestFormatSteps:
    def test_numbers_a_plain_list_of_steps(self):
        result = agent.format_steps(["Open the app", "Click login"])
        assert result == "1. Open the app\n2. Click login"

    def test_does_not_double_number_already_numbered_steps(self):
        result = agent.format_steps(["1. Open the app", "2) Click login"])
        assert result == "1. Open the app\n2) Click login"

    def test_strips_whitespace_around_each_step(self):
        result = agent.format_steps(["  Open the app  ", "Click login"])
        assert result == "1. Open the app\n2. Click login"

    def test_empty_list_returns_empty_string(self):
        assert agent.format_steps([]) == ""

    def test_falls_back_to_safe_for_non_list_input(self):
        assert agent.format_steps("Open the app") == "Open the app"

    def test_none_returns_empty_string(self):
        assert agent.format_steps(None) == ""

    def test_nested_list_items_are_stringified(self):
        # A malformed LLM response might nest lists; format_steps must not crash.
        result = agent.format_steps([["Open the app", "extra"], "Click login"])
        assert "Click login" in result
        assert result.startswith("1. ")


# ---------------- normalize_tc ----------------

class TestNormalizeTc:
    def test_normalizes_a_complete_test_case(self):
        tc = {
            "id": "TC_1", "req_id": "REQ_1", "scenario": "Login", "type": "Positive",
            "steps": ["Open app", "Login"], "expected_result": "Logged in", "priority": "High",
        }
        result = agent.normalize_tc(tc)
        assert result["id"] == "TC_1"
        assert result["req_id"] == "REQ_1"
        assert result["scenario"] == "Login"
        assert result["type"] == "Positive"
        assert result["steps"] == "1. Open app\n2. Login"
        assert result["expected_result"] == "Logged in"
        assert result["priority"] == "High"
        assert result["automatable"] == ""

    def test_missing_fields_default_to_empty_string(self):
        result = agent.normalize_tc({})
        assert all(v == "" for k, v in result.items() if k != "steps")
        assert result["steps"] == ""

    def test_automatable_is_filled_from_lookup_by_id(self):
        tc = {"id": "TC_1", "scenario": "x"}
        lookup = {"TC_1": {"automatable": "Yes", "recommended_tool": "Selenium"}}
        result = agent.normalize_tc(tc, automation_lookup=lookup)
        assert result["automatable"] == "Yes"

    def test_automatable_blank_when_id_not_in_lookup(self):
        tc = {"id": "TC_99", "scenario": "x"}
        lookup = {"TC_1": {"automatable": "Yes", "recommended_tool": "Selenium"}}
        result = agent.normalize_tc(tc, automation_lookup=lookup)
        assert result["automatable"] == ""

    def test_none_automation_lookup_is_safe(self):
        result = agent.normalize_tc({"id": "TC_1"}, automation_lookup=None)
        assert result["automatable"] == ""

    def test_steps_as_plain_string_is_preserved(self):
        result = agent.normalize_tc({"id": "TC_1", "steps": "1. Do a thing"})
        assert result["steps"] == "1. Do a thing"


# ---------------- normalize_automation ----------------

class TestNormalizeAutomation:
    def test_normalizes_and_looks_up_scenario(self):
        a = {"id": "TC_1", "automatable": "Yes", "recommended_tool": "Selenium", "reason": "stable"}
        result = agent.normalize_automation(a, scenario_lookup={"TC_1": "Login test"})
        assert result == {
            "id": "TC_1", "scenario": "Login test", "automatable": "Yes",
            "recommended_tool": "Selenium", "reason": "stable",
        }

    def test_missing_scenario_lookup_entry_is_blank(self):
        a = {"id": "TC_99", "automatable": "No", "recommended_tool": "Manual", "reason": "n/a"}
        result = agent.normalize_automation(a, scenario_lookup={})
        assert result["scenario"] == ""


# ---------------- safe ----------------

class TestSafe:
    def test_none_becomes_empty_string(self):
        assert agent.safe(None) == ""

    def test_list_joins_with_newlines(self):
        assert agent.safe(["a", "b"]) == "a\nb"

    def test_dict_becomes_json_string(self):
        assert agent.safe({"a": 1}) == json.dumps({"a": 1})

    def test_nested_list_of_lists(self):
        assert agent.safe([["a", "b"], "c"]) == "a\nb\nc"

    def test_number_is_stringified(self):
        assert agent.safe(42) == "42"
