# Design Spec: Agentic AI Opponent — "Challenge Mode"
**Date:** 2026-04-24  
**Project:** Game Glitch Investigator (Project4 → Applied AI System)  
**AI Feature:** Agentic Workflow  
**Status:** Approved

---

## 1. Overview

Extend the existing Streamlit number guessing game with a **Challenge Mode** where an AI agent plays the same game simultaneously with the human player. The AI uses a **deterministic Python strategy** to pick guesses and calls the **OpenAI API only for narration** — the personality voice. This separation keeps gameplay reliable, testable, and bounded while still delivering visible agentic behavior and compelling commentary.

The human and agent race to guess the same secret number. Whoever guesses correctly first wins.

---

## 2. Core Principle

> **The LLM is the voice, not the decision-maker.**

- Strategy (what to guess next) → pure Python, deterministic
- Narration (how to express it) → OpenAI API, personality-driven
- If OpenAI is unavailable → canned fallback lines, game still runs

---

## 3. Phase 0: Finish the Refactor First

Before adding any new features, complete the existing unfinished refactor:

- Move all game logic functions from `app.py` into `logic_utils.py` (currently stubbed with `NotImplementedError`)
- Functions to move: `get_range_for_difficulty`, `parse_guess`, `check_guess`, `update_score`
- `app.py` should import from `logic_utils.py` after this step
- All existing `pytest` tests must pass before Phase 1 begins
- This gives `agent.py` a stable, tested foundation to depend on

---

## 4. AI Personalities

Four selectable personalities. Each is a config with: strategy function, system prompt, canned fallback lines, and UI accent color.

| Personality | Strategy | Tone | Color |
|---|---|---|---|
| **The Strategist** | Pure binary search (always midpoint) | Cold, analytical, no emotion | Blue |
| **The Gambler** | Random within range, skewed toward extremes | Overconfident, reckless | Red |
| **The Professor** | Binary search + explains the math | Verbose, educational, mildly condescending | Green |
| **The Trash-Talker** | Near-optimal but adds ±5 random jitter, clamped to [low, high] | Boastful when ahead, dramatic when losing | Orange |

Strategy functions are pure Python — they take `(low, high, history)` and return an `int` guaranteed to be within `[low, high]`. They never call OpenAI. The Trash-Talker applies jitter then clamps: `max(low, min(high, midpoint + jitter))`.

---

## 5. Agentic Loop (Per Turn)

After the human submits a guess, the agent executes this observable loop:

```
1. OBSERVE   → read current [low, high] and agent guess history
2. PLAN      → call strategy function → pick next_guess (Python only)
3. NARRATE   → call OpenAI API with system prompt + observed state → stream commentary
4. ACT       → evaluate next_guess against secret (via check_guess from logic_utils)
5. EVALUATE  → update [low, high] based on result (Too High / Too Low)
6. LOG       → append structured entry to game_log.jsonl
```

The UI renders all six steps in a collapsible **"Agent Thinking"** panel in the sidebar. Labels used:
- Observed state
- Chosen strategy
- Next guess
- Commentary

This avoids the phrase "chain-of-thought" (which overpromises) while still showing full transparency.

---

## 6. Win Condition

- Human submits their guess first each round
- If the human guesses correctly → **round ends immediately**, agent does not get a response turn
- If the agent guesses correctly on its turn → agent wins, human's remaining turns are locked
- Ties are impossible because the human always goes first

---

## 7. Module Boundaries

```
logic_utils.py    ← Pure game rules (no Streamlit, no OpenAI)
                     get_range_for_difficulty, parse_guess, check_guess, update_score

agent.py          ← Agentic turn execution and agent state updates (no Streamlit UI code)
                     AgentState dataclass, run_agent_turn(state, personality, secret) → TurnResult

personalities.py  ← Personality configs: strategy function + system prompt + fallback lines + theme color

logger.py         ← JSONL append helper: log_turn(entry: dict) → writes to game_log.jsonl

app.py            ← Streamlit rendering and control flow only
                     Imports from all of the above, owns st.session_state
```

`agent.py` has zero Streamlit imports. It is a plain Python module that accepts state and returns results.

