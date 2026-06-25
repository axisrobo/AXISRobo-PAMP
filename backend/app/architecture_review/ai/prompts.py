"""Prompt loading helpers for EA Review agent."""
from __future__ import annotations

from pathlib import Path


PROMPT_DIR = Path(__file__).resolve().parent / "prompts"


def load_prompt(name: str) -> str:
    path = PROMPT_DIR / name
    return path.read_text(encoding="utf-8")


def get_review_prompt(review_type: str) -> str:
    if review_type == "App_Arch":
        return load_prompt("app_architect_review.md")
    return load_prompt("tech_architect_review.md")


def get_info_extract_prompt(review_type: str) -> str:
    if review_type == "App_Arch":
        return load_prompt("app_vision_to_json.md")
    return load_prompt("tech_vision_to_json.md")
