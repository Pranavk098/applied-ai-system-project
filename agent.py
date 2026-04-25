import os
import random
from dataclasses import dataclass, field

from logic_utils import check_guess
from logger import log_turn
from personalities import Personality


@dataclass
class AgentState:
    low: int
    high: int
    attempts: int = 0
    status: str = "playing"  # "playing" | "won" | "lost"
    history: list = field(default_factory=list)


@dataclass
class TurnResult:
    guess: int
    outcome: str       # "Win" | "Too High" | "Too Low"
    narration: str
    thinking: list     # internal steps (used for logging, not displayed to player)
    api_used: bool


def _detect_situation(agent_attempts: int, human_attempts: int, low: int, high: int) -> str:
    if agent_attempts == 0:
        return "opening"
    range_size = high - low + 1
    if range_size <= 3:
        return "closing_in"
    if agent_attempts < human_attempts:
        return "ahead"
    if agent_attempts > human_attempts:
        return "behind"
    return "tied"


def _call_openai(
    personality: Personality,
    low: int,
    high: int,
    guess: int,
    outcome: str,
    situation: str,
    human_last_guess: int | None,
) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    context = f"I guessed {guess} (range was {low}–{high}). Result: {outcome}."
    if situation == "opening":
        context += " This is my first guess."
    elif situation == "closing_in":
        context += f" I've narrowed it to just {high - low + 1} possible numbers."
    elif situation == "ahead":
        context += " I'm ahead — fewer guesses than the human."
    elif situation == "behind":
        context += " I'm behind — more guesses than the human."
    if human_last_guess is not None:
        context += f" The human just guessed {human_last_guess}."
    context += " React in character, addressing the human player directly. Under 30 words."

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": personality.system_prompt},
            {"role": "user", "content": context},
        ],
        max_tokens=60,
        temperature=0.95,
    )
    return response.choices[0].message.content.strip()


def get_narration(
    personality: Personality,
    low: int,
    high: int,
    guess: int,
    outcome: str,
    situation: str = "",
    human_last_guess: int | None = None,
) -> tuple:
    """Return (narration_text, api_was_used). Falls back to canned line if API unavailable."""
    def _fallback() -> str:
        lines = personality.situation_lines.get(situation) or personality.situation_lines.get("default") or personality.fallback_lines
        return random.choice(lines)

    if not os.environ.get("OPENAI_API_KEY"):
        return _fallback(), False
    try:
        return _call_openai(personality, low, high, guess, outcome, situation, human_last_guess), True
    except Exception:
        return _fallback(), False


# ── Named step functions ───────────────────────────────────────────────────────

def _observe(state: AgentState) -> dict:
    return {"step": "observe", "output": {"range": [state.low, state.high], "attempts": state.attempts}}


def _plan(personality: Personality, state: AgentState) -> dict:
    guess = personality.strategy(state.low, state.high, state.history)
    return {"step": "plan", "output": {"guess": guess, "reason": personality.key}}


def _act(guess: int, secret: int) -> dict:
    outcome = check_guess(guess, secret)
    return {"step": "act", "output": {"guess": guess, "outcome": outcome}}


def _assess(state: AgentState, human_attempts: int) -> dict:
    situation = _detect_situation(state.attempts, human_attempts, state.low, state.high)
    return {"step": "assess", "output": {"situation": situation}}


def _narrate(personality: Personality, state: AgentState, guess: int, outcome: str, situation: str, human_last_guess: int | None) -> dict:
    narration, api_used = get_narration(
        personality, state.low, state.high, guess, outcome,
        situation=situation, human_last_guess=human_last_guess,
    )
    return {"step": "narrate", "output": {"narration": narration, "api_used": api_used}}


def _evaluate(state: AgentState, guess: int, outcome: str) -> dict:
    if outcome == "Too High":
        state.high = guess - 1
    elif outcome == "Too Low":
        state.low = guess + 1
    state.attempts += 1
    state.history.append(guess)
    if outcome == "Win":
        state.status = "won"
    return {"step": "evaluate", "output": {"low": state.low, "high": state.high}}


# ── Main agent turn ────────────────────────────────────────────────────────────

def run_agent_turn(
    state: AgentState,
    personality: Personality,
    secret: int,
    human_attempts: int = 0,
    human_last_guess: int | None = None,
    log: bool = True,
) -> TurnResult:
    """Execute one agentic turn. Modifies state in-place. Returns a TurnResult."""
    # Capture range before mutation so the log records state at decision time
    low_before = state.low
    high_before = state.high

    obs  = _observe(state)
    plan = _plan(personality, state)
    guess = plan["output"]["guess"]

    act = _act(guess, secret)
    outcome = act["output"]["outcome"]

    # _assess must run before _evaluate: _detect_situation uses pre-increment state.attempts
    assess = _assess(state, human_attempts)
    situation = assess["output"]["situation"]

    nar = _narrate(personality, state, guess, outcome, situation, human_last_guess)
    narration = nar["output"]["narration"]
    api_used  = nar["output"]["api_used"]

    ev = _evaluate(state, guess, outcome)

    thinking = [obs, plan, act, assess, nar, ev]

    if log:
        log_turn({
            "personality": personality.key,
            "round": state.attempts,
            "low_before": low_before,
            "high_before": high_before,
            "chosen_guess": guess,
            "result": outcome,
            "narration": narration,
            "api_used": api_used,
            "situation": situation,
        })

    return TurnResult(
        guess=guess,
        outcome=outcome,
        narration=narration,
        thinking=thinking,
        api_used=api_used,
    )
