import json
from pathlib import Path

FILE_PATH = Path(__file__).with_name("simon_highscores.json")


def load_scores():
    if FILE_PATH.exists():
        try:
            with FILE_PATH.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except json.JSONDecodeError:
            pass
    return []


def save_scores(scores):
    # keep only top 3
    scores = sorted(scores, reverse=True)[:3]
    with FILE_PATH.open("w", encoding="utf-8") as f:
        json.dump(scores, f)
    return scores 