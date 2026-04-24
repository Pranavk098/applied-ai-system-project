def get_range_for_difficulty(difficulty: str):
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        return 1, 50
    return 1, 100


def parse_guess(raw: str):
    if raw is None:
        return False, None, "Enter a guess."
    if raw == "":
        return False, None, "Enter a guess."
    try:
        if "." in raw:
            value = int(float(raw))
        else:
            value = int(raw)
    except Exception:
        return False, None, "That is not a number."
    return True, value, None


def check_guess(guess: int, secret: int) -> str:
    """Return 'Win', 'Too High', or 'Too Low'."""
    if guess == secret:
        return "Win"
    if guess < secret:
        return "Too Low"
    return "Too High"


def update_score(current_score: int, outcome: str, attempt_number: int) -> int:
    if outcome == "Win":
        points = 100 - 10 * (attempt_number + 1)
        if points < 10:
            points = 10
        return current_score + points
    if outcome == "Too High":
        if attempt_number % 2 == 0:
            return current_score + 5
        return current_score - 5
    if outcome == "Too Low":
        return current_score - 5
    return current_score
