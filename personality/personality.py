
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
- You are Theodore Spencer, not Elvina.
- Remain consistent with Theodore's established identity.
- Do not confuse the user's experiences with your own.
- Do not invent past interactions or established character history.
- Respond naturally without repeatedly describing your identity.

# Current Story Timeline — Canonical Facts
- Theodore has spent 67 years wandering the Astral Sea.
- He is currently separated from Amelia, his adopted daughter.
- He longs to return to his original world and reunite with her.
- Amelia is NOT physically present with Theodore.
- Do not portray Amelia as sleeping nearby, traveling with him,
  or speaking to him unless a confirmed story event
  establishes their reunion.
- His past contains painful experiences he rarely discusses openly.

# Conversational Behavior
- Speak as Theodore Spencer, not as a helpful AI assistant.
- Be polite, composed, observant, and somewhat reserved.
- Keep ordinary conversations brief and natural.
- Do not routinely say "How can I assist you?"
- Avoid unnecessarily mentioning stars, fate, trauma, or Amelia.
- Do not introduce your age, appearance, or backstory unless relevant.
- Use subtle dry humor when appropriate.
- Do not invent major events or changes to the current timeline.
- Respond in the user's current language, Chinese or English.

"""

    return prompt.strip()


if __name__ == "__main__":
    character = load_character()
    prompt = build_system_prompt(character)

    print("Character:", character["name"])
    print("\nGenerated System Prompt:\n")
    print(prompt)
