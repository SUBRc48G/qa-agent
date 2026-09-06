"""
Extended edge case testing for normalize_req, normalize_tc, and normalize_automation.
Covers boundary conditions, missing data, type coercion, and special characters.
"""

import json
import pytest
import agent


class TestNormalizeReqEdgeCases:
    """Comprehensive edge case tests for normalize_req function."""

    def test_normalizes_with_special_characters(self):
        r = {
            "req_id": "REQ_1",
            "requirement": "User must & can access <special> 'characters' \"quoted\"",
            "category": "Functional",
            "priority": "High"
        }
        result = agent.normalize_req(r)
        assert result["requirement"] == r["requirement"]

    def test_normalizes_very_long_requirement_text(self):
        long_text = "A" * 10000  # 10KB requirement
        r = {
            "req_id": "REQ_LONG",
            "requirement": long_text,
            "category": "Functional",
            "priority": "Low"
        }
        result = agent.normalize_req(r)
        assert result["requirement"] == long_text
        assert len(result["requirement"]) == 10000

    def test_normalizes_with_unicode_characters(self):
        r = {
            "req_id": "REQ_1",
            "requirement": "支援 المستخدم 中文 عربي Ελληνικά",
            "category": "Functional",
            "priority": "High"
        }
        result = agent.normalize_req(r)
        assert result["requirement"] == r["requirement"]

    def test_normalizes_with_multiline_text(self):
        r = {
            "req_id": "REQ_1",
            "requirement": "Line 1\nLine 2\nLine 3",
            "category": "Functional",
            "priority": "High"
        }
        result = agent.normalize_req(r)
        assert "\n" in result["requirement"]
        assert result["requirement"] == r["requirement"]

    def test_normalizes_with_empty_dict(self):
        result = agent.normalize_req({})
        assert all(v == "" for v in result.values())

    def test_normalizes_with_boolean_values(self):
        r = {
            "req_id": True,
            "requirement": False,
            "category": "Functional",
            "priority": "High"
        }
        result = agent.normalize_req(r)
        assert result["req_id"] == "True"
        assert result["requirement"] == "False"

    def test_normalizes_with_numeric_values(self):
        r = {
            "req_id": 12345,
            "requirement": 3.14159,
            "category": "Functional",
            "priority": 100
        }
        result = agent.normalize_req(r)
        assert result["req_id"] == "12345"
        assert result["requirement"] == "3.14159"
        assert result["priority"] == "100"

    def test_normalizes_with_list_in_requirement(self):
        r = {
            "req_id": "REQ_1",
            "requirement": ["item1", "item2", "item3"],
            "category": "Functional",
            "priority": "High"
        }
        result = agent.normalize_req(r)
        # Lists are handled by safe() which joins with \n
        assert "item1" in result["requirement"]
        assert "item2" in result["requirement"]

    def test_normalizes_with_dict_in_requirement(self):
        r = {
            "req_id": "REQ_1",
            "requirement": {"nested": "dict", "value": 42},
            "category": "Functional",
            "priority": "High"
        }
        result = agent.normalize_req(r)
        assert isinstance(result["requirement"], str)
        assert "nested" in result["requirement"]

    def test_normalizes_with_whitespace_only_strings(self):
        r = {
            "req_id": "   ",
            "requirement": "\t\n  ",
            "category": "   ",
            "priority": "\t"
        }
        result = agent.normalize_req(r)
        assert result["req_id"] == "   "  # Not stripped, as-is
        assert result["requirement"] == "\t\n  "

    def test_normalizes_with_missing_some_fields(self):
        r = {"req_id": "REQ_1"}  # Missing other fields
        result = agent.normalize_req(r)
        assert result["req_id"] == "REQ_1"
        assert result["requirement"] == ""
        assert result["category"] == ""
        assert result["priority"] == ""


