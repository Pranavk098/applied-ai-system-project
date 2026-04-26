# Reflection: Number Duel — Applied AI System

---

## Part 1: Game Glitch Investigator (Modules 1–3)

### 1. What was broken when you started?

When I first ran the game, it immediately behaved incorrectly in two visible ways. The hint direction was reversed — guessing a number clearly below the secret would say "Go Higher" when the correct hint should have been "Too Low," and vice versa. On top of that, the attempt counter started at 1 instead of 0, which meant the very first turn already showed one attempt used even though the player had not yet guessed. The root cause of the hint bug was that the comparison operators in `check_guess()` were flipped (`<` and `>` swapped), so every hint pointed the player in the wrong direction. The attempt initialization error caused all attempt-based scoring and display calculations to be off by one from the start, making the game feel broken even when the core logic was otherwise correct.

There was also a third bug specifically affecting even-numbered attempts: the secret number was being compared to the guess as a string rather than as an integer. This meant that on those attempts, the comparison was lexicographic rather than numeric — so `"9"` would appear greater than `"10"` because `"9"` sorts after `"1"` alphabetically. This caused hints to be randomly correct or wrong depending on the attempt number, which was one of the hardest bugs to spot without looking at the debug panel.

---

### 2. How did you use AI as a teammate?

I used GitHub Copilot inside VSCode throughout the debugging process — primarily for two purposes: confirming theories about what was causing a bug, and explaining why a piece of code behaved the way it did. When I suspected the hint comparisons were backwards, I described the symptom to Copilot and it confirmed that the operators were flipped and explained exactly which lines needed to change. Its most useful contribution was explaining that the type mismatch bug caused lexicographic rather than numeric comparison — I could see the wrong hints appearing, but I did not initially understand why they only appeared on even attempts. Copilot connected the symptom to the root cause clearly.

However, Copilot was less helpful when I asked it to locate exactly where the attempt initialization logic lived in the code. Instead of pointing me directly to the `attempts = 1` line in `app.py`, it kept steering the conversation toward diagnosing whether there was a logic error in how attempts were counted during gameplay. It was looking for a more complex bug than the one that existed. That experience taught me that AI assistants are better at explaining concepts and confirming specific theories than at navigating unfamiliar code bases on your behalf.

---

### 3. How did you debug and verify your fixes?

My primary debugging method was combining the built-in debug panel in the Streamlit app with manual testing. By watching the debug panel while guessing, I could see that the `secret` variable was sometimes stored as an integer and sometimes as a string depending on the attempt number — this directly confirmed the type-switching bug without needing to read all of the code. After fixing `check_guess()`, I verified the hint logic manually by guessing numbers I knew were too high and checking that the displayed hint matched: "Too High" when the guess exceeded the secret, "Too Low" when it was below. I repeated this for several secrets across all three difficulty ranges to make sure the fix held under different conditions.

For the attempt counter bug, I reset the game and watched the initial display before making any guess at all. Seeing "Attempts left: 7" instead of "Attempts left: 8" on Normal difficulty before the first guess confirmed the off-by-one immediately. After changing the initialization from `attempts = 1` to `attempts = 0`, the counter started correctly. I used Copilot to double-check my reasoning before each fix — not to generate the fix, but to confirm that my diagnosis was correct — which gave me confidence that I was fixing the right thing and not introducing new issues.

---

### 4. What did you learn about Streamlit and state?

The most important thing I learned is that Streamlit reruns the entire script from top to bottom on every user interaction — every button click, every form submission, every widget change triggers a full re-execution of `app.py`. This means any variable defined outside of `st.session_state` is reset to its initial value on every interaction, which is why the secret number appeared to change randomly during gameplay: it was being re-randomized each time the script ran. Once I understood this, the fix was clear — the secret and all game state had to be stored inside `st.session_state` so they would persist across reruns.

A related lesson was that the difficulty range and attempt limit had to be derived from `st.session_state` rather than hardcoded. The original code had hardcoded values that did not update when the player changed the difficulty setting mid-game. By tying the range and limit display directly to the selected difficulty, the UI correctly reflected the current game rules instead of showing stale values from a previous session.

---

### 5. Looking ahead: your developer habits

The most transferable habit I developed in this project is treating existing tests as a specification before touching any code. The `game_logic.py` test file was already written and described exactly what `check_guess()` should return for each input. Running `pytest` before making any changes immediately told me which behavior the code was supposed to have, and gave me a concrete pass/fail target for each fix rather than guessing whether my changes were correct. That habit — read the tests first, then make the code match — is something I now apply at the start of any debugging session.

The second habit is asking AI to explain the *reasoning* behind generated code, not just accept the code itself. In this project, the AI-generated `check_guess()` had the comparison operators backwards — a subtle bug that produced plausible-looking code that did exactly the wrong thing. If I had asked "why does this comparison go in this direction?" instead of "does this look right?", the bug would have surfaced immediately. Treating AI output as a first draft to interrogate, not a finished answer to accept, is the most important adjustment I have made in how I work.

---

## Part 2: Number Duel — AI Opponent (Project 4)

### 1. What are the limitations or biases in the system?

