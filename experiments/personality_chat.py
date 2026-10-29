
import sys
from pathlib import Path
from ollama import chat

# ==========================================
# 1. Project setup
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(
    0,
    str(PROJECT_ROOT / "personality")
)

from personality import load_character, build_system_prompt
from lore_manager import load_lore, retrieve_lore


# ==========================================
# 2. Load character and lore
# ==========================================

character = load_character()
system_prompt = build_system_prompt(character)
lore = load_lore()

MODEL_NAME = "qwen3:1.7b"

# Temporary trust level for testing
trust_level = 35

messages = [
    {
        "role": "system",
        "content": system_prompt
    }
]


# ==========================================
# 3. Language detection
# ==========================================

def detect_language(text):
    chinese_count = sum(
        1 for char in text
        if "\u4e00" <= char <= "\u9fff"
    )

    english_count = sum(
        1 for char in text
        if char.isascii() and char.isalpha()
    )

    if chinese_count > 0 and english_count > 0:
        if chinese_count >= english_count / 2:
            return "Chinese"
        return "English"

    if chinese_count > 0:
        return "Chinese"

    return "English"


def build_language_instruction(language):
    return {
        "role": "system",
        "content": (
            f"Respond in {language}. "
            "Follow the language of the latest user message. "
            "Maintain Theodore's established personality. "
            "Use restrained, polite and natural language. "
            "Avoid excessive poetic monologues. "
            "Do not invent biographical facts."
        )
    }


# ==========================================
# 4. Lore topic matching
# ==========================================

# Add aliases for questions that do not
# contain the exact English lore ID.

LORE_ALIASES = {
    "amelia": [
        "amelia", "阿梅莉亚", "养女"
    ],
    "lady_victoria": [
        "lady victoria", "victoria", "维多利亚"
    ],
    "cruise_incident": [
        "cruise", "ship incident", "邮轮", "游轮",
        "船上发生", "邮轮事件"
    ],
    "arawn": [
        "arawn", "阿拉温"
    ],
    "istus": [
        "istus", "命运之神"
    ],
    "brandy_hidgens": [
        "brandy hidgens", "brandy"
    ],
    "astral_drift": [
        "astral", "星界", "漂泊"
    ],
    "wager_against_fate": [
        "wager", "bet against fate", "赌局", "命运赌约"
    ],
    "forced_drug_use": [
        "forced drug", "父亲强迫", "强迫吸毒"
    ]
}


def find_lore_topic(user_input):
    text = user_input.casefold()

    for topic_id, aliases in LORE_ALIASES.items():
        if any(alias.casefold() in text for alias in aliases):
            return topic_id

    return None


def get_lore_result(user_input):
    topic_id = find_lore_topic(user_input)

    if topic_id is None:
        return {
            "status": "unknown",
            "topic": None
        }

    # Convert the matched topic to the format
    # expected by the existing lore_manager.
    query = topic_id.replace("_", " ")

    return retrieve_lore(
        lore,
        query,
        trust_level
    )


# ==========================================
# 5. Private topic responses
# ==========================================

def private_response(language, topic):
    """Return a restrained refusal without
    generating private event details."""

    if language == "Chinese":
        return (
            "恐怕那并不是我愿意轻易谈论的事情。"
            "请原谅，我暂时不想多说。"
        )

    return (
        "I'm afraid that's not something "
        "I care to discuss so readily. "
        "I hope you'll forgive my discretion."
    )


# ==========================================
# 6. Build lore instruction
# ==========================================

def build_lore_instruction(result):
    status = result["status"]

    if status == "available":
        facts = result.get("facts", [])
        subjective = result.get("subjective_memory")

        fact_text = "\n".join(
            f"- {fact}" for fact in facts
        )

        if not fact_text:
            fact_text = "No detailed facts recorded."

        content = (
            "CANONICAL CHARACTER LORE:\n"
            f"{fact_text}\n\n"
            "These facts are established by the "
            "character's source material. "
            "Do not contradict them. "
            "Do not invent additional historical events. "
            "You may answer briefly or decline to "
            "discuss sensitive details."
        )

        if subjective:
            content += (
                "\n\nUNCERTAIN PERSONAL MEMORY:\n"
                f"{subjective}\n"
                "Treat this as Theodore's uncertain "
                "recollection, not objective certainty."
            )

    else:
        content = (
            "No relevant canonical facts were retrieved. "
            "Do not invent established personal history. "
            "If asked about unknown biographical details, "
            "politely acknowledge uncertainty. "
            "For ordinary conversation, respond naturally."
        )

    return {
        "role": "system",
        "content": content
    }


# ==========================================
# 7. Main conversation
# ==========================================

print(f"\n{character['name']} is ready!")
print("Bilingual mode: Chinese / English")
print(f"Current trust level: {trust_level}")
print("Type 'exit' to quit.\n")


while True:
    try:
        user_input = input("You: ").strip()

    except (KeyboardInterrupt, EOFError):
        print("\nConversation ended.")
        break

    if user_input.lower() == "exit":
        print("Conversation ended.")
        break

    if not user_input:
        continue

    # Identify current language
    language = detect_language(user_input)

    # Find relevant lore and disclosure status
    lore_result = get_lore_result(user_input)

    # Save user message in current session
    messages.append({
        "role": "user",
        "content": user_input
    })

    # ======================================
    # Private lore: skip free generation
    # ======================================

    if lore_result["status"] == "private":
        ai_reply = private_response(
            language,
            lore_result["topic"]
        )

        print(
            f"\n{character['name']}: "
            f"{ai_reply}\n"
        )

        messages.append({
            "role": "assistant",
            "content": ai_reply
        })

        continue

    # ======================================
    # Normal conversation
    # ======================================

    language_instruction = (
        build_language_instruction(language)
    )

    lore_instruction = (
        build_lore_instruction(lore_result)
    )

    # Core personality first,
    # followed by history and current rules.
    request_messages = [
        messages[0],
        *messages[1:-1],
        language_instruction,
        lore_instruction,
        messages[-1]
    ]

    try:
        response = chat(
            model=MODEL_NAME,
            messages=request_messages,
            think=False,
            keep_alive="10m",
            options={
                "temperature": 0.4,
                "num_predict": 220
            }
        )

        ai_reply = response.message.content

        print(
            f"\n{character['name']}: "
            f"{ai_reply}\n"
        )

        messages.append({
            "role": "assistant",
            "content": ai_reply
        })

    except Exception as error:
        # Remove the unanswered user message.
        messages.pop()

        print(f"\nOllama error: {error}\n")
