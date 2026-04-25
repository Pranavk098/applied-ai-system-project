"""
eval.py — Offline evaluation harness for Number Duel AI personalities.

Usage:
    python eval.py

Runs each personality against 21 fixed secrets in the Normal range (1-100,
limit 8 guesses). Prints a summary table. No API calls, no file logging.
"""
import random
from agent import AgentState, run_agent_turn
from personalities import list_personalities, get_personality

SECRETS  = [1, 6, 11, 16, 21, 26, 31, 36, 41, 46, 51, 56, 61, 66, 71, 76, 81, 86, 91, 96, 100]
LOW, HIGH = 1, 100
LIMIT     = 8


def simulate(personality_key: str, secrets: list[int]) -> dict:
    guesses_list = []
    wins_within_limit = 0
    total_wins = 0

    for secret in secrets:
        state = AgentState(low=LOW, high=HIGH)
        for _ in range(HIGH - LOW + 1):     # theoretical max for any strategy in this range
            if state.status == "won":
                break
            run_agent_turn(state, get_personality(personality_key), secret=secret, log=False)

        solved = state.status == "won"
        guesses_taken = state.attempts

        if solved:
            total_wins += 1
            guesses_list.append(guesses_taken)
            if guesses_taken <= LIMIT:
                wins_within_limit += 1

    n = len(secrets)
    avg  = sum(guesses_list) / len(guesses_list) if guesses_list else float("inf")
    worst = max(guesses_list) if guesses_list else float("inf")
    win_rate = f"{total_wins}/{n}"
    within   = f"{wins_within_limit}/{n}"
    return {"avg": avg, "worst": worst, "win_rate": win_rate, "within_limit": within}


def main():
    random.seed(42)
    print("\nNumber Duel — AI Evaluation Harness")
    print(f"Secrets: {len(SECRETS)} fixed values in [{LOW}, {HIGH}]   Guess limit: {LIMIT}\n")

    header = f"{'Personality':<16} {'Avg Guesses':>12} {'Max Guesses':>12} {'Solved':>8} {'Within Limit':>14}"
    print(header)
    print("-" * len(header))

    for key in list_personalities():
        stats = simulate(key, SECRETS)
        avg_str = f"{stats['avg']:.1f}" if stats["avg"] != float("inf") else "DNF"
        max_str = str(stats["worst"]) if stats["worst"] != float("inf") else "DNF"
        print(
            f"{key:<16} {avg_str:>12} {max_str:>12} "
            f"{stats['win_rate']:>8} {stats['within_limit']:>14}"
        )

    print()


if __name__ == "__main__":
    main()
