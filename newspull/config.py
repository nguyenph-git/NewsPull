import copy
import shutil
import tomllib
import tomli_w
from pathlib import Path

PREFS_PATH = Path.home() / ".newspull" / "preferences.toml"

DEFAULT_PREFS: dict = {
    "topics": {"ai": 1.0, "tech": 0.8, "politics": 0.3},
    "sources": {
        "reddit": ["r/MachineLearning", "r/technology"],
        "youtube": [],
        "rss": [],
        "hn": True,
    },
    "credibility": {"min_score": 0.5, "cross_ref_bonus": 0.2},
    "digester": {"style": "concise", "keypoints": 5},
}


def load_prefs() -> dict:
    PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not PREFS_PATH.exists():
        save_prefs(DEFAULT_PREFS)
        return copy.deepcopy(DEFAULT_PREFS)
    with open(PREFS_PATH, "rb") as f:
        return tomllib.load(f)


def save_prefs(prefs: dict) -> None:
    PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
    bak_path = PREFS_PATH.with_suffix(".toml.bak")
    if PREFS_PATH.exists():
        shutil.copy2(PREFS_PATH, bak_path)
    with open(PREFS_PATH, "wb") as f:
        tomli_w.dump(prefs, f)


def restore_prefs_backup() -> bool:
    bak_path = PREFS_PATH.with_suffix(".toml.bak")
    if bak_path.exists():
        shutil.copy2(bak_path, PREFS_PATH)
        return True
    return False
