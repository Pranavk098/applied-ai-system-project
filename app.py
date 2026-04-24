import random
import streamlit as st
from logic_utils import get_range_for_difficulty, parse_guess, check_guess, update_score
from agent import AgentState, run_agent_turn
from personalities import get_personality, list_personalities

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
    # Reset agent state
    st.session_state.agent_low = low
    st.session_state.agent_high = high
    st.session_state.agent_attempts = 0
    st.session_state.agent_status = "playing"
    st.session_state.agent_history = []
    st.session_state.thinking_panel = []
    st.session_state.turn_log = []


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
