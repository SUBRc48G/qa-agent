"""
Task 11: Error handling and resilience.
Tests that helper functions handle edge cases gracefully without crashing.
"""

import pytest

import agent


def test_malformed_json_in_extract_json_returns_none():
    malformed = "not json at all"
    result = agent.extract_json(malformed)
    assert result is None


def test_extract_json_with_wrapped_markdown_blocks():
    text = "```json\n{\"key\": \"value\"}\n```"
    result = agent.extract_json(text)
    assert result == {"key": "value"}


def test_safe_function_with_none():
    # safe() returns "" for None, not "None"
    result = agent.safe(None)
    assert result == ""


def test_safe_function_with_empty_list():
    result = agent.safe([])
    assert result == ""


def test_safe_function_with_single_item_list():
    result = agent.safe(["one"])
    assert result == "one"


def test_safe_function_with_multi_item_list():
    # safe() joins lists with \n, not ,
    result = agent.safe(["one", "two", "three"])
    assert result == "one\ntwo\nthree"


def test_safe_function_with_dict():
    result = agent.safe({"key": "value"})
    assert isinstance(result, str)
    # safe() json-dumps dicts
    assert "key" in result and "value" in result


def test_safe_function_with_string():
    result = agent.safe("hello")
    assert result == "hello"


def test_normalize_req_with_valid_dict():
    # normalize_req expects a dict-like object
    result = agent.normalize_req({"req_id": "REQ_1", "requirement": "Test"})
    assert result["req_id"] == "REQ_1"
    assert result["requirement"] == "Test"


def test_normalize_req_with_none_values():
    result = agent.normalize_req({"req_id": None, "requirement": None})
    # safe(None) = "", so all None fields become ""
    assert result == {"req_id": "", "requirement": "", "category": "", "priority": ""}


def test_format_steps_with_empty_list():
    result = agent.format_steps([])
    assert result == ""


def test_format_steps_with_single_step():
    result = agent.format_steps(["Single step"])
    assert result == "1. Single step"


def test_format_steps_with_multiple_steps():
    result = agent.format_steps(["Step one", "Step two"])
    assert "1. Step one" in result
    assert "2. Step two" in result


def test_normalize_tc_with_missing_id():
    tc = {"scenario": "test", "type": "Positive"}
    result = agent.normalize_tc(tc, {})

    assert result["id"] == ""
    assert result["req_id"] == ""
    assert result["scenario"] == "test"
    assert result["type"] == "Positive"


def test_normalize_automation_with_missing_fields():
    auto_partial = {"id": "TC_1"}
    result = agent.normalize_automation(auto_partial, {})

    assert result["id"] == "TC_1"
    assert "automatable" in result
    assert "recommended_tool" in result
    assert "reason" in result
