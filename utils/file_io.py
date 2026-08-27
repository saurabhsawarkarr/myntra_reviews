import json
from pathlib import Path

def load_json(path: str) -> list | dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data: list | dict, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_config(filename: str) -> dict:
    import os
    return load_json(os.path.join("config", filename))
