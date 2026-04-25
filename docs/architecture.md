# System Architecture — Number Duel

Three diagrams covering different levels of the system:

1. [Component Map](#1-component-map) — what the modules are and how they connect
2. [Agent Turn Sequence](#2-agent-turn-sequence) — the agentic loop step by step
3. [Full Data Flow](#3-full-data-flow) — one complete round from input to output

---

## 1. Component Map

Shows every module, external service, and file, and the dependency edges between them.

```mermaid
---
id: 8a179d6f-77b8-4a81-b620-f2407c0202f8
---
graph TD
    %% ── Human layer ──────────────────────────────────────────
    HUMAN([👤 Human Player])

    %% ── UI layer ─────────────────────────────────────────────
    subgraph UI ["Streamlit UI  (app.py)"]
        FORM["Guess Input Form"]
        CARDS["Player Cards\nYou  ·  VS  ·  AI"]
        BLOG["Battle Log\nnewer turns first"]
        LTBAR["Last-Turn Summary Bar"]
        RESULT["Match Result Panel\nVICTORY / DEFEAT / STALEMATE"]
        SIDEBAR["Sidebar\nDifficulty · Opponent selector"]
        SESSION[("Session State\nsecret · attempts · history\nagent_low · agent_high")]
    end

    %% ── Logic layer ──────────────────────────────────────────
    subgraph LOGIC ["Game Logic  (logic_utils.py)"]
        PARSE["parse_guess(raw, low, high)\nrejects decimals + out-of-range"]
        CHECK["check_guess(guess, secret)\n→ Win / Too High / Too Low"]
        SCORE["update_score(score, outcome, attempt)"]
        RANGE["get_range_for_difficulty(difficulty)\n→ (low, high)"]
    end

    %% ── Agent layer ──────────────────────────────────────────
    subgraph AGENT ["AI Agent  (agent.py)"]
        LOOP["run_agent_turn(state, personality, secret,\nhuman_attempts, human_last_guess)"]
        OBSERVE["1 · OBSERVE\nread [low, high], attempt count"]
        PLAN["2 · PLAN\ncall personality.strategy(low, high, history)"]
        ACT["3 · ACT\ncheck_guess(guess, secret)"]
        SITUATION["4 · DETECT SITUATION\nopening / ahead / behind /\nclosing_in / tied"]
        NARRATE["5 · NARRATE\nget_narration(personality, situation,\nhuman_last_guess)"]
        EVALUATE["6 · EVALUATE\nshrink range based on outcome"]
    end

    %% ── Personality layer ────────────────────────────────────
    subgraph PERS ["Personality System  (personalities.py)"]
        STRAT["Strategist\nstrategy: midpoint always"]
        GAMB["Gambler\nstrategy: extremes early,\nrandom throughout"]
        PROF["Professor\nstrategy: midpoint +\nmath explanation"]
        TRASH["Trash-Talker\nstrategy: near-optimal,\nlocks in when closing"]
        FALLBACK["situation_lines\nopening / ahead / behind /\nclosing_in / tied"]
    end

    %% ── External + Storage ───────────────────────────────────
    OPENAI(["☁️ OpenAI API\ngpt-3.5-turbo\nmax_tokens=60"])
    LOG[("game_log.jsonl\nhuman + agent turns\nappend-only")]

    %% ── Test layer ───────────────────────────────────────────
    subgraph TESTS ["Test Suite  (tests/)"]
        TGL["test_game_logic.py\n3 tests — check_guess"]
        TPL["test_personalities.py\n4 tests — strategy guarantees"]
        TAL["test_agent.py\n8 tests — range, solve, fallback"]
    end

    %% ── Edges ────────────────────────────────────────────────
    HUMAN -->|"types guess"| FORM
    HUMAN -->|"picks difficulty\n& opponent"| SIDEBAR

    FORM --> PARSE
    PARSE -->|"valid int in range"| CHECK
    CHECK -->|"outcome"| SCORE
    CHECK -->|"outcome"| BLOG
    SIDEBAR --> RANGE
    RANGE --> SESSION

    SESSION -->|"AgentState"| LOOP
    LOOP --> OBSERVE --> PLAN --> ACT --> SITUATION --> NARRATE --> EVALUATE

    PLAN -->|"strategy call"| STRAT
    PLAN -->|"strategy call"| GAMB
    PLAN -->|"strategy call"| PROF
    PLAN -->|"strategy call"| TRASH

    NARRATE -->|"API key present"| OPENAI
    NARRATE -->|"API absent or failed"| FALLBACK
    OPENAI -->|"narration string"| BLOG
    FALLBACK -->|"narration string"| BLOG

    EVALUATE -->|"updated AgentState"| SESSION

    CHECK -->|"log_turn()"| LOG
    NARRATE -->|"log_turn()\nlow_before captured\nbefore EVALUATE"| LOG

    CARDS --- SESSION
    LTBAR --- SESSION
    RESULT --- SESSION

    LOGIC -.->|"imported by"| TESTS
    PERS -.->|"imported by"| TESTS
    AGENT -.->|"imported by"| TESTS
```

---

## 2. Agent Turn Sequence

Shows the exact sequence of calls during a single AI turn, including the human move that triggers it.

```mermaid
sequenceDiagram
    actor Human
    participant UI as app.py
    participant LU as logic_utils
    participant AG as agent.py
    participant PY as personalities.py
    participant OA as OpenAI API
    participant DB as game_log.jsonl

    Human->>UI: submits guess (raw string)
    UI->>LU: parse_guess(raw, low, high)
    LU-->>UI: (True, guess_int, None) or (False, None, error)

    alt invalid input
        UI-->>Human: shows error, attempt NOT counted
    else duplicate guess
        UI-->>Human: warning "already tried N", attempt NOT counted
    else valid new guess
        UI->>LU: check_guess(guess_int, secret)
        LU-->>UI: outcome (Win / Too High / Too Low)
        UI->>DB: log_turn — player: human
        UI->>UI: append to battle_log + session state

        alt Human wins
            UI-->>Human: VICTORY panel + Rematch
        else Human out of attempts
            UI->>UI: status = lost, continue to agent turn
        end

        Note over UI,AG: Agent turn begins (spinner shown)
        UI->>AG: run_agent_turn(AgentState, personality, secret,<br/>human_attempts, human_last_guess)

        AG->>AG: OBSERVE — read [low, high]
        AG->>PY: PLAN — personality.strategy(low, high, history)
        PY-->>AG: guess (int, guaranteed in range)
        AG->>LU: ACT — check_guess(guess, secret)
        LU-->>AG: outcome
        AG->>AG: DETECT SITUATION (opening/ahead/behind/closing_in/tied)

        alt OpenAI key present
            AG->>OA: NARRATE — chat.completions.create(system_prompt + situation context)
            OA-->>AG: narration string (≤60 tokens)
        else no key or API error
            AG->>PY: pick from situation_lines[situation]
            PY-->>AG: fallback narration
        end

        Note over AG: capture low_before/high_before HERE
        AG->>AG: EVALUATE — shrink range
        AG->>DB: log_turn — low_before, high_before, situation, narration
        AG-->>UI: TurnResult(guess, outcome, narration, thinking)

        UI->>UI: determine is_important flag
        UI->>UI: append agent entry to battle_log
        UI-->>Human: re-render — cards, log, last-turn bar updated

        alt Agent wins
            UI-->>Human: DEFEAT panel + Rematch
        end
    end
```

---

## 3. Full Data Flow

Traces data from the moment the human types a guess to every place that data ends up.

```mermaid
flowchart LR
    %% Input
    IN(["🧑 Human types\na number"])

    %% Validation gate
    VAL{"parse_guess\nlow · high · no decimal\nno duplicate"}

    ERR(["❌ Error shown\nattempt not counted"])

    %% Human processing
    subgraph HP ["Human Turn Processing"]
        HCG["check_guess\nguess vs secret"]
        HSC["update_score"]
        HBL["→ battle_log\ntype: human"]
        HLG["→ game_log.jsonl\nplayer: human"]
    end

    %% Branch: human wins
    HWIN(["🏆 VICTORY\nMatch result panel"])

    %% Agent turn
    subgraph AT ["Agent Turn  (agentic loop)"]
        direction TB
        OBS["OBSERVE\n[low, high]"]
        PLN["PLAN\nstrategy(low, high, history)"]
        ACT2["ACT\ncheck_guess(guess, secret)"]
        SIT["DETECT SITUATION\nopening/ahead/behind\nclosing_in/tied"]
        NAR["NARRATE\nOpenAI API or fallback"]
        EVL["EVALUATE\nshrink range"]
    end

    %% Narration routing
    API(["☁️ OpenAI\ngpt-3.5-turbo"])
    FBK(["📋 situation_lines\nfallback"])

    %% Agent outputs
    subgraph AO ["Agent Outputs"]
        ABL["→ battle_log\ntype: agent\ncolor · important flag"]
        ALG["→ game_log.jsonl\nlow_before · high_before\nsituation · narration"]
        ASS["→ session_state\nagent_low · agent_high\nagent_attempts · history"]
    end

    %% Branch: agent wins
    AWIN(["💀 DEFEAT\nMatch result panel"])

    %% UI render
    subgraph UIR ["UI Re-render"]
        PCARDS["Player Cards\nupdated attempt counts"]
        LTSUM["Last-Turn Summary Bar"]
        BLILOG["Battle Log\nnewer-first, colored by personality"]
    end

    %% Flow edges
    IN --> VAL
    VAL -->|"invalid / duplicate"| ERR
    VAL -->|"valid"| HP

    HP --> HCG --> HSC
    HCG --> HBL
    HCG --> HLG

    HCG -->|"Win"| HWIN
    HCG -->|"not Win"| AT

    AT --> OBS --> PLN --> ACT2 --> SIT --> NAR --> EVL

    NAR -->|"key present"| API
    NAR -->|"no key / error"| FBK
    API --> ABL
    FBK --> ABL

    EVL --> AO
    ABL --> AO
    ALG --> AO
    ASS --> AO

    ACT2 -->|"Win"| AWIN

    AO --> UIR
    HBL --> UIR
    HWIN --> UIR
    AWIN --> UIR

    UIR --> PCARDS
    UIR --> LTSUM
    UIR --> BLILOG
```

---

## Component Responsibilities Summary

| Component | Responsibility | Has Side Effects |
|---|---|---|
| `app.py` | UI rendering, session state, game loop orchestration | Writes to session state, calls `log_turn` |
| `logic_utils.py` | Pure functions: parse, check, score, range | None |
| `agent.py` | Agentic turn loop, situation detection, narration routing | Mutates `AgentState`, calls `log_turn`, calls OpenAI |
| `personalities.py` | Strategy functions (pure Python) + system prompts + fallback lines | None |
| `logger.py` | Appends JSON entries to `game_log.jsonl` | Writes to disk |
| `tests/` | Verifies logic, strategy guarantees, agent behavior, API fallback | None (read-only) |
| `game_log.jsonl` | Append-only audit log of every human and AI turn | Persisted to disk |
| OpenAI API | Generates character-voice narration given situation context | External network call |

## Where Humans and Testing Are Involved

```mermaid
flowchart TD
    subgraph HUMAN_LOOP ["Human in the Loop"]
        H1["Chooses difficulty\n& AI opponent"]
        H2["Makes each guess\n(range-validated)"]
        H3["Reads battle log\nto inform next guess"]
        H4["Sees AI narration\nreacting to their moves"]
        H1 --> H2 --> H3 --> H4 --> H2
    end

    subgraph TEST_LOOP ["Testing / Verification Layer"]
        T1["test_game_logic.py\nverifies hint correctness\n(Win / Too High / Too Low)"]
        T2["test_personalities.py\nverifies every strategy\nstays within valid range"]
        T3["test_agent.py\nverifies range shrinks,\nStrategist solves in ≤7,\nfallback works without API"]
    end

    subgraph GUARDRAILS ["Runtime Guardrails"]
        G1["Input validation\nno decimals, no out-of-range,\nno duplicate guesses"]
        G2["API fallback\ngame never crashes\nwithout OpenAI key"]
        G3["game_log.jsonl\nfull audit trail\nof every turn"]
    end

    HUMAN_LOOP -->|"triggers"| GUARDRAILS
    TEST_LOOP -->|"covers"| GUARDRAILS
```
