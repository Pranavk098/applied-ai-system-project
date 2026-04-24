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
    outcome: str          # "Win" | "Too High" | "Too Low"
    narration: str
    thinking: list        # observable steps shown in UI
    api_used: bool


def _call_openai(personality: Personality, low: int, high: int, guess: int, outcome: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": personality.system_prompt},
            {
                "role": "user",
                "content": (
                    f"Range: {low}–{high}. My guess: {guess}. Result: {outcome}. "
                    "React in character."
                ),
            },
        ],
        max_tokens=80,
        temperature=0.9,
    )
    return response.choices[0].message.content.strip()


def get_narration(
    personality: Personality,
    low: int,
    high: int,
    guess: int,
    outcome: str,
) -> tuple:
    """Return (narration_text: str, api_was_used: bool).
    Falls back to a canned line if OPENAI_API_KEY is missing or the call fails."""
    if not os.environ.get("OPENAI_API_KEY"):
        return random.choice(personality.fallback_lines), False
    try:
        return _call_openai(personality, low, high, guess, outcome), True
    except Exception:
        return random.choice(personality.fallback_lines), False


def run_agent_turn(state: AgentState, personality: Personality, secret: int) -> TurnResult:
    """Execute one agentic turn. Modifies state in-place. Returns a TurnResult."""
    thinking = []

    # 1. OBSERVE
    thinking.append(f"Observed range: [{state.low}, {state.high}] | Attempts: {state.attempts}")

    # 2. PLAN
    guess = personality.strategy(state.low, state.high, state.history)
    thinking.append(f"Strategy ({personality.name}): chose guess {guess}")

    # 3. ACT
    outcome = check_guess(guess, secret)

    # 4. NARRATE
    narration, api_used = get_narration(personality, state.low, state.high, guess, outcome)
    thinking.append(f'Commentary: "{narration}"')

    # 5. EVALUATE — update range
    if outcome == "Too High":
        state.high = guess - 1
    elif outcome == "Too Low":
        state.low = guess + 1

    state.attempts += 1
    state.history.append(guess)

    if outcome == "Win":
        state.status = "won"

    thinking.append(f"Updated range: [{state.low}, {state.high}]")

    # 6. LOG
    log_turn({
        "personality": personality.key,
        "round": state.attempts,
        "low_before": state.low,
        "high_before": state.high,
        "chosen_guess": guess,
        "result": outcome,
        "narration": narration,
        "api_used": api_used,
    })

    return TurnResult(
        guess=guess,
        outcome=outcome,
        narration=narration,
        thinking=thinking,
        api_used=api_used,
    )