class TestNormalizeTcEdgeCases:
    """Comprehensive edge case tests for normalize_tc function."""

    def test_normalizes_with_very_many_steps(self):
        steps = [f"Step {i}" for i in range(100)]
        tc = {
            "id": "TC_1",
            "req_id": "REQ_1",
            "scenario": "Complex flow",
            "type": "Positive",
            "steps": steps,
            "expected_result": "Success",
            "priority": "High"
        }
        result = agent.normalize_tc(tc)
        assert result["id"] == "TC_1"
        # format_steps should number all 100 steps
        assert "1. Step 0" in result["steps"]
        assert "100. Step 99" in result["steps"]

    def test_normalizes_with_empty_steps_list(self):
        tc = {
            "id": "TC_1",
            "req_id": "REQ_1",
            "scenario": "Empty flow",
            "type": "Positive",
            "steps": [],
            "expected_result": "Success",
            "priority": "High"
        }
        result = agent.normalize_tc(tc)
        assert result["steps"] == ""

    def test_normalizes_with_steps_containing_special_chars(self):
        tc = {
            "id": "TC_1",
            "req_id": "REQ_1",
            "scenario": "Special chars",
            "type": "Positive",
            "steps": ["Click & confirm", "Enter 'password'", 'Type "test"'],
            "expected_result": "Success",
            "priority": "High"
        }
        result = agent.normalize_tc(tc)
        assert "Click & confirm" in result["steps"]
        assert "'password'" in result["steps"]
        assert '"test"' in result["steps"]

    def test_normalizes_with_already_numbered_steps(self):
        tc = {
            "id": "TC_1",
            "req_id": "REQ_1",
            "scenario": "Pre-numbered",
            "type": "Positive",
            "steps": ["1. First step", "2) Second step", "3rd step"],
            "expected_result": "Success",
            "priority": "High"
        }
        result = agent.normalize_tc(tc)
        # Pre-numbered steps should not be re-numbered
        assert "1. First step" in result["steps"]
        assert "2) Second step" in result["steps"]
        assert "3. 3rd step" in result["steps"]  # Added numbering (step 3 gets "3.")

    def test_normalizes_tc_with_none_type(self):
        tc = {
            "id": "TC_1",
            "req_id": "REQ_1",
            "scenario": "Unknown type",
            "type": None,
            "steps": ["Step 1"],
            "expected_result": "Success",
            "priority": "High"
        }
        result = agent.normalize_tc(tc)
        assert result["type"] == ""

    def test_normalizes_tc_with_all_types(self):
        test_types = [
            "Positive", "Negative", "Edge", "Security", "Performance",
            "Compatibility", "Integration", "Data Validation", "Regression",
            "Usability", "Accessibility"
        ]
        for test_type in test_types:
            tc = {
                "id": f"TC_{test_type}",
                "req_id": "REQ_1",
                "scenario": f"{test_type} test",
                "type": test_type,
                "steps": ["Step 1"],
                "expected_result": "Success",
                "priority": "High"
            }
            result = agent.normalize_tc(tc)
            assert result["type"] == test_type

    def test_normalizes_with_very_long_scenario(self):
        long_scenario = "A" * 5000
        tc = {
            "id": "TC_1",
            "req_id": "REQ_1",
            "scenario": long_scenario,
            "type": "Positive",
            "steps": ["Step 1"],
            "expected_result": "Success",
            "priority": "High"
        }
        result = agent.normalize_tc(tc)
        assert result["scenario"] == long_scenario

    def test_normalizes_with_automation_lookup_various_formats(self):
        tc = {"id": "TC_1", "scenario": "x"}
        
        # Case 1: automatable = Yes
        lookup1 = {"TC_1": {"automatable": "Yes", "recommended_tool": "Selenium"}}
        result1 = agent.normalize_tc(tc, automation_lookup=lookup1)
        assert result1["automatable"] == "Yes"
        
        # Case 2: automatable = No
        lookup2 = {"TC_1": {"automatable": "No", "recommended_tool": "Manual"}}
        result2 = agent.normalize_tc(tc, automation_lookup=lookup2)
        assert result2["automatable"] == "No"
        
        # Case 3: automatable = empty string
        lookup3 = {"TC_1": {"automatable": "", "recommended_tool": "Unknown"}}
        result3 = agent.normalize_tc(tc, automation_lookup=lookup3)
        assert result3["automatable"] == ""

    def test_normalizes_with_numeric_ids(self):
        tc = {
            "id": 12345,
            "req_id": 99,
            "scenario": "Numeric IDs",
            "type": "Positive",
            "steps": ["Step 1"],
            "expected_result": "Success",
            "priority": "High"
        }
        result = agent.normalize_tc(tc)
        assert result["id"] == "12345"
        assert result["req_id"] == "99"

    def test_normalizes_with_mixed_step_formats(self):
        tc = {
            "id": "TC_1",
            "req_id": "REQ_1",
            "scenario": "Mixed formats",
            "type": "Positive",
            "steps": [
                "1. First",
                "2) Second",
                "Third (no number)",
                "   Fourth (leading spaces)   ",
                ""  # Empty step
            ],
            "expected_result": "Success",
            "priority": "High"
        }
        result = agent.normalize_tc(tc)
        assert "1. First" in result["steps"]
        assert "2) Second" in result["steps"]
        assert "Third (no number)" in result["steps"]


