import html as _html
import random
import streamlit as st
from logic_utils import get_range_for_difficulty, parse_guess, check_guess, update_score
from agent import AgentState, run_agent_turn
from personalities import get_personality
from logger import log_turn

st.set_page_config(page_title="Number Duel", page_icon="⚔️", layout="wide")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@400;500;600;700&family=Russo+One&display=swap');

.stApp {
    background-color: #0F0F23;
    font-family: 'Chakra Petch', monospace;
}

section[data-testid="stSidebar"] {
    background-color: #080818;
    border-right: 1px solid #1E1B4B;
}

h1, h2, h3 { font-family: 'Russo One', sans-serif !important; color: #E2E8F0 !important; }

.duel-title {
    font-family: 'Russo One', sans-serif;
    font-size: 2.8rem;
    color: #E2E8F0;
    text-align: center;
    letter-spacing: 0.12em;
    text-shadow: 0 0 30px #7C3AED60, 0 0 60px #7C3AED20;
    margin-bottom: 0.1rem;
    line-height: 1.1;
}
.duel-sub {
    text-align: center;
    color: #7C3AED;
    font-size: 0.75rem;
    letter-spacing: 0.35em;
    text-transform: uppercase;
    margin-bottom: 1.75rem;
}

.player-card {
    background: #0D0D2B;
    border: 1px solid #1E293B;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    text-align: center;
}
.player-card.winner { box-shadow: 0 0 24px #F59E0B30; }
.player-card.loser { opacity: 0.45; }

.card-label { font-size: 0.62rem; letter-spacing: 0.3em; text-transform: uppercase; color: #475569; margin-bottom: 0.35rem; }
.card-name { font-family: 'Russo One', sans-serif; font-size: 1.1rem; color: #E2E8F0; letter-spacing: 0.04em; margin-bottom: 0.9rem; }
.card-stat { font-family: 'Russo One', sans-serif; font-size: 2.4rem; line-height: 1; }
.card-stat-label { font-size: 0.58rem; color: #475569; letter-spacing: 0.2em; text-transform: uppercase; margin-top: 0.2rem; }
.card-status { font-size: 0.72rem; margin-top: 0.6rem; letter-spacing: 0.08em; }
.s-playing { color: #4ADE80; }
.s-won { color: #F59E0B; font-family: 'Russo One', sans-serif; }
.s-lost { color: #F43F5E; }
.card-last { margin-top: 0.55rem; font-size: 0.78rem; color: #64748B; }

.vs-wrap {
    display: flex; flex-direction: column; align-items: center;
    justify-content: center; height: 100%; gap: 0.3rem; padding: 1rem 0;
}
.vs-label { font-size: 0.58rem; color: #374151; letter-spacing: 0.25em; text-transform: uppercase; }
.vs-text { font-family: 'Russo One', sans-serif; font-size: 2.2rem; color: #F43F5E; text-shadow: 0 0 18px #F43F5E70; line-height: 1; }
.vs-range { font-size: 0.68rem; color: #374151; letter-spacing: 0.08em; }

.last-turn-bar {
    background: #0A0A1E;
    border: 1px solid #1E293B;
    border-radius: 8px;
    padding: 0.55rem 1rem;
    font-size: 0.78rem;
    color: #64748B;
    display: flex;
    gap: 1.5rem;
    margin-bottom: 0.85rem;
    font-family: 'Chakra Petch', monospace;
}
.lt-you { color: #60A5FA; }
.lt-ai { color: #A78BFA; }
.lt-val { color: #E2E8F0; font-family: 'Russo One', sans-serif; }
.lt-outcome { font-size: 0.72rem; }
.lt-high { color: #F87171; }
.lt-low { color: #4ADE80; }
.lt-win { color: #F59E0B; }

.log-section-label {
    font-size: 0.62rem; letter-spacing: 0.3em; text-transform: uppercase;
    color: #374151; margin-bottom: 0.6rem; padding-bottom: 0.5rem;
    border-bottom: 1px solid #1E293B;
}

.battle-log {
    background: #06060F;
    border: 1px solid #1E293B;
    border-radius: 10px;
    padding: 0.85rem 1.1rem;
    max-height: 310px;
    overflow-y: auto;
    margin-bottom: 1.25rem;
}
.battle-log::-webkit-scrollbar { width: 3px; }
.battle-log::-webkit-scrollbar-track { background: transparent; }
.battle-log::-webkit-scrollbar-thumb { background: #7C3AED; border-radius: 2px; }

.log-empty { color: #334155; text-align: center; padding: 2rem 1rem; font-size: 0.82rem; font-style: italic; }

.log-row {
    display: flex; align-items: center; gap: 0.65rem;
    padding: 0.42rem 0; border-bottom: 1px solid #0F172A;
    font-size: 0.855rem; font-family: 'Chakra Petch', monospace;
}
.log-row:last-child { border-bottom: none; }

.log-tag {
    font-size: 0.58rem; font-weight: 700; letter-spacing: 0.12em;
    text-transform: uppercase; padding: 0.18rem 0.45rem; border-radius: 4px;
    flex-shrink: 0; min-width: 64px; text-align: center;
}
.tag-human { background: #1E3A5F; color: #60A5FA; }

.log-guess { font-family: 'Russo One', sans-serif; font-size: 1rem; color: #F1F5F9; }
.log-sep { color: #334155; font-size: 0.75rem; }
.log-result { font-size: 0.78rem; flex: 1; }
.r-high { color: #F87171; }
.r-low { color: #4ADE80; }
.r-win { color: #F59E0B; font-weight: 700; font-family: 'Russo One', sans-serif; font-size: 0.88rem; }

.log-narration {
    padding: 0.28rem 0 0.28rem 80px;
    font-size: 0.78rem;
    font-style: italic;
    border-bottom: 1px solid #0F172A;
    font-family: 'Chakra Petch', monospace;
    opacity: 0.85;
}
.log-narration:last-child { border-bottom: none; }

.log-event {
    text-align: center; padding: 0.6rem;
    font-family: 'Russo One', sans-serif; font-size: 0.9rem;
    color: #F59E0B; letter-spacing: 0.06em;
}

/* Match result panel */
.match-result {
    background: #0D0D2B;
    border-radius: 16px;
    padding: 2.5rem 2rem;
    text-align: center;
    margin: 1.5rem auto;
    max-width: 560px;
    border: 1px solid #1E293B;
}
.result-headline {
    font-family: 'Russo One', sans-serif;
    font-size: 3rem;
    letter-spacing: 0.15em;
    line-height: 1;
    margin-bottom: 0.5rem;
}
.result-sub { font-size: 0.85rem; color: #64748B; margin-bottom: 1.5rem; letter-spacing: 0.05em; }
.result-secret { font-size: 0.78rem; color: #475569; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.3rem; }
.result-number { font-family: 'Russo One', sans-serif; font-size: 4rem; color: #E2E8F0; line-height: 1; margin-bottom: 1.5rem; }
.result-stats {
    display: flex; justify-content: center; gap: 2.5rem;
    margin-bottom: 0; font-size: 0.8rem; color: #64748B;
}
.result-stat-val { font-family: 'Russo One', sans-serif; font-size: 1.6rem; display: block; }

/* Input overrides */
div[data-testid="stTextInput"] input {
    background: #06060F !important; border: 1px solid #7C3AED80 !important;
    color: #E2E8F0 !important; border-radius: 8px !important;
    font-family: 'Chakra Petch', monospace !important; font-size: 1rem !important;
}
div[data-testid="stTextInput"] input:focus { border-color: #A78BFA !important; box-shadow: 0 0 0 3px #7C3AED25 !important; }
div[data-testid="stTextInput"] input::placeholder { color: #334155 !important; }
div[data-testid="stFormSubmitButton"] > button { font-family: 'Russo One', sans-serif !important; letter-spacing: 0.08em !important; border-radius: 8px !important; }
button[data-testid="baseButton-secondary"] {
    background: #0D0D2B !important; color: #A78BFA !important;
    border: 1px solid #7C3AED60 !important; border-radius: 8px !important;
    font-family: 'Chakra Petch', monospace !important;
}
div[data-testid="stAlert"] { border-radius: 8px !important; font-family: 'Chakra Petch', monospace !important; }
details { background: #0D0D2B !important; border: 1px solid #1E293B !important; border-radius: 8px !important; }
details summary { font-family: 'Chakra Petch', monospace !important; color: #64748B !important; }

#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
</style>""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _outcome_display(outcome: str) -> tuple[str, str]:
    if outcome == "Win":
        return "FOUND IT", "r-win"
    if outcome == "Too High":
        return "↓ Too High", "r-high"
    return "↑ Too Low", "r-low"


def render_last_turn_bar(log: list):
    """Compact summary line showing the most recent human and agent turns."""
    human_last = next((e for e in reversed(log) if e["type"] == "human"), None)
    agent_last = next((e for e in reversed(log) if e["type"] == "agent"), None)
    if not human_last and not agent_last:
        return

    def _badge(entry, player_cls):
        text, cls = _outcome_display(entry["outcome"])
        return (
            f'<span class="{player_cls}">{entry["guess"]}</span> '
            f'<span class="lt-outcome {cls}">{text}</span>'
        )

    parts = []
    if human_last:
        parts.append(f'<span class="lt-you">You:</span> {_badge(human_last, "lt-val")}')
    if agent_last:
        name = agent_last.get("short_name", "AI")
        parts.append(f'<span class="lt-ai">{name}:</span> {_badge(agent_last, "lt-val")}')

    st.markdown(
        f'<div class="last-turn-bar">{"&nbsp;&nbsp;|&nbsp;&nbsp;".join(parts)}</div>',
        unsafe_allow_html=True,
    )


def render_battle_log(log: list):
    if not log:
        html = '<div class="battle-log"><div class="log-empty">No turns yet — make your first guess.</div></div>'
        st.markdown(html, unsafe_allow_html=True)
        return

    rows = ""
    for entry in reversed(log):
        t = entry["type"]
        if t == "human":
            text, cls = _outcome_display(entry["outcome"])
            rows += (
                f'<div class="log-row">'
                f'<span class="log-tag tag-human">You</span>'
                f'<span class="log-guess">{entry["guess"]}</span>'
                f'<span class="log-sep">→</span>'
                f'<span class="log-result {cls}">{text}</span>'
                f'</div>'
            )
        elif t == "agent":
            text, cls = _outcome_display(entry["outcome"])
            color = _html.escape(entry.get("color", "#A78BFA"))
            name = _html.escape(entry.get("short_name", "AI"))
            rows += (
                f'<div class="log-row">'
                f'<span class="log-tag" style="background:{color}25;color:{color}">{name}</span>'
                f'<span class="log-guess">{entry["guess"]}</span>'
                f'<span class="log-sep">→</span>'
                f'<span class="log-result {cls}">{text}</span>'
                f'</div>'
            )
            if entry.get("narration"):
                safe_narration = _html.escape(entry["narration"])
                # Important turns get a slightly brighter, bolder narration
                weight = "600" if entry.get("important") else "400"
                opacity = "1" if entry.get("important") else "0.7"
                rows += (
                    f'<div class="log-narration" style="color:{color};font-weight:{weight};opacity:{opacity}">'
                    f'"{safe_narration}"</div>'
                )
        elif t == "event":
            safe_msg = _html.escape(entry["message"])
            rows += f'<div class="log-row"><div class="log-event">{safe_msg}</div></div>'

    st.markdown(f'<div class="battle-log">{rows}</div>', unsafe_allow_html=True)


def render_player_card(label, name, attempts, attempt_limit, status, last_guess, border_color):
    if status == "won":
        status_html = '<div class="card-status s-won">WINNER</div>'
        extra_style = f"border-color:{border_color};box-shadow:0 0 20px {border_color}30;"
        extra_class = " winner"
    elif status == "lost":
        status_html = '<div class="card-status s-lost">ELIMINATED</div>'
        extra_style = "border-color:#F43F5E40;"
        extra_class = " loser"
    else:
        remaining = attempt_limit - attempts
        status_html = f'<div class="card-status s-playing">{remaining} attempt{"s" if remaining != 1 else ""} left</div>'
        extra_style = f"border-color:{border_color}60;"
        extra_class = ""

    last_html = ""
    if last_guess is not None:
        last_html = f'<div class="card-last">Last guess: <strong style="color:#E2E8F0">{last_guess}</strong></div>'

    st.markdown(
        f'<div class="player-card{extra_class}" style="{extra_style}">'
        f'<div class="card-label">{_html.escape(label)}</div>'
        f'<div class="card-name">{_html.escape(name)}</div>'
        f'<div class="card-stat" style="color:{border_color}">{attempts}</div>'
        f'<div class="card-stat-label">guesses</div>'
        f'{status_html}'
        f'{last_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_match_result(winner: str, secret: int, human_attempts: int, agent_attempts: int, agent_name: str):
    if winner == "human":
        headline = "VICTORY"
        color = "#F59E0B"
        sub = f"You found it before {_html.escape(agent_name)}."
    elif winner == "agent":
        headline = "DEFEAT"
        color = "#F43F5E"
        sub = f"{_html.escape(agent_name)} found it first."
    elif winner == "both_lost":
        headline = "STALEMATE"
        color = "#64748B"
        sub = "Neither player found the number."
    else:
        headline = "DRAW"
        color = "#A78BFA"
        sub = "You tied — same number of guesses."

    st.markdown(
        f'<div class="match-result" style="border-color:{color}40">'
        f'<div class="result-headline" style="color:{color}">{headline}</div>'
        f'<div class="result-sub">{sub}</div>'
        f'<div class="result-secret">The secret was</div>'
        f'<div class="result-number">{secret}</div>'
        f'<div class="result-stats">'
        f'<div><span class="result-stat-val" style="color:#60A5FA">{human_attempts}</span>your guesses</div>'
        f'<div><span class="result-stat-val" style="color:#A78BFA">{agent_attempts}</span>AI guesses</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def reset_round(difficulty: str):
    low, high = get_range_for_difficulty(difficulty)
    st.session_state.secret = random.randint(low, high)
    st.session_state.attempts = 0
    st.session_state.status = "playing"
    st.session_state.history = []
    st.session_state.human_last_guess = None
    st.session_state.agent_low = low
    st.session_state.agent_high = high
    st.session_state.agent_attempts = 0
    st.session_state.agent_status = "playing"
    st.session_state.agent_history = []
    st.session_state.agent_last_guess = None
    st.session_state.battle_log = []


# ── Title ─────────────────────────────────────────────────────────────────────
st.markdown('<h1 class="duel-title">NUMBER DUEL</h1>', unsafe_allow_html=True)
st.markdown('<p class="duel-sub">Human vs AI &nbsp;·&nbsp; Who finds it first?</p>', unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("### Settings")
difficulty = st.sidebar.selectbox("Difficulty", ["Easy", "Normal", "Hard"], index=1)
attempt_limit_map = {"Easy": 6, "Normal": 8, "Hard": 5}
attempt_limit = attempt_limit_map[difficulty]
low, high = get_range_for_difficulty(difficulty)
st.sidebar.caption(f"Range: {low}–{high}   ·   Max guesses: {attempt_limit}")

st.sidebar.divider()
st.sidebar.markdown("### Your Opponent")
_p_labels = {
    "Strategist": "The Strategist — cold & precise",
    "Gambler": "The Gambler — reckless instinct",
    "Professor": "The Professor — condescending logic",
    "TrashTalker": "The Trash-Talker — pure ego",
}
selected_personality = st.sidebar.radio(
    "Pick your opponent",
    options=list(_p_labels.keys()),
    format_func=lambda k: _p_labels[k],
    label_visibility="collapsed",
)

# ── Session state init ────────────────────────────────────────────────────────
_defaults = {
    "secret": None,
    "attempts": 0,
    "score": 0,
    "status": "playing",
    "history": [],
    "active_difficulty": difficulty,
    "personality_key": selected_personality,
    "agent_low": low,
    "agent_high": high,
    "agent_attempts": 0,
    "agent_status": "playing",
    "agent_history": [],
    "battle_log": [],
    "human_last_guess": None,
    "agent_last_guess": None,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

if st.session_state.secret is None:
    st.session_state.secret = random.randint(low, high)

if st.session_state.active_difficulty != difficulty:
    st.session_state.active_difficulty = difficulty
    reset_round(difficulty)
    st.rerun()

if st.session_state.personality_key != selected_personality:
    st.session_state.personality_key = selected_personality
    reset_round(difficulty)
    st.rerun()

personality = get_personality(st.session_state.personality_key)

# ── Head-to-head status bar ───────────────────────────────────────────────────
col_you, col_vs, col_ai = st.columns([5, 2, 5])

with col_you:
    render_player_card(
        label="YOU",
        name="Player",
        attempts=st.session_state.attempts,
        attempt_limit=attempt_limit,
        status=st.session_state.status,
        last_guess=st.session_state.human_last_guess,
        border_color="#3B82F6",
    )

with col_vs:
    st.markdown(
        f'<div class="vs-wrap">'
        f'<div class="vs-label">Round 1</div>'
        f'<div class="vs-text">VS</div>'
        f'<div class="vs-range">{low} — {high}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

with col_ai:
    render_player_card(
        label="AI OPPONENT",
        name=personality.name,
        attempts=st.session_state.agent_attempts,
        attempt_limit=attempt_limit,
        status=st.session_state.agent_status,
        last_guess=st.session_state.agent_last_guess,
        border_color=personality.color,
    )

# ── Last turn summary + battle log ───────────────────────────────────────────
render_last_turn_bar(st.session_state.battle_log)
st.markdown('<div class="log-section-label">Battle Log — newest first</div>', unsafe_allow_html=True)
render_battle_log(st.session_state.battle_log)

# ── Game over ─────────────────────────────────────────────────────────────────
human_done = st.session_state.status != "playing"
agent_done = st.session_state.agent_status != "playing"

if human_done or agent_done:
    if st.session_state.status == "won" and st.session_state.agent_status != "won":
        winner = "human"
    elif st.session_state.agent_status == "won" and st.session_state.status != "won":
        winner = "agent"
    elif st.session_state.status == "lost" and st.session_state.agent_status == "lost":
        winner = "both_lost"
    else:
        winner = "draw"

    render_match_result(
        winner=winner,
        secret=st.session_state.secret,
        human_attempts=st.session_state.attempts,
        agent_attempts=st.session_state.agent_attempts,
        agent_name=personality.name,
    )

    if st.button("Rematch", type="primary"):
        reset_round(difficulty)
        st.rerun()
    st.stop()

# ── Guess input ───────────────────────────────────────────────────────────────
col_input, col_new = st.columns([4, 1])
with col_input:
    with st.form(key=f"guess_{difficulty}_{selected_personality}", clear_on_submit=True):
        raw_guess = st.text_input(
            "guess",
            placeholder=f"Enter a number between {low} and {high}…",
            label_visibility="collapsed",
        )
        submit = st.form_submit_button("LOCK IN GUESS", type="primary", use_container_width=True)

with col_new:
    if st.button("New Game", use_container_width=True):
        reset_round(difficulty)
        st.rerun()

# ── Game logic ────────────────────────────────────────────────────────────────
if submit:
    ok, guess_int, err = parse_guess(raw_guess, low=low, high=high)

    if not ok:
        st.error(err)
    elif guess_int in st.session_state.history:
        st.warning(f"You already tried {guess_int} — pick a different number.")
    else:
        st.session_state.attempts += 1
        st.session_state.history.append(guess_int)
        st.session_state.human_last_guess = guess_int
        outcome = check_guess(guess_int, st.session_state.secret)
        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        # Log the human turn
        log_turn({
            "player": "human",
            "guess": guess_int,
            "result": outcome,
            "attempt": st.session_state.attempts,
        })

        st.session_state.battle_log.append({
            "type": "human",
            "guess": guess_int,
            "outcome": outcome,
        })

        if outcome == "Win":
            st.session_state.status = "won"
            st.session_state.battle_log.append({
                "type": "event",
                "message": f"YOU WIN — secret was {st.session_state.secret}",
            })
            st.rerun()

        if st.session_state.attempts >= attempt_limit:
            st.session_state.status = "lost"

        # Agent turn
        if st.session_state.agent_status == "playing":
            with st.spinner(f"{personality.name} is thinking…"):
                agent_state = AgentState(
                    low=st.session_state.agent_low,
                    high=st.session_state.agent_high,
                    attempts=st.session_state.agent_attempts,
                    status=st.session_state.agent_status,
                    history=list(st.session_state.agent_history),
                )
                result = run_agent_turn(
                    agent_state,
                    personality,
                    st.session_state.secret,
                    human_attempts=st.session_state.attempts,
                    human_last_guess=guess_int,
                )

            st.session_state.agent_low = agent_state.low
            st.session_state.agent_high = agent_state.high
            st.session_state.agent_attempts = agent_state.attempts
            st.session_state.agent_status = agent_state.status
            st.session_state.agent_history = agent_state.history
            st.session_state.agent_last_guess = result.guess

            # Show narration only on important moments
            remaining_range = st.session_state.agent_high - st.session_state.agent_low + 1
            is_important = (
                st.session_state.agent_attempts == 1       # first AI turn
                or remaining_range <= 5                    # closing in
                or result.outcome == "Win"                 # AI wins
                or st.session_state.agent_attempts < st.session_state.attempts  # AI overtook
            )

            st.session_state.battle_log.append({
                "type": "agent",
                "guess": result.guess,
                "outcome": result.outcome,
                "narration": result.narration,
                "short_name": personality.name.replace("The ", ""),
                "color": personality.color,
                "important": is_important,
            })

            if result.outcome == "Win":
                st.session_state.agent_status = "won"
                st.session_state.battle_log.append({
                    "type": "event",
                    "message": f"{personality.name} wins — secret was {st.session_state.secret}",
                })
            elif st.session_state.agent_attempts >= attempt_limit:
                st.session_state.agent_status = "lost"

        st.rerun()

# ── Debug ─────────────────────────────────────────────────────────────────────
with st.expander("Developer Debug"):
    st.write({
        "secret": st.session_state.secret,
        "human_attempts": st.session_state.attempts,
        "agent_attempts": st.session_state.agent_attempts,
        "agent_range": [st.session_state.agent_low, st.session_state.agent_high],
        "score": st.session_state.score,
        "history": st.session_state.history,
    })
