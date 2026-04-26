# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

- What did the game look like the first time you ran it?
- The two mains bugs I have observed were:
    1. The original fallback converted guess to a string and compared it to secret (which on even attempts was already a string). The fix converts both values to int and does proper numeric comparison. It also added a nested try/except and an equality check in the fallback path.
    2. attempts Initialized to 1 Instead of 0 in app.py, Starting at 1 means the very first display shows "Attempts left: 7" (for Normal, limit 8) instead of the correct "Attempts left: 8", and all attempt-based scoring calculations are off-by-one from the start.

## 2. How did you use AI as a teammate?

- I have used Copilot in VSCode.
- One such suggestion that AI handed me was the type error logic. It clearly explained me that the comparisions are lexicographic and not numeric. And after the fix was implemented I ran and concluded that fix was implemented by testing the website on and confirming the correct logic. 
- Nor a wrong suggestion but when I was asking the exact section of the code where number of attempts ligc was implemented the, was getting not to straight answer it was focused on finding some logic glitch behind the number of attempts section rather than the exact part of the code.


## 3. Debugging and testing your fixes

Fix and verify manually — after correcting check_guess() in app.py, manually guessing numbers confirmed hints matched expectations.
Noticed that hints said "Go Higher" when guessing a number that was clearly too high, and vice versa. This pointed directly to the comparison in check_guess().
by watching the debug panel, you could observe the secret was sometimes an int and sometimes a str depending on attempt number, confirming the type-switching bug.
Asking AI whenever i feel there is a bug in certain sectio of the code, to confirm my theory has been a great help, as it gives me confidence and also give a proper start to debug the issue.

## 4. What did you learn about Streamlit and state?

Streamlit re-runs the entire script on every interaction. Every button click, text input change, or widget interaction triggers a full top-to-bottom re-execution of app.py. Variables defined outside st.session_state are reset each run — this is why the secret number appeared to change randomly
- removed the hard coded part in the UI and made it correspoding to difficulting selected, new game will reset with the random integer within low and high of the selected difficulty range. 


## 5. Looking ahead: your developer habits
game_logic.py file was already written as a spec. Running pytest before touching any code immediately told you exactly what behavior was expected ("Win", "Too High", "Too Low") and gave a clear pass/fail target for each fix.

ask the AI to explain why each piece of generated code works, not just what it does. In this project, the AI-generated check_guess() had the comparison operator backwards — a subtle bug that would have been caught if the reasoning behind the comparison had been questioned during generation

---

## Project 4 Reflection — Number Duel (AI Opponent)

### 1. Limitations and biases in the system

The Strategist and Professor personalities always pick the mathematical midpoint — they are deterministic and will always solve a 1–100 game in at most 7 guesses. This means they are not interesting to play against once you know how they work: you can predict every guess they will make. The Gambler's randomness makes it unreliable in the other direction — it can get lucky or waste most of its attempts depending on where the random walk lands. Neither extreme represents how a human opponent actually plays.

The narration is biased toward the personality matching the situation label, but those labels (opening, ahead, behind, closing_in) are coarse. Two guesses into a range of [1, 100] the agent is labeled "ahead" if it has guessed fewer times than the human — but that's not meaningful this early. The commentary can feel false when the game is still wide open.

Without an API key, all four personalities collapse into a single set of canned lines per situation. The personality distinction disappears from the narration entirely; only the strategy remains different.

### 1b. Future Improvements

The most impactful near-term improvement would be making the agent's reasoning **visible in the UI**. The structured thinking steps (`_observe`, `_plan`, `_act`, `_assess`, `_narrate`, `_evaluate`) already exist as structured dicts in `TurnResult.thinking`, but they are never rendered for the player to see. A collapsible "Agent Trace" panel in the sidebar would let the player watch the AI's decision chain after each turn — this would make the agentic loop a feature of the experience rather than an internal implementation detail.

A second improvement is **fallback narration deduplication**. In the current system, fallback lines are picked randomly and the same line can appear twice in a row (visible in game testing: "You're burning attempts. I'm not." appeared back-to-back). Tracking the last 2–3 narration lines in `AgentState` and excluding them from the random pick would eliminate the repetition and make the AI feel more present.

A third improvement is **server-side API proxying** for public deployment. The API key is currently read from an environment variable which works locally but cannot safely be embedded in a public app. A thin FastAPI or Flask proxy that accepts narration requests from the Streamlit frontend, enforces per-session token limits, and holds the key server-side would make the game safe to deploy publicly.

### 2. Could the AI be misused, and how would you prevent it?

The game itself is low-stakes — it cannot produce harmful output because it only narrates a number guessing game. The most realistic misuse vector is the OpenAI API key: it is read from an environment variable, and if the app were deployed publicly with a key set, any player could trigger unlimited API calls. Mitigation: proxy calls through a server-side route that enforces per-session rate limits and never exposes the key to the client. A hard cap on tokens per game session (e.g., 500 tokens) would also contain costs.

A second, subtler concern: the narration prompts include the human's last guess. In principle a user could inject instructions into their guess if input were passed unsanitized. The current code only passes a validated integer, so this path is closed — but it is worth keeping that invariant explicit as the system evolves.

### 3. What surprised me while testing reliability

The most surprising result came from `test_fallback_narration_when_no_api_key`. I expected the test to require mocking — patching the OpenAI client so it would not actually call the API. Instead, `get_narration` already handled the missing-key case with a try/except that caught the authentication error and returned a fallback line. The test passed immediately with zero changes to `agent.py`. That was reassuring, but it also revealed that the fallback path had never been intentionally designed — it was a side effect of a broad exception handler. A function that silently absorbs errors and returns a default can hide real bugs just as easily as it masks expected failures.

The second surprise was how stable the Strategist tests were. `test_strategist_solves_normal_within_7` runs five different secrets (1, 25, 50, 73, 100) and passes every time with no flakiness. I had assumed off-by-one errors in the range narrowing would show up at the extremes (secret = 1 or 100), but the binary search logic was clean from the start.

### 4. Collaboration with AI — one helpful suggestion, one flawed one

**Helpful:** When designing how the agent should track its search range across turns, I asked Claude Code how to pass mutable state through repeated function calls without using globals. It suggested the `AgentState` dataclass — a single object holding `low`, `high`, `status`, and `history` that gets passed by reference and mutated in place each turn. This was cleaner than the dict I was planning to use and made the tests straightforward to write, since I could inspect `state.low` and `state.high` directly after each `run_agent_turn` call.

**Flawed:** When writing `test_win_sets_status`, Claude Code suggested asserting `result.outcome == "win"` (lowercase). The test passed the linter but silently failed at runtime — `TurnResult.outcome` is set to `"Win"` (capitalized, matching the return value of `check_guess`). The mismatch meant the assertion always evaluated to `False` without raising an error because I had not yet added the `assert` keyword in that draft. Once the `assert` was in place the test failed immediately, making the bug obvious — but if the assertion had been written without the keyword it would have looked like a passing test forever. The lesson: always verify that a new test can actually fail before trusting that it passes.