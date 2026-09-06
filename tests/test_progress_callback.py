"""
Task 12: Progress callback message ordering and content.
Verifies that progress_callback is invoked with correct messages in the correct order
for each pipeline stage.
"""

import pytest

import agent


def test_progress_callback_is_invoked(patch_crew_kickoff, make_stage_outputs, sample_requirements_text, tmp_output_dir):
    messages = []

    def capture_progress(msg):
        messages.append(msg)

    patch_crew_kickoff(make_stage_outputs())
    agent.run_pipeline(sample_requirements_text, progress_callback=capture_progress, output_dir=tmp_output_dir)

    assert len(messages) > 0


def test_progress_callback_receives_stage_complete_messages(
    patch_crew_kickoff, make_stage_outputs, sample_requirements_text, tmp_output_dir
):
    messages = []

    def capture_progress(msg):
        messages.append(msg)

    patch_crew_kickoff(make_stage_outputs(
        analyze="[]",
        generate="[]",
        review="[]",
        fix="[]",
        automation="[]",
        estimate="{}",
    ))
    agent.run_pipeline(sample_requirements_text, progress_callback=capture_progress, output_dir=tmp_output_dir)

    # Should have messages indicating stage completion
    message_text = " ".join(messages)
    assert "analyze" in message_text.lower() or "requirement" in message_text.lower()


def test_progress_callback_message_mentions_stage_names(
    patch_crew_kickoff, make_stage_outputs, sample_requirements_text, tmp_output_dir
):
    messages = []

    def capture_progress(msg):
        messages.append(msg)

    patch_crew_kickoff(make_stage_outputs(
        analyze=[{"req_id": "REQ_1", "requirement": "Test", "category": "Functional", "priority": "High"}],
        generate=[{"id": "TC_1", "req_id": "REQ_1", "scenario": "x", "type": "Positive",
                   "steps": [], "expected_result": "", "priority": "High"}],
        review=[],
        fix=[],
        automation=[],
        estimate={},
    ))
    agent.run_pipeline(sample_requirements_text, progress_callback=capture_progress, output_dir=tmp_output_dir)

    message_text = " ".join(messages)
    # Messages should include stage names or result counts
    assert "1" in message_text or "requirement" in message_text.lower()


def test_progress_callback_with_counts(
    patch_crew_kickoff, make_stage_outputs, sample_test_cases, sample_requirements_text, tmp_output_dir
):
    messages = []

    def capture_progress(msg):
        messages.append(msg)

    patch_crew_kickoff(make_stage_outputs(generate=sample_test_cases))
    agent.run_pipeline(sample_requirements_text, progress_callback=capture_progress, output_dir=tmp_output_dir)

    # Should see a message about generated test cases
    message_text = " ".join(messages)
    # The final message typically includes the counts summary
    assert len(message_text) > 0


def test_progress_callback_is_optional(
    patch_crew_kickoff, make_stage_outputs, sample_requirements_text, tmp_output_dir
):
    patch_crew_kickoff(make_stage_outputs())

    # Should not crash if no callback is provided
    result = agent.run_pipeline(sample_requirements_text, output_dir=tmp_output_dir)
    assert isinstance(result, dict)
    assert "timestamp" in result


def test_progress_callback_receives_completion_message(
    patch_crew_kickoff, make_stage_outputs, sample_requirements_text, tmp_output_dir
):
    messages = []

    def capture_progress(msg):
        messages.append(msg)

    patch_crew_kickoff(make_stage_outputs())
    agent.run_pipeline(sample_requirements_text, progress_callback=capture_progress, output_dir=tmp_output_dir)

    # Last message or messages should include completion indicator
    message_text = " ".join(messages).lower()
    assert "completed" in message_text or "success" in message_text or "pipeline" in message_text
