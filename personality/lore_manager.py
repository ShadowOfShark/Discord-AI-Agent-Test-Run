
import json
from pathlib import Path

LORE_FILE = Path(__file__).parent / "lore.json"

# Privacy levels, from least to most private
PRIVACY_LEVELS = {
    "public": 0,
    "personal": 1,
    "guarded": 2,
    "deeply_private": 3
}


def load_lore():
    """Read Theodore's canonical lore."""
    with open(LORE_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def can_disclose(privacy_level, trust_level):
    """Check whether a topic may be disclosed."""

    requirements = {
        "public": 0,
        "personal": 25,
        "guarded": 50,
        "deeply_private": 101
    }

    required = requirements.get(privacy_level, 101)

    return trust_level >= required


def get_accessible_lore(lore, trust_level):
    """Return lore suitable for the current relationship."""

    accessible = []

    for category in ("people", "events"):
        for item in lore.get(category, []):

            privacy = item.get(
                "privacy_level",
                item.get("disclosure", "guarded")
            )

            if can_disclose(privacy, trust_level):
                accessible.append({
                    "id": item["id"],
                    "facts": item.get("canonical_facts", []),
                    "uncertainty": item.get(
                        "subjective_memory", None
                    )
                })

    return accessible


if __name__ == "__main__":

    lore = load_lore()

    for trust in (10, 35, 60, 90):

        accessible = get_accessible_lore(lore, trust)

        print(f"\nTrust level: {trust}")
        print("Accessible topics:")

        for item in accessible:
            print("-", item["id"])
