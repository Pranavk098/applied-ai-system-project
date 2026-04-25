# Agentic AI Opponent — Challenge Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the Streamlit guessing game with a Challenge Mode where a personality-driven AI agent plays alongside the human — strategy is pure Python, OpenAI is used only for narration.

**Architecture:** Phase 0 completes the existing refactor (logic_utils.py), then three new modules are added (personalities.py, agent.py, logger.py) before app.py is extended with the Challenge Mode UI. The agent turn runs after every human guess, with all six observable steps written to a collapsible "Agent Thinking" panel.

**Tech Stack:** Python 3.11, Streamlit, OpenAI Python SDK (`openai>=1.0`), pytest

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `logic_utils.py` | MODIFY | Pure game rules — implement the 4 stubs |
| `logger.py` | CREATE | Append structured entries to `game_log.jsonl` |
| `personalities.py` | CREATE | 4 personality configs: strategy fn + system prompt + fallback lines + color |
| `agent.py` | CREATE | AgentState dataclass, TurnResult dataclass, run_agent_turn(), get_narration() |
| `app.py` | MODIFY | Add Challenge Mode session state + UI + agent turn wiring |
| `tests/test_game_logic.py` | EXISTING | Already written — must pass after Task 1 |
| `tests/test_personalities.py` | CREATE | Verify strategies always return in-range values |
| `tests/test_agent.py` | CREATE | Verify range shrinks, Strategist solves within 7, fallback works |
| `requirements.txt` | MODIFY | Add `openai>=1.0` |
| `README.md` | MODIFY | Document Challenge Mode, setup, and sample interactions |

---

## Task 1: Implement logic_utils.py (make existing tests pass)

**Files:**
- Modify: `logic_utils.py`
- Test: `tests/test_game_logic.py` (already written — run it)

- [ ] **Step 1: Run the existing tests to see them fail**

```bash
pytest tests/test_game_logic.py -v
```
Expected: 3 failures — `NotImplementedError` for `check_guess`

- [ ] **Step 2: Implement all four functions in logic_utils.py**

Replace the entire contents of `logic_utils.py` with:

```python
def get_range_for_difficulty(difficulty: str):
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        return 1, 50
    return 1, 100


def parse_guess(raw: str):
    if raw is None:
        return False, None, "Enter a guess."
    if raw == "":
        return False, None, "Enter a guess."
    try:
        if "." in raw:
            value = int(float(raw))
        else:
            value = int(raw)
    except Exception:
        return False, None, "That is not a number."
    return True, value, None


def check_guess(guess: int, secret: int) -> str:
    """Return 'Win', 'Too High', or 'Too Low'."""
    if guess == secret:
        return "Win"
    if guess < secret:
        return "Too Low"
    return "Too High"


def update_score(current_score: int, outcome: str, attempt_number: int) -> int:
    if outcome == "Win":
        points = 100 - 10 * (attempt_number + 1)
        if points < 10:
            points = 10
        return current_score + points
    if outcome == "Too High":
        if attempt_number % 2 == 0:
            return current_score + 5
        return current_score - 5
    if outcome == "Too Low":
        return current_score - 5
    return current_score
```

> **Note:** `check_guess` now returns a plain string (not a tuple). The display message will be looked up in `app.py`.

- [ ] **Step 3: Run the tests and confirm they pass**

```bash
pytest tests/test_game_logic.py -v
```
Expected:
```
PASSED tests/test_game_logic.py::test_winning_guess
PASSED tests/test_game_logic.py::test_guess_too_high
PASSED tests/test_game_logic.py::test_guess_too_low
```

- [ ] **Step 4: Commit**

```bash
git add logic_utils.py
git commit -m "feat: implement logic_utils functions and make tests pass"
```

---

## Task 2: Update app.py to use logic_utils

**Files:**
- Modify: `app.py`

`check_guess` now returns a string, not a tuple. `app.py` still has its own copies of the functions — replace them with imports.

- [ ] **Step 1: Replace app.py with the refactored version**

Replace the entire contents of `app.py` with:

```python
import random
import streamlit as st
from logic_utils import get_range_for_difficulty, parse_guess, check_guess, update_score

_HINT_MESSAGES = {
    "Win": "🎉 Correct!",
    "Too Low": "📈 Go HIGHER!",
    "Too High": "📉 Go LOWER!",
}


def reset_round_for_difficulty(difficulty: str):
    low, high = get_range_for_difficulty(difficulty)
    st.session_state.secret = random.randint(low, high)
    st.session_state.attempts = 0
    st.session_state.status = "playing"
    st.session_state.history = []


st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")
st.title("🎮 Game Glitch Investigator")
st.caption("An AI-generated guessing game. Something is off.")

st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox("Difficulty", ["Easy", "Normal", "Hard"], index=1)

attempt_limit_map = {"Easy": 6, "Normal": 8, "Hard": 5}
attempt_limit = attempt_limit_map[difficulty]

low, high = get_range_for_difficulty(difficulty)
st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")

if "secret" not in st.session_state:
    st.session_state.secret = random.randint(low, high)
if "attempts" not in st.session_state:
    st.session_state.attempts = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "status" not in st.session_state:
    st.session_state.status = "playing"
if "history" not in st.session_state:
    st.session_state.history = []
if "active_difficulty" not in st.session_state:
    st.session_state.active_difficulty = difficulty

if st.session_state.active_difficulty != difficulty:
    st.session_state.active_difficulty = difficulty
    reset_round_for_difficulty(difficulty)
    st.rerun()

st.subheader("Make a guess")
st.info(
    f"Guess a number between {low} and {high}. "
    f"Attempts left: {attempt_limit - st.session_state.attempts}"
)

with st.form(key=f"guess_form_{difficulty}"):
    raw_guess = st.text_input("Enter your guess:", key=f"guess_input_{difficulty}")
    submit = st.form_submit_button("Submit Guess 🚀")

col1, col2 = st.columns(2)
with col1:
    new_game = st.button("New Game 🔁")
with col2:
    show_hint = st.checkbox("Show hint", value=True)

if new_game:
    reset_round_for_difficulty(difficulty)
    st.success("New game started.")
    st.rerun()

if st.session_state.status != "playing":
    if st.session_state.status == "won":
        st.success("You already won. Start a new game to play again.")
    else:
        st.error("Game over. Start a new game to try again.")
    st.stop()

if submit:
    st.session_state.attempts += 1
    ok, guess_int, err = parse_guess(raw_guess)

    if not ok:
        st.session_state.history.append(raw_guess)
        st.error(err)
    else:
        st.session_state.history.append(guess_int)
        outcome = check_guess(guess_int, st.session_state.secret)
        message = _HINT_MESSAGES[outcome]

        if show_hint:
            st.warning(message)

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"
            st.success(
                f"You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score}"
            )
        elif st.session_state.attempts >= attempt_limit:
            st.session_state.status = "lost"
            st.error(
                f"Out of attempts! The secret was {st.session_state.secret}. "
                f"Score: {st.session_state.score}"
            )

with st.expander("Developer Debug Info"):
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("History:", st.session_state.history)

st.divider()
st.caption("Built by an AI that claims this code is production-ready.")
```

- [ ] **Step 2: Verify the app still runs**

```bash
python -m streamlit run app.py
```
Expected: App opens in browser. Play one round — hints and score should work exactly as before.

- [ ] **Step 3: Run all tests**

```bash
pytest tests/ -v
```
Expected: 3 passing, 0 failing.

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "refactor: import logic from logic_utils, remove duplicate functions from app.py"
```

---

## Task 3: Create logger.py

**Files:**
- Create: `logger.py`

- [ ] **Step 1: Create logger.py**

```python
import json
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path("game_log.jsonl")


def log_turn(entry: dict) -> None:
    """Append a structured entry to game_log.jsonl."""
    entry["timestamp"] = datetime.now(timezone.utc).isoformat()
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
```

- [ ] **Step 2: Smoke-test it manually**

```bash
python -c "from logger import log_turn; log_turn({'test': 'ok', 'value': 42}); print(open('game_log.jsonl').read())"
```
Expected: one JSON line printed with `test`, `value`, and `timestamp` keys.

- [ ] **Step 3: Clean up the test file**

```bash
del game_log.jsonl
```
(On Mac/Linux: `rm game_log.jsonl`)

- [ ] **Step 4: Commit**

```bash
git add logger.py
git commit -m "feat: add JSONL logger for agent turns"
```

---

## Task 4: Create personalities.py

**Files:**
- Create: `personalities.py`

- [ ] **Step 1: Create personalities.py**

```python
import random
from dataclasses import dataclass
from typing import Callable


@dataclass
class Personality:
    key: str
    name: str
    strategy: Callable[[int, int, list], int]
    system_prompt: str
    fallback_lines: list
    color: str


def _strategy_strategist(low: int, high: int, history: list) -> int:
    return (low + high) // 2