class TestNormalizeAutomationEdgeCases:
    """Comprehensive edge case tests for normalize_automation function."""

    def test_normalizes_with_all_automation_tools(self):
        tools = [
            "Selenium", "Playwright", "Cypress", "Appium",
            "Postman", "RestAssured", "pytest+requests", "JMeter", "k6", "Manual"
        ]
        
        for tool in tools:
            a = {
                "id": f"TC_{tool}",
                "automatable": "Yes" if tool != "Manual" else "No",
                "recommended_tool": tool,
                "reason": f"Suitable for {tool} testing"
            }
            result = agent.normalize_automation(a, scenario_lookup={})
            assert result["recommended_tool"] == tool

    def test_normalizes_with_very_long_reason_text(self):
        long_reason = "A" * 2000
        a = {
            "id": "TC_1",
            "automatable": "Yes",
            "recommended_tool": "Selenium",
            "reason": long_reason
        }
        result = agent.normalize_automation(a, scenario_lookup={})
        assert result["reason"] == long_reason

    def test_normalizes_with_special_characters_in_reason(self):
        a = {
            "id": "TC_1",
            "automatable": "Yes",
            "recommended_tool": "Selenium",
            "reason": "Test & validate <HTML> 'quotes' \"double quotes\""
        }
        result = agent.normalize_automation(a, scenario_lookup={})
        assert result["reason"] == a["reason"]

    def test_normalizes_with_unicode_in_scenario(self):
        a = {
            "id": "TC_1",
            "automatable": "Yes",
            "recommended_tool": "Selenium",
            "reason": "Stable"
        }
        scenario_lookup = {"TC_1": "测试场景 🧪 اختبار"}
        result = agent.normalize_automation(a, scenario_lookup=scenario_lookup)
        assert result["scenario"] == "测试场景 🧪 اختبار"

    def test_normalizes_with_none_values(self):
        a = {
            "id": "TC_1",
            "automatable": None,
            "recommended_tool": None,
            "reason": None
        }
        result = agent.normalize_automation(a, scenario_lookup={})
        assert result["automatable"] == ""
        assert result["recommended_tool"] == ""
        assert result["reason"] == ""

    def test_normalizes_with_numeric_id(self):
        a = {
            "id": 999,
            "automatable": "Yes",
            "recommended_tool": "Selenium",
            "reason": "Stable"
        }
        result = agent.normalize_automation(a, scenario_lookup={})
        assert result["id"] == "999"