---

## 8. Session State Layout

All mutable game state lives in `st.session_state` to survive Streamlit reruns:

```python
# Human game state
st.session_state.secret          # int: the secret number
st.session_state.attempts        # int: human attempt count
st.session_state.score           # int: human score
st.session_state.status          # str: "playing" | "won" | "lost"
st.session_state.history         # list: human guess history

# Agent game state
st.session_state.agent_low       # int: agent's current range low
st.session_state.agent_high      # int: agent's current range high
st.session_state.agent_attempts  # int: agent attempt count
st.session_state.agent_status    # str: "playing" | "won" | "lost"
st.session_state.agent_history   # list: agent guess history

# UI state
st.session_state.turn_log        # list[TurnResult]: one entry per round
st.session_state.thinking_panel  # list[str]: current round's agent steps for display
st.session_state.challenge_mode  # bool: is Challenge Mode active
st.session_state.personality     # str: selected personality key
```

---

## 9. API-Off Mode

Challenge Mode works without an OpenAI key:

- Strategy always runs (pure Python — no key needed)
- If `OPENAI_API_KEY` is not set → narration uses canned personality lines from `personalities.py`
- If API call fails at runtime → catch exception, fall back to canned line, log the failure
- Game never crashes due to API unavailability

This ensures grading and demos work even if the key is missing or rate-limited.

---

## 10. Logging

Every agent turn appends a JSON object to `game_log.jsonl`:

```json
{
  "timestamp": "2026-04-24T10:15:30Z",
  "personality": "Strategist",
  "round": 3,
  "observed_low": 51,
  "observed_high": 100,
  "chosen_guess": 75,
  "result": "Too Low",
  "new_low": 76,
  "new_high": 100,
  "narration": "Range narrowed to 51-100. Midpoint: 75. Calculating...",
  "api_latency_ms": 342,
  "api_used": true
}
```

---

## 11. Test Plan

Tests focus on correctness and safety, not brittle win-rate metrics:

| Test | What it checks |
|---|---|
| `test_game_logic.py` | Existing tests — all must pass (Phase 0) |
| `test_agent.py` — guesses in range | Agent never guesses outside `[low, high]` |
| `test_agent.py` — range always shrinks | After each Too High/Too Low, `high - low` strictly decreases |
| `test_agent.py` — history consistency | Agent history matches expected sequence for deterministic strategies |
| `test_agent.py` — Strategist solves in time | Binary search always solves Normal (1-100) within 7 guesses |
| `test_agent.py` — fallback narration | `get_narration(api_available=False)` returns a non-empty string |
| `test_personalities.py` | Each personality's strategy function returns an int within `[low, high]` for 50 random inputs |

---

## 12. Data Flow

```
User enables Challenge Mode → selects Personality
         │
         ▼
User submits guess → [logic_utils: check_guess] → hint shown
         │
         ▼  (if human did not win)
Agent turn begins: agent.py
    OBSERVE  [low, high, history]
    PLAN     personalities.py strategy fn → next_guess (Python)
    NARRATE  OpenAI API (or fallback)  → commentary string
    ACT      logic_utils.check_guess(next_guess, secret) → result
    EVALUATE update [low, high]
    LOG      logger.py → game_log.jsonl
         │
         ▼
app.py renders "Agent Thinking" panel + result
         │
         ▼
Win condition check → declare winner or continue
```

---

## 13. Folder Structure

```
Project4/
├── app.py
├── agent.py              ← NEW
├── personalities.py      ← NEW
├── logger.py             ← NEW
├── logic_utils.py        ← COMPLETED (Phase 0)
├── requirements.txt      ← updated: openai added
├── game_log.jsonl        ← generated at runtime
├── assets/
│   └── architecture.png  ← system diagram for README
├── tests/
│   ├── test_game_logic.py
│   ├── test_agent.py         ← NEW
│   └── test_personalities.py ← NEW
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-04-24-agentic-guessing-game-design.md
```

---

## 14. Out of Scope

- Multiplayer (two humans)
- Agent playing against itself
- Fine-tuning any model
- Persistent leaderboard across sessions
- Mobile layout optimization
