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
    result = run_agent_turn(state, personality, secret=99)
    assert len(result.thinking) >= 3
    for step in result.thinking:
        assert isinstance(step, str)
        assert len(step) > 0


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
    from logger import LOG_PATH
    import logger
    # Redirect log path to a temp file
    tmp_log = tmp_path / "test_game_log.jsonl"
    monkeypatch.setattr(logger, "LOG_PATH", tmp_log)

    personality = get_personality("Strategist")
    state = AgentState(low=1, high=100)
    run_agent_turn(state, personality, secret=50, log=False)

    assert not tmp_log.exists(), "log=False should not write to game_log.jsonl"
