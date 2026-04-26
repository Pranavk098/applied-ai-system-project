# Model Card — Number Duel AI Opponent

## Model Overview

| Field | Value |
|---|---|
| **Model used** | `gpt-3.5-turbo` (OpenAI Chat Completions API) |
| **Role in system** | Narration only — generates in-character commentary after each AI guess |
| **Decision-making** | Pure Python strategy functions (not the LLM) |
| **API optional** | Yes — the game runs fully without an API key using fallback lines |
| **Max tokens per call** | 60 |
| **Temperature** | 0.95 |

---

## What the Model Does (and Does Not Do)

The LLM is the **voice**, not the brain. It never chooses which number to guess — that is handled by deterministic Python strategy functions in `personalities.py`. The LLM only receives the result of a guess (the number, the outcome, the situation label, and the human's last guess) and produces a short in-character reaction (under 30 words).

This separation means:
- Game correctness does not depend on the LLM
- All 4 personality strategies are fully testable without an API key
- The game never crashes if the API is unavailable

---

## Prompting Approach

Each API call uses a three-layer message structure:

```
[system]   Personality system prompt — defines character voice, constraints, max length
[user]     Few-shot example 1 (human context)
[assistant] Few-shot example 1 (expected response)
[user]     Few-shot example 2 (human context)
[assistant] Few-shot example 2 (expected response)
[user]     Few-shot example 3 (human context)
[assistant] Few-shot example 3 (expected response)
[user]     Live game context — guess, outcome, range, situation, human's last guess
```

### System Prompts by Personality

| Personality | Voice Style | Key Constraint |
|---|---|---|
| Strategist | Cold, analytical, precise | "No warmth. No filler. Max 25 words." |
| Gambler | Reckless, overconfident, instinct-driven | "Sound like you're winning even when losing." |
| Professor | Condescending, educational, mathematical | "Reference O(log n) naturally. Max 35 words." |
| Trash-Talker | Boastful, dramatic, relational | "Taunt their guesses, celebrate your own." |

### Few-Shot Examples

Each personality has 3 (user, assistant) pairs injected before the live context. These anchor the model to the target register and prevent generic hedging under pressure. See `personalities.py` → `few_shot_examples` field for the full set.

### Situational Context

The live user message includes a `situation` label computed by `_detect_situation()`:

| Situation | Condition |
|---|---|
| `opening` | First agent guess |
| `closing_in` | Remaining range ≤ 3 numbers |
| `ahead` | Agent has fewer guesses than human |
| `behind` | Agent has more guesses than human |
| `tied` | Equal guess counts |

---

## Fallback Behavior (No API Key)

When `OPENAI_API_KEY` is not set or an API call fails, `get_narration()` returns a pre-written line from the personality's `situation_lines` dict — a curated set of 3 lines per situation per personality (e.g., `opening`, `ahead`, `behind`, `closing_in`, `tied`). The game never crashes or displays an error to the player.

**Limitation:** Without an API key, all four personalities share the same line-picking mechanism (random choice from the situation's pool). Personality distinction in narration disappears — only the strategy differs.

---

## Evaluation Results

Evaluated using `eval.py` — 21 fixed secrets in [1, 100], 8-guess limit, `random.seed(42)`:

```
Personality       Avg Guesses  Max Guesses   Solved   Within Limit
------------------------------------------------------------------
Strategist                5.7            7    21/21          21/21
Gambler                   8.5           17    21/21          12/21
Professor                 5.7            7    21/21          21/21
TrashTalker               6.4           11    21/21          18/21
```

The Strategist and Professor are deterministic binary-search — they always converge within 7 guesses. The Gambler's random strategy solves every secret eventually but exceeds the 8-guess limit on 9 of 21 secrets. The Trash-Talker's near-optimal strategy (midpoint + upward jitter, locks in when range ≤ 6) finishes within the limit on 18/21.

---

## Intended Use

- Competitive number guessing game narration
- Educational demonstration of agentic AI loop design
- Classroom context showing how LLMs can add personality to deterministic systems

## Out-of-Scope Use

- The model should not be used to make game decisions (it does not — Python handles that)
- Should not be deployed publicly with an exposed API key (server-side proxying required)
- Not suitable for high-stakes or sensitive contexts

---

## Limitations

1. **Narration repetition** — Fallback lines are picked randomly and the same line can appear twice in a row. Tracked in `AgentState` history for future deduplication.
2. **Coarse situation labels** — "Ahead" after 1 guess vs. 4 guesses means very different things tactically, but the model receives the same label.
3. **No memory across turns** — Each narration call is stateless. The model cannot reference what it said two turns ago.
4. **API cost exposure** — If deployed publicly, unlimited API calls are possible without server-side rate limiting.
5. **Token cap** — Max 60 tokens per call. Longer reasoning or richer context cannot be expressed.

---

## Ethical Considerations

The game cannot produce harmful output — it only narrates a number guessing game. The main risk is API cost misuse if deployed without rate limiting. Input injection through guess values is not possible because only validated integers are passed to the prompt. The system is transparent about its AI use — the UI labels AI guesses clearly and the architecture separates LLM voice from Python decision-making.