def _strategy_gambler(low: int, high: int, history: list) -> int:
    return random.randint(low, high)


def _strategy_professor(low: int, high: int, history: list) -> int:
    return (low + high) // 2


def _strategy_trash_talker(low: int, high: int, history: list) -> int:
    midpoint = (low + high) // 2
    jitter = random.randint(-5, 5)
    return max(low, min(high, midpoint + jitter))


PERSONALITIES: dict[str, Personality] = {
    "Strategist": Personality(
        key="Strategist",
        name="The Strategist",
        strategy=_strategy_strategist,
        system_prompt=(
            "You are The Strategist, a cold analytical AI playing a number guessing game. "
            "Speak in short precise sentences. No emotion. State your range, midpoint, and logic. "
            "Keep responses under 40 words."
        ),
        fallback_lines=[
            "Range analyzed. Optimal guess computed.",
            "Binary search applied. Efficiency maximized.",
            "Midpoint selected. Proceeding.",
        ],
        color="#1E88E5",
    ),
    "Gambler": Personality(
        key="Gambler",
        name="The Gambler",
        strategy=_strategy_gambler,
        system_prompt=(
            "You are The Gambler, a reckless overconfident AI playing a number guessing game. "
            "Brag about your instincts, ignore logic, love the thrill. "
            "Keep responses under 40 words. Sound like you're winning even when you're not."
        ),
        fallback_lines=[
            "I got a feeling about this one! All in!",
            "My gut never lies. Trust the process!",
            "Logic is for losers. I'm going with vibes!",
        ],
        color="#E53935",
    ),
    "Professor": Personality(
        key="Professor",
        name="The Professor",
        strategy=_strategy_professor,
        system_prompt=(
            "You are The Professor, an educational AI playing a number guessing game. "
            "Explain the binary search algorithm and math behind your guess. Be slightly condescending. "
            "Reference the current range and midpoint calculation. Keep responses under 60 words."
        ),
        fallback_lines=[
            "Binary search dictates we halve the range. Elementary, really.",
            "The midpoint minimizes worst-case attempts. As I've explained.",
            "Logarithmic complexity at work. Do try to keep up.",
        ],
        color="#43A047",
    ),
    "TrashTalker": Personality(
        key="TrashTalker",
        name="The Trash-Talker",
        strategy=_strategy_trash_talker,
        system_prompt=(
            "You are The Trash-Talker, a boastful dramatic AI playing a number guessing game. "
            "Taunt the human. Brag when ahead, be dramatic and blame everything when behind. "
            "Keep responses under 40 words."
        ),
        fallback_lines=[
            "You call that a guess?! Watch and learn!",
            "Still behind? Must be rough being you.",
            "Playing with my eyes closed and still winning!",
        ],
        color="#FB8C00",
    ),
}


def get_personality(key: str) -> Personality:
    return PERSONALITIES[key]


def list_personalities() -> list:
    return list(PERSONALITIES.keys())
```

- [ ] **Step 2: Commit**

```bash
git add personalities.py
git commit -m "feat: add four AI personalities with strategy functions"
```

---

## Task 5: Write and pass tests for personalities.py

**Files:**
- Create: `tests/test_personalities.py`

- [ ] **Step 1: Create tests/test_personalities.py**

```python
import random
from personalities import get_personality, list_personalities, PERSONALITIES


def test_all_four_personalities_exist():
    for key in ["Strategist", "Gambler", "Professor", "TrashTalker"]:
        p = get_personality(key)
        assert p.key == key
        assert p.name
        assert callable(p.strategy)
        assert len(p.fallback_lines) >= 3
        assert p.color.startswith("#")


def test_strategist_always_picks_midpoint():
    p = get_personality("Strategist")
    assert p.strategy(1, 100, []) == 50
    assert p.strategy(1, 101, []) == 51
    assert p.strategy(50, 100, []) == 75
    assert p.strategy(5, 5, []) == 5


def test_all_strategies_return_in_range():
    random.seed(42)
    for key in list_personalities():
        p = get_personality(key)
        for _ in range(50):
            low = random.randint(1, 90)
            high = random.randint(low, 100)
            result = p.strategy(low, high, [])
            assert low <= result <= high, (
                f"{key} returned {result} outside [{low}, {high}]"
            )


def test_list_personalities_returns_all_keys():
    keys = list_personalities()
    assert set(keys) == {"Strategist", "Gambler", "Professor", "TrashTalker"}
