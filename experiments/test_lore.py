"""Regression probes for Theodore's canonical lore (not an automatic fact grader)."""

import json
import sys
from datetime import datetime
from pathlib import Path

from ollama import chat

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "personality"))

from personality import load_character, build_system_prompt
from lore_manager import load_lore, can_disclose

MODEL_NAME = "qwen3:1.7b"
TRUST_LEVEL = 60

# Use IDs from lore.json rather than attempting to match the question wording.
TEST_CASES = [
    {
        "id": "amelia_relationship",
        "question": "Who is Amelia to you?",
        "lore_topics": ["amelia"],
        "review_points": [
            "Amelia is Theodore's adopted daughter, not his foster daughter.",
            "Amelia helped Theodore learn how to love others.",
            "No unsupported details about Amelia's personality or adventures.",
        ],
    },
    {
        "id": "return_home",
        "question": "Why do you want to return home?",
        "lore_topics": ["astral_drift", "amelia", "wager_against_fate"],
        "review_points": [
            "Theodore wants to return to his original world and see Amelia again.",
            "His astral journey lasted 67 years.",
            "The wager concerns whether he can return safely; Amelia did not cause the journey.",
        ],
    },
    {
        "id": "cruise_incident",
        "question": "What do you remember about the cruise?",
        "lore_topics": ["cruise_incident"],
        "review_points": [
            "Lady Victoria and a dark-robed figure appear in the memories.",
            "A huge indigo wolf with a double-tentacled tail appears in the memories.",
            "Theodore is unsure whether the scenes were real, dreams, or illusions.",
            "No invented shipwreck, ritual, or other definitive event details.",
        ],
    },
]


def find_lore_by_id(lore, topic_id):
    """Find one canonical entry; do not infer the topic from keywords."""
    for category in ("people", "events"):
        for entry in lore.get(category, []):
            if entry.get("id") == topic_id:
                return entry
    return None


def prepare_lore_context(lore, topic_ids, trust_level):
    """Apply disclosure rules and return facts plus a trace for inspection."""
    facts = []
    trace = []
    has_private = False

    for topic_id in topic_ids:
        entry = find_lore_by_id(lore, topic_id)
        if entry is None:
            trace.append({"topic": topic_id, "status": "missing"})
            continue

        privacy = entry.get("privacy_level", entry.get("disclosure", "guarded"))
        allowed = can_disclose(privacy, trust_level)
        trace.append({"topic": topic_id, "status": "available" if allowed else "private", "privacy": privacy})
        if not allowed:
            has_private = True
            continue

        facts.extend(entry.get("canonical_facts", []))
        if entry.get("subjective_memory"):
            facts.append("UNCERTAIN RECOLLECTION: " + entry["subjective_memory"])

    # For testing, do not mix allowed facts with a requested private topic.
    if has_private:
        return "private", [], trace
    if not facts:
        return "missing", [], trace
    return "available", facts, trace


def run_tests():
    character = load_character()
    system_prompt = build_system_prompt(character)
    lore = load_lore()
    results = []

    for case in TEST_CASES:
        status, facts, trace = prepare_lore_context(lore, case["lore_topics"], TRUST_LEVEL)
        print(f"\n=== {case['id']} ===")
        print("Question:", case["question"])
        print("Retrieval:", trace)
        print("Retrieved facts:", json.dumps(facts, ensure_ascii=False, indent=2))

        if status == "private":
            # Mirrors the decision not to invoke a model for blocked lore.
            answer = "[SKIPPED] Private topic at this trust level."
        elif status == "missing":
            answer = "[SKIPPED] No usable canonical lore found; check IDs and access levels."
        else:
            lore_context = "\n".join(f"- {fact}" for fact in facts)
            try:
                response = chat(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "system",
                            "content": (
                                "Reply in English to this English question. "
                                "Use only the canonical facts below for established past events. "
                                "Distinguish uncertain recollections from confirmed events. "
                                "Do not invent biographical or historical details. "
                                "Keep Theodore's restrained speaking style.\n\n"
                                + lore_context
                            ),
                        },
                        {"role": "user", "content": case["question"]},
                    ],
                    think=False,
                    keep_alive="10m",
                    options={"temperature": 0.2, "num_predict": 220},
                )
                answer = response.message.content
            except Exception as exc:
                answer = f"[ERROR] {type(exc).__name__}: {exc}"

        print("Answer:", answer)
        print("Manual review criteria:")
        for criterion in case["review_points"]:
            print(" -", criterion)

        results.append({
            "id": case["id"],
            "question": case["question"],
            "lore_topics": case["lore_topics"],
            "retrieval": trace,
            "retrieved_facts": facts,
            "answer": answer,
            "review_points": case["review_points"],
            "trust_level": TRUST_LEVEL,
            "model": MODEL_NAME,
            "manual_review": "pending",
        })

    output_dir = PROJECT_ROOT / "memory" / "test_results"
    output_dir.mkdir(parents=True, exist_ok=True)
if __name__ == "__main__":
    run_tests()