The Strategist and Professor personalities always pick the mathematical midpoint — they are fully deterministic and will always solve a 1–100 game in at most 7 guesses. This means they are predictable once you know how they work: after a few games, a player can anticipate every guess the Strategist will make. The Gambler is unreliable in the opposite direction — its random strategy means it can get very lucky or waste most of its attempts, and its performance varies significantly across runs. Neither extreme represents how a real human opponent plays, which limits the variety of experiences the game can offer.

The situation detection system is also coarse. The agent is labeled "ahead" if it has made fewer guesses than the human, but early in the game this comparison is meaningless — being one guess ahead out of eight does not reflect a real strategic advantage. This means the AI's narration can feel tonally off, celebrating a lead that does not yet exist or reacting to a deficit that is easily recoverable. Without an API key, the problem becomes more visible: all four personalities collapse into the same pool of canned lines per situation, and the personality distinction in narration disappears entirely — only the guessing strategy differs.

### 2. Future improvements

The most impactful near-term improvement would be making the agent's reasoning **visible in the UI**. The structured thinking steps (`_observe`, `_plan`, `_act`, `_assess`, `_narrate`, `_evaluate`) already exist as structured dicts inside `TurnResult.thinking` and are written to `game_log.jsonl` on every turn, but they are not rendered in the interface. A collapsible "Agent Trace" panel would let the player watch the decision chain after each turn — turning the agentic loop from an internal detail into an actual feature of the game experience.

A second improvement is **fallback narration deduplication**. Fallback lines are currently picked at random from the situation pool, and the same line can appear on consecutive turns — during testing, "You're burning attempts. I'm not." appeared back-to-back. Tracking the last two or three narration lines in `AgentState` and excluding them from the random pick would eliminate this repetition with minimal code change.

A third improvement is **server-side API proxying** for safe public deployment. The API key is currently read from an environment variable, which works locally but cannot be embedded in a publicly hosted app. A thin server-side proxy that accepts narration requests, enforces per-session token limits, and never exposes the key to the client would make the game deployable without financial risk.

---

### 3. Could the AI be misused, and how would you prevent it?

The game itself cannot produce harmful output — it only generates short narration lines for a number guessing game. The most realistic misuse risk is API cost abuse: if the app were deployed publicly with an API key set in the environment, any player could trigger unlimited OpenAI calls by playing continuously. The mitigation is server-side proxying with a per-session token cap (for example, 500 tokens per game session), so the key is never exposed to the client and individual sessions cannot run up large bills.

A subtler concern is prompt injection. The narration prompt includes the human player's last guess as context so the AI can react to it. If that value were passed as a raw string rather than a validated integer, a player could type instructions instead of a number and potentially manipulate the AI's output. The current `parse_guess()` function rejects anything that is not a valid integer before it ever reaches the prompt, so this path is closed — but this invariant must be maintained explicitly as the codebase evolves, since it is not immediately obvious to a future contributor why the validation is security-relevant.

---

### 4. What surprised me while testing reliability?

The most surprising result came from `test_fallback_narration_when_no_api_key`. I expected the test to require mocking — patching the OpenAI client to prevent a real API call. Instead, `get_narration()` already handled the missing-key case: the broad `except Exception` handler caught the authentication error and returned a fallback line silently. The test passed immediately without any changes to `agent.py`. That was reassuring, but it also revealed that the fallback behavior had never been deliberately designed — it was a side effect of catching all exceptions. A function that silently absorbs errors and returns a default is difficult to trust, because it masks real failures just as effectively as it handles expected ones.

The second surprise was how stable the Strategist tests were across all edge-case secrets. `test_strategist_solves_normal_within_7` runs against secrets at both extremes of the range (1 and 100) and in the middle, and passes every time without flakiness. I had expected off-by-one errors in the range narrowing to appear at the boundaries, but the binary search implementation was correct from the start. This showed me that well-chosen test cases at the edges of the input space give much stronger confidence than many tests clustered in the middle.

---

### 5. Describe your collaboration with AI — one helpful suggestion, one flawed one

**Helpful:** When designing how the agent should track its search range across turns, I asked Claude Code how to pass mutable state through repeated function calls without using global variables. It suggested the `AgentState` dataclass — a single object holding `low`, `high`, `status`, and `history` that gets passed by reference and mutated in place each turn. This was cleaner than the dictionary I had been planning to use, and it made the tests significantly easier to write: after each call to `run_agent_turn`, I could inspect `state.low` and `state.high` directly to verify the range had narrowed correctly.

**Flawed:** When writing the `test_win_sets_status` test, Claude Code suggested asserting `result.outcome == "win"` (all lowercase). The test passed the linter without complaint, but at runtime the assertion silently evaluated to `False` every time — `TurnResult.outcome` is set to `"Win"` with a capital W, matching the return value of `check_guess()`. The casing mismatch meant the assertion was always wrong but never raised an error because I had not yet added the `assert` keyword in that draft of the code. Once `assert` was in place the test failed immediately and made the bug obvious. The lesson I took from this is to always verify that a new test can actually fail before trusting that it passes — a test that never fails is not a test.