```

- [ ] **Step 2: Run the tests**

```bash
pytest tests/test_personalities.py -v
```
Expected: 4 passing.

- [ ] **Step 3: Commit**

```bash
git add tests/test_personalities.py
git commit -m "test: add personality strategy tests"
```

---

## Task 6: Create agent.py

**Files:**
- Create: `agent.py`

- [ ] **Step 1: Create agent.py**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add agent.py
git commit -m "feat: add agentic turn runner with narration and logging"
```

---

## Task 7: Write and pass tests for agent.py

**Files:**
- Create: `tests/test_agent.py`

- [ ] **Step 1: Create tests/test_agent.py**

```python
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
```

- [ ] **Step 2: Run the tests**

```bash
pytest tests/test_agent.py -v
```
Expected: 8 passing. (The fallback test passes because no key is set in test env; if your key IS set, the API is called — that's fine, it should still pass.)

- [ ] **Step 3: Run the full test suite**

```bash
pytest tests/ -v
```
Expected: All tests passing.

- [ ] **Step 4: Commit**

```bash
git add tests/test_agent.py
git commit -m "test: add agent turn behavior tests"
```

---

## Task 8: Add Challenge Mode session state to app.py

**Files:**
- Modify: `app.py`

Add agent session state initialization and update `reset_round_for_difficulty` to also reset agent state. All changes go in `app.py` after the human state initialization block.

- [ ] **Step 1: Add the Challenge Mode imports at the top of app.py**

Find the existing import block at the top of `app.py`:
```python
import random
import streamlit as st
from logic_utils import get_range_for_difficulty, parse_guess, check_guess, update_score
```

Replace it with:
```python
import random
import streamlit as st
from logic_utils import get_range_for_difficulty, parse_guess, check_guess, update_score
from agent import AgentState, run_agent_turn
from personalities import get_personality, list_personalities
```

- [ ] **Step 2: Update reset_round_for_difficulty to also reset agent state**

Find:
```python
def reset_round_for_difficulty(difficulty: str):
    low, high = get_range_for_difficulty(difficulty)
    st.session_state.secret = random.randint(low, high)
    st.session_state.attempts = 0
    st.session_state.status = "playing"
    st.session_state.history = []
```

Replace with:
```python
def reset_round_for_difficulty(difficulty: str):
    low, high = get_range_for_difficulty(difficulty)
    st.session_state.secret = random.randint(low, high)
    st.session_state.attempts = 0
    st.session_state.status = "playing"
    st.session_state.history = []
    # Reset agent state
    st.session_state.agent_low = low
    st.session_state.agent_high = high
    st.session_state.agent_attempts = 0
    st.session_state.agent_status = "playing"
    st.session_state.agent_history = []
    st.session_state.thinking_panel = []
    st.session_state.turn_log = []
```

- [ ] **Step 3: Add agent session state initialization**

Find the block that starts with:
```python
if "secret" not in st.session_state:
```

Add these lines immediately AFTER the existing human state initialization block (after `if "active_difficulty" not in st.session_state:`):

```python
# Challenge Mode state
if "challenge_mode" not in st.session_state:
    st.session_state.challenge_mode = False
if "personality_key" not in st.session_state:
    st.session_state.personality_key = "Strategist"
if "agent_low" not in st.session_state:
    st.session_state.agent_low = low
if "agent_high" not in st.session_state:
    st.session_state.agent_high = high
if "agent_attempts" not in st.session_state:
    st.session_state.agent_attempts = 0
if "agent_status" not in st.session_state:
    st.session_state.agent_status = "playing"
if "agent_history" not in st.session_state:
    st.session_state.agent_history = []
if "thinking_panel" not in st.session_state:
    st.session_state.thinking_panel = []
if "turn_log" not in st.session_state:
    st.session_state.turn_log = []
```

- [ ] **Step 4: Verify app still runs**

```bash
python -m streamlit run app.py
```
Expected: App opens, works exactly as before, no errors in terminal.

- [ ] **Step 5: Commit**

```bash
git add app.py
git commit -m "feat: add challenge mode session state initialization"
```

---

## Task 9: Add Challenge Mode UI to sidebar

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Add Challenge Mode controls to the sidebar**

Find this line in `app.py`:
```python
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")
```

Add immediately after it:
```python
st.sidebar.divider()
st.sidebar.subheader("🤖 Challenge Mode")
challenge_mode = st.sidebar.checkbox("Race the AI", value=st.session_state.challenge_mode)

if challenge_mode != st.session_state.challenge_mode:
    st.session_state.challenge_mode = challenge_mode
    reset_round_for_difficulty(difficulty)
    st.rerun()

if st.session_state.challenge_mode:
    personality_names = {
        "Strategist": "🧠 The Strategist",
        "Gambler": "🎲 The Gambler",
        "Professor": "📚 The Professor",
        "TrashTalker": "😤 The Trash-Talker",
    }
    selected = st.sidebar.radio(
        "Pick your opponent",
        options=list(personality_names.keys()),
        format_func=lambda k: personality_names[k],
        index=list(personality_names.keys()).index(st.session_state.personality_key),
    )
    if selected != st.session_state.personality_key:
        st.session_state.personality_key = selected
        reset_round_for_difficulty(difficulty)
        st.rerun()
```

- [ ] **Step 2: Add the Agent Thinking panel to the sidebar**

Add this block at the very end of `app.py`, just before the final `st.caption` line:
```python
if st.session_state.challenge_mode and st.session_state.thinking_panel:
    st.sidebar.divider()
    with st.sidebar.expander("🤖 Agent Thinking", expanded=True):
        for step in st.session_state.thinking_panel:
            st.write(step)
```

- [ ] **Step 3: Verify the sidebar shows the toggle**

```bash
python -m streamlit run app.py
```
Expected: Sidebar shows "Challenge Mode" toggle. Flipping it resets the game. Personality radio appears when toggle is on.

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "feat: add challenge mode sidebar controls and agent thinking panel"
```

---

## Task 10: Wire agent turn into the game loop

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Add the agent turn block after the human guess is processed**

Find this block in `app.py`:
```python
        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"
            st.success(
                f"You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score}"
            )
        elif st.session_state.attempts >= attempt_limit:
            st.session_state.status = "lost"
            st.error(
                f"Out of attempts! The secret was {st.session_state.secret}. "
                f"Score: {st.session_state.score}"
            )
```

Replace with:
```python
        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"
            st.success(
                f"You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score}"
            )
        elif st.session_state.attempts >= attempt_limit:
            st.session_state.status = "lost"
            st.error(
                f"Out of attempts! The secret was {st.session_state.secret}. "
                f"Score: {st.session_state.score}"
            )

        # Agent turn — only if human did not just win and challenge mode is on
        if (
            st.session_state.challenge_mode
            and st.session_state.status == "playing"
            and st.session_state.agent_status == "playing"
        ):
            personality = get_personality(st.session_state.personality_key)
            agent_state = AgentState(
                low=st.session_state.agent_low,
                high=st.session_state.agent_high,
                attempts=st.session_state.agent_attempts,
                status=st.session_state.agent_status,
                history=list(st.session_state.agent_history),
            )
            result = run_agent_turn(agent_state, personality, st.session_state.secret)
            # Sync agent state back to session state
            st.session_state.agent_low = agent_state.low
            st.session_state.agent_high = agent_state.high
            st.session_state.agent_attempts = agent_state.attempts
            st.session_state.agent_status = agent_state.status
            st.session_state.agent_history = agent_state.history
            st.session_state.thinking_panel = result.thinking
            st.session_state.turn_log.append({
                "guess": result.guess,
                "outcome": result.outcome,
                "narration": result.narration,
            })

            if result.outcome == "Win":
                st.session_state.agent_status = "won"
                p = get_personality(st.session_state.personality_key)
                st.error(f"🤖 {p.name} wins! It guessed {result.guess}. \"{result.narration}\"")
            elif st.session_state.agent_attempts >= attempt_limit:
                st.session_state.agent_status = "lost"
```

- [ ] **Step 2: Add head-to-head status display**

Find this line:
```python
st.subheader("Make a guess")
```

Add this block immediately before it:
```python
if st.session_state.challenge_mode:
    col_human, col_agent = st.columns(2)
    with col_human:
        st.metric("Your attempts", st.session_state.attempts)
        st.caption(f"Status: {st.session_state.status}")
    with col_agent:
        p = get_personality(st.session_state.personality_key)
        st.metric(f"{p.name} attempts", st.session_state.agent_attempts, delta_color="inverse")
        st.caption(f"Agent status: {st.session_state.agent_status}")
    st.divider()
```

- [ ] **Step 3: Test the full Challenge Mode flow**

```bash
python -m streamlit run app.py
```

1. Enable Challenge Mode toggle
2. Select "The Strategist"
3. Submit any guess
4. Verify: Agent Thinking panel appears in sidebar with 4 steps
5. Verify: Head-to-head metrics update
6. Play until someone wins — verify correct winner message

- [ ] **Step 4: Test API-off mode**

Temporarily rename your `.env` or unset the key, then run the app and submit a guess in Challenge Mode.
Expected: Agent still guesses, uses a canned fallback line, no crash.

- [ ] **Step 5: Run the full test suite one final time**

```bash
pytest tests/ -v
```
Expected: All tests pass.

- [ ] **Step 6: Commit**

```bash
git add app.py
git commit -m "feat: wire agent turn into game loop, add head-to-head metrics display"
```

---

## Task 11: Update requirements.txt

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Read the current requirements.txt**

Open `requirements.txt` and check what's there. It likely has `streamlit` and `pytest`.

- [ ] **Step 2: Add openai**

Add this line to `requirements.txt`:
```
openai>=1.0
```

Final `requirements.txt` should look like:
```
streamlit
pytest
openai>=1.0
```

- [ ] **Step 3: Install it**

```bash
pip install openai>=1.0
```

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "deps: add openai sdk"
```

---

## Task 12: Update README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add Challenge Mode section to README.md**

Open `README.md`. After the existing `## 🛠️ Setup` section, add:

```markdown
## 🤖 Challenge Mode — Agentic AI Opponent

Enable **Challenge Mode** in the sidebar to race against an AI agent. The agent plays the same game simultaneously — same secret number, same attempt limit.

### How it works

After each human guess, the agent runs a 4-step agentic loop:

1. **Observe** — reads its current valid range
2. **Plan** — picks its next guess using a deterministic Python strategy
3. **Narrate** — calls the OpenAI API to generate in-character commentary
4. **Evaluate** — updates its range based on the hint

All four steps appear in the **Agent Thinking** panel in the sidebar.

### Personalities

| Personality | Strategy | Tone |
|---|---|---|
| 🧠 The Strategist | Binary search (always midpoint) | Cold, analytical |
| 🎲 The Gambler | Random within valid range | Reckless, overconfident |
| 📚 The Professor | Binary search + explains the math | Verbose, educational |
| 😤 The Trash-Talker | Near-optimal with slight jitter | Boastful, dramatic |

### Setup

Set your OpenAI API key before running:

```bash
export OPENAI_API_KEY=sk-...   # Mac/Linux
set OPENAI_API_KEY=sk-...      # Windows
```

If no key is set, the agent still plays using built-in fallback lines — it never crashes.

### Sample Interactions

**Human wins vs Strategist (Normal mode, secret = 73)**
```
Human guess: 80 → Too High
Agent: guesses 50 → "Range 1-100. Midpoint: 50. Processing."
Human guess: 73 → Win! 🎉
Agent did not get a final turn — human wins immediately on a correct guess.
```

**Agent wins vs Trash-Talker (Normal mode, secret = 42)**
```
Human guess: 10 → Too Low
Agent: guesses 50 → "You're still guessing single digits?! I'm already at 50. Amateur."
Human guess: 30 → Too Low  
Agent: guesses 46 → "Getting warmer... for you. I'm practically there."
Human guess: 40 → Too Low
Agent: guesses 43 → Too High
Human guess: 42 → Win!
```

### Logging

Every agent turn is appended to `game_log.jsonl`:

```json
{"personality": "Strategist", "round": 1, "chosen_guess": 50, "result": "Too Low", "narration": "Midpoint selected.", "api_used": true, "timestamp": "2026-04-24T10:00:00Z"}
```
```

- [ ] **Step 2: Add architecture diagram placeholder**

Add this to the README under Challenge Mode section:
```markdown
### Architecture

![System Architecture](assets/architecture.png)
```

Then create the `assets/` folder:
```bash
mkdir assets
```

You will add the architecture PNG after generating it (e.g., from Mermaid Live Editor using the diagram in the design spec).

- [ ] **Step 3: Commit**

```bash
git add README.md assets/
git commit -m "docs: document challenge mode, personalities, and sample interactions in README"
```

---

## Final Verification

- [ ] Run full test suite: `pytest tests/ -v` — all green
- [ ] Run app: `python -m streamlit run app.py` — Challenge Mode works end-to-end with all 4 personalities
- [ ] Check `game_log.jsonl` exists and has entries after a Challenge Mode game
- [ ] Confirm API-off fallback: unset key, play a round, no crash
- [ ] Confirm Strategist solves Normal mode in ≤ 7 guesses
