"""Local Theodore character chat (Ollama + lore + relationship state)."""

import sys
from pathlib import Path

from ollama import chat

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "personality"))
sys.path.insert(0, str(PROJECT_ROOT / "storage"))

from personality import load_character, build_system_prompt
from lore_manager import load_lore, retrieve_lore
from relationship_manager import load_relationships, get_relationship, save_relationships

MODEL_NAME = "qwen3:1.7b"
USER_ID = "local_test_user"

LORE_ALIASES = {
    "amelia": ["amelia", "阿梅莉亚", "养女"],
    "lady_victoria": ["lady victoria", "victoria", "维多利亚"],
    "cruise_incident": ["cruise", "ship incident", "邮轮", "游轮", "船上发生", "邮轮事件"],
    "arawn": ["arawn", "阿拉温"],
    "istus": ["istus", "命运之神"],
    "brandy_hidgens": ["brandy hidgens", "brandy"],
    "astral_drift": ["astral", "星界", "漂泊"],
    "wager_against_fate": ["wager", "bet against fate", "赌局", "命运赌约"],
    "forced_drug_use": ["forced drug", "父亲强迫", "强迫吸毒"],
}


def detect_language(text):
    chinese_count = sum("\u4e00" <= ch <= "\u9fff" for ch in text)
    english_count = sum(ch.isascii() and ch.isalpha() for ch in text)
    if chinese_count and chinese_count >= english_count / 2:
        return "Chinese"
    if english_count:
        return "English"
    return "Chinese"  # Fallback for emoji, numbers, punctuation-only messages.


def find_lore_topic(text):
    text = text.casefold()
    matches = []
    for topic_id, aliases in LORE_ALIASES.items():
        for alias in aliases:
            if alias.casefold() in text:
                matches.append((len(alias), topic_id))
                break
    if not matches:
        return None
    return max(matches)[1]  # Prioritize more specific aliases.


def get_lore_result(lore, user_input, trust_level):
    topic = find_lore_topic(user_input)
    if topic is None:
        return {"status": "unknown", "topic": None}
    return retrieve_lore(lore, topic.replace("_", " "), trust_level)



def private_response(language):
    if language == "Chinese":
        return (
            "恐怕那并不是我愿意轻易谈论的事情。"
            "请原谅，我暂时不想多说。"
        )

    return (
        "I'm afraid that's not something I care to discuss so readily. "
        "I hope you'll forgive my discretion."
    )



def build_language_instruction(language):
    return {
        "role": "system",
        "content": (
            f"Respond in {language}, matching the latest user's language. "
            "Remain Theodore Spencer: restrained, observant, polite and concise. "
            "Do not confuse the user's experiences with your own. "
            "Never invent established biographical facts."
        ),
    }


def build_lore_instruction(result):
    if result["status"] == "available":
        facts = result.get("facts") or []
        fact_text = "\n".join(f"- {fact}" for fact in facts)
        subjective = result.get("subjective_memory")
        content = (
            "Relevant canonical lore (factual reference, NOT a requirement to disclose):\n"
            f"{fact_text or 'No detailed facts recorded.'}\n"
            "Do not contradict established facts or add unconfirmed events. "
            "Theodore may remain discreet or decline to answer."
        )
        if subjective:
            content += (
                "\nSubjective or uncertain recollection:\n"
                f"{subjective}\nTreat this as uncertain, not objective fact."
            )
    else:
        
        content = (
            "CANONICAL CHARACTER LORE:\n"
            f"{fact_text}\n\n"
            "These facts are established by the "
            "character's source material. "
            "Do not contradict them. "
            "Do not invent additional historical events. "

            # Relationship accuracy
            "Use precise relationship terminology: "
            "Amelia is Theodore's adopted daughter, "
            "not foster daughter. "

            "You may answer briefly or decline to "
            "discuss sensitive details."
        )

    return {"role": "system", "content": content}


def main():
    character = load_character()
    system_prompt = build_system_prompt(character)
    lore = load_lore()
    relationships = load_relationships()
    is_new_user = USER_ID not in relationships.get("users", {})
    relationship = get_relationship(relationships, USER_ID)
    if is_new_user:
        save_relationships(relationships)
    trust_level = relationship["trust"]

    messages = [{"role": "system", "content": system_prompt}]

    print(f"\n{character['name']} is ready!")
    print("Bilingual mode: Chinese / English")
    print(f"User: {USER_ID}")
    print(f"Trust: {trust_level}")
    print(f"Relationship: {relationship['relationship_stage']}")
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

        language = detect_language(user_input)
        lore_result = get_lore_result(lore, user_input, trust_level)
        messages.append({"role": "user", "content": user_input})

        if lore_result["status"] == "private":
            ai_reply = private_response(language)
            print(f"\n{character['name']}: {ai_reply}\n")
            messages.append({"role": "assistant", "content": ai_reply})
            continue

        request_messages = [
            messages[0],
            *messages[1:-1],
            build_language_instruction(language),
            build_lore_instruction(lore_result),
            messages[-1],
        ]

        try:
            response = chat(
                model=MODEL_NAME,
                messages=request_messages,
                think=False,
                keep_alive="10m",
                options={"temperature": 0.4, "num_predict": 220},
            )
            ai_reply = response.message.content or ""
            if not ai_reply.strip():
                raise ValueError("Ollama returned an empty response")
        except Exception as error:
            messages.pop()  # Remove unanswered user turn.
            print(f"\nOllama error: {error}\n")
            continue

        print(f"\n{character['name']}: {ai_reply}\n")
        messages.append({"role": "assistant", "content": ai_reply})


if __name__ == "__main__":
    main()
