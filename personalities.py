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
