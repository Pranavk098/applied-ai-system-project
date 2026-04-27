import os
import pytest
from agent import AgentState, TurnResult, run_agent_turn, get_narration
from personalities import get_personality


def test_strategist_guesses_midpoint():
    personality = get_personality("Strategist")
    state = AgentState(low=1, high=100)
    # Secret = 99 so midpoint 50 is Too Low
    result = run_agent_turn(state, personality, secret=99)
    assert result.guess == 50


def test_guess_always_in_range():
    personality = get_personality("TrashTalker")
    for i in range(20):
        low, high = 30, 70
        state = AgentState(low=low, high=high)
        result = run_agent_turn(state, personality, secret=99)
        assert low <= result.guess <= high, f"Guess {result.guess} outside [{low}, {high}]"


def test_range_shrinks_after_too_high():
    personality = get_personality("Strategist")
    state = AgentState(low=1, high=100)
    # midpoint=50, secret=1 → Too High → high should drop to 49
    run_agent_turn(state, personality, secret=1)
    assert state.high == 49


def test_range_shrinks_after_too_low():
    personality = get_personality("Strategist")
    state = AgentState(low=1, high=100)
    # midpoint=50, secret=100 → Too Low → low should rise to 51
    run_agent_turn(state, personality, secret=100)
    assert state.low == 51


def test_strategist_solves_normal_within_7():
    personality = get_personality("Strategist")
    for secret in [1, 25, 50, 73, 100]:
        state = AgentState(low=1, high=100)
        for _ in range(7):
            if state.status == "won":
                break
            run_agent_turn(state, personality, secret=secret)
        assert state.status == "won", f"Strategist failed to solve secret={secret} in 7 guesses"


def test_win_sets_status():
    personality = get_personality("Strategist")
    state = AgentState(low=50, high=50)
    result = run_agent_turn(state, personality, secret=50)
    assert result.outcome == "Win"
    assert state.status == "won"


def test_turn_result_has_thinking_steps():
    personality = get_personality("Professor")
    state = AgentState(low=1, high=100)
    result = run_agent_turn(state, personality, secret=99, log=False)
    assert len(result.thinking) >= 5
    step_names = {s["step"] for s in result.thinking}
    assert step_names >= {"observe", "plan", "act", "assess", "narrate", "evaluate"}
    for step in result.thinking:
        assert "step" in step
        assert "output" in step


def test_fallback_narration_when_no_api_key():
    personality = get_personality("Strategist")
    original = os.environ.pop("OPENAI_API_KEY", None)
    try:
        narration, api_used = get_narration(personality, 1, 100, 50, "Too Low")
    finally:
        if original:
            os.environ["OPENAI_API_KEY"] = original
    assert isinstance(narration, str)
    assert len(narration) > 0
    assert api_used is False


def test_log_flag_suppresses_file_write(tmp_path, monkeypatch):
    import logger
    tmp_log = tmp_path / "test_game_log.jsonl"
    monkeypatch.setattr(logger, "LOG_PATH", tmp_log)

    personality = get_personality("Strategist")

    # Confirm the redirect works — log=True should produce a file
    state = AgentState(low=1, high=100)
    run_agent_turn(state, personality, secret=50, log=True)
    assert tmp_log.exists(), "log=True should write to the log file"

    # Now confirm log=False suppresses it
    tmp_log.unlink()
    state2 = AgentState(low=1, high=100)
    run_agent_turn(state2, personality, secret=50, log=False)
    assert not tmp_log.exists(), "log=False should not write to game_log.jsonl"


def test_fallback_deduplication_avoids_recent_line():
    """When all-but-one lines are in recent history, the remaining line is always chosen."""
    personality = get_personality("Strategist")
    ahead_lines = personality.situation_lines["ahead"]   # 3 lines
    recent = ahead_lines[:2]                             # mark first 2 as recent
    for _ in range(30):
        narration, _ = get_narration(
            personality, 1, 100, 50, "Too Low",
            situation="ahead", recent_narrations=recent,
        )
        assert narration == ahead_lines[2], (
            f"Expected only the non-recent line but got: {narration}"
        )


def test_fallback_deduplication_resets_when_all_lines_exhausted():
    """When every line is in recent history the function still returns a valid string."""
    personality = get_personality("Strategist")
    all_ahead = personality.situation_lines["ahead"]
    for _ in range(10):
        narration, _ = get_narration(
            personality, 1, 100, 50, "Too Low",
            situation="ahead", recent_narrations=list(all_ahead),
        )
        assert isinstance(narration, str) and len(narration) > 0
