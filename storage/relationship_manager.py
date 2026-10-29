
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MEMORY_FILE = PROJECT_ROOT / "memory" / "relationships.json"


def load_relationships():
    """Load saved relationships from disk."""
    if not MEMORY_FILE.exists():
        return {"users": {}}

    with open(MEMORY_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_relationships(data):
    """Save relationships to disk."""
    with open(MEMORY_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def get_relationship(data, user_id):
    """Get a user's relationship, creating one if missing."""
    users = data["users"]

    if user_id not in users:
        users[user_id] = {
            "trust": 10,
            "interaction_count": 0,
            "relationship_stage": "stranger",
            "shared_experiences": []
        }

    return users[user_id]


def get_relationship_stage(trust):
    """Determine relationship stage from trust."""

    if trust < 25:
        return "stranger"
    elif trust < 50:
        return "acquaintance"
    elif trust < 80:
        return "friend"
    else:
        return "trusted"


def update_trust(relationship, change):
    """Update trust while keeping it within bounds."""

    old_trust = relationship["trust"]

    new_trust = max(
        0,
        min(100, old_trust + change)
    )

    relationship["trust"] = new_trust
    relationship["relationship_stage"] = (
        get_relationship_stage(new_trust)
    )

    return old_trust, new_trust



if __name__ == "__main__":
    data = load_relationships()
    user = get_relationship(data, "local_test_user")

    print("Trust:", user["trust"])
    print("Stage:", user["relationship_stage"])