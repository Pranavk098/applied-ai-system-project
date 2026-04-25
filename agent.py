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
    # Pick a situation-specific fallback line when available
    def _fallback() -> str:
        lines = personality.situation_lines.get(situation) or personality.situation_lines.get("default") or personality.fallback_lines
        return random.choice(lines)

    if not os.environ.get("OPENAI_API_KEY"):
        return _fallback(), False
    try:
        return _call_openai(personality, low, high, guess, outcome, situation, human_last_guess), True
    except Exception:
        return _fallback(), False


def run_agent_turn(
    state: AgentState,
    personality: Personality,
    secret: int,
    human_attempts: int = 0,
    human_last_guess: int | None = None,
) -> TurnResult:
    """Execute one agentic turn. Modifies state in-place. Returns a TurnResult."""
    thinking = []

    # 1. OBSERVE
    thinking.append(f"Range: [{state.low}, {state.high}] | Attempts: {state.attempts}")

    # 2. PLAN
    guess = personality.strategy(state.low, state.high, state.history)
    thinking.append(f"Strategy ({personality.name}): guess {guess}")

    # 3. ACT
    outcome = check_guess(guess, secret)

    # 4. DETECT SITUATION
    situation = _detect_situation(state.attempts, human_attempts, state.low, state.high)

    # 5. NARRATE
    narration, api_used = get_narration(
        personality, state.low, state.high, guess, outcome,
        situation=situation,
        human_last_guess=human_last_guess,
    )
    thinking.append(f'Situation: {situation} | Commentary: "{narration}"')

    # Capture range before mutation so the log is accurate
    low_before = state.low
    high_before = state.high

    # 6. EVALUATE — update range
    if outcome == "Too High":
        state.high = guess - 1
    elif outcome == "Too Low":
        state.low = guess + 1

    state.attempts += 1
    state.history.append(guess)

    if outcome == "Win":
        state.status = "won"

    thinking.append(f"Updated range: [{state.low}, {state.high}]")

    # 7. LOG
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
