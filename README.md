# 🎮 Game Glitch Investigator: The Impossible Guesser

## 🚨 The Situation

You asked an AI to build a simple "Number Guessing Game" using Streamlit.
It wrote the code, ran away, and now the game is unplayable. 

- You can't win.
- The hints lie to you.
- The secret number seems to have commitment issues.

## 🛠️ Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Run the broken app: `python -m streamlit run app.py`

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

## 🕵️‍♂️ Your Mission

1. **Play the game.** Open the "Developer Debug Info" tab in the app to see the secret number. Try to win.
2. **Find the State Bug.** Why does the secret number change every time you click "Submit"? Ask ChatGPT: *"How do I keep a variable from resetting in Streamlit when I click a button?"*
3. **Fix the Logic.** The hints ("Higher/Lower") are wrong. Fix them.
4. **Refactor & Test.** - Move the logic into `logic_utils.py`.
   - Run `pytest` in your terminal.
   - Keep fixing until all tests pass!

## 📝 Document Your Experience

- [ ] Describe the game's purpose.
- [ ] Detail which bugs you found.
- [ ] Explain what fixes you applied.

## 📸 Demo

- [ ] [Insert a screenshot of your fixed, winning game here]

## 🚀 Stretch Features

- [ ] [If you choose to complete Challenge 4, insert a screenshot of your Enhanced Game UI here]
