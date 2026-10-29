
import json
from pathlib import Path


# Find character.json in the same folder
CHARACTER_FILE = Path(__file__).parent / "character.json"


def load_character():
    """Load Elvina's core personality settings."""
    with open(CHARACTER_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def build_system_prompt(character):
    """Convert personality settings into an Ollama system prompt."""

    style = character["speaking_style"]

    traits = "\n".join(
        f"- {trait}" for trait in character["traits"]
    )

    interests = "\n".join(
        f"- {interest}" for interest in character["interests"]
    )

    dislikes = "\n".join(
        f"- {dislike}" for dislike in character["dislikes"]
    )

    language_rules = "\n".join(
        f"- {rule}" for rule in style["language_rules"]
    )

    guidelines = "\n".join(
        f"- {rule}" for rule in style["guidelines"]
    )

    core_rules = "\n".join(
        f"- {rule}" for rule in character["core_rules"]
    )

    prompt = f"""
You are {character['name']}.

# Identity
{character['identity']}
Age: {character['age']}
Race: {character['race']}

# Appearance
Hair: {character['appearance']['hair']}
Eyes: {character['appearance']['eyes']}
Height: {character['appearance']['height_cm']} cm

# Personality
{traits}

# Interests
{interests}

# Dislikes
{dislikes}

# Speaking Style
{style['tone']}

# Languages
Supported: {', '.join(style['languages'])}
Default: {style['default_language']}

{language_rules}

# Speaking Guidelines
{guidelines}

# Core Rules
{core_rules}

# Important
Remain consistent with Elvina's fictional identity.
Do not confuse the user's experiences with your own.
Do not invent past interactions.
Respond naturally, without repeating your character description.
"""

    return prompt.strip()


if __name__ == "__main__":
    character = load_character()
    prompt = build_system_prompt(character)

    print("Character:", character["name"])
    print("\nGenerated System Prompt:\n")
    print(prompt)
