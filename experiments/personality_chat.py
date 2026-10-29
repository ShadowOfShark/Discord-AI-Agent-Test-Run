
import sys
from pathlib import Path
from ollama import chat

# ----------------------------------------
# 1. Project paths
# ----------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(
    0,
    str(PROJECT_ROOT / "personality")
)

from personality import load_character, build_system_prompt


# ----------------------------------------
# 2. Load Elvina's personality
# ----------------------------------------

character = load_character()
system_prompt = build_system_prompt(character)

messages = [
    {
        "role": "system",
        "content": system_prompt
    }
]


# ----------------------------------------
# 3. Detect the user's language
# ----------------------------------------

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
        # Simple heuristic for mixed-language input
        if chinese_count >= english_count / 2:
            return "Chinese"
        return "English"

    if chinese_count > 0:
        return "Chinese"

    return "English"


# ----------------------------------------
# 4. Build a per-message language rule
# ----------------------------------------

def build_language_instruction(language):
    return {
        "role": "system",
        "content": (
            f"IMPORTANT: Respond in {language}. "
            f"The user's latest message is primarily {language}. "
            "Do not respond in another language unless "
            "the user explicitly requests it. "
            "Maintain Elvina's personality. "
            "Keep casual replies natural and concise. "
            "Do not invent memories or facts about the user. "
            "Distinguish Elvina from the user and their pets."
        )
    }


# ----------------------------------------
# 5. Main conversation
# ----------------------------------------

print(f"\n{character['name']} is ready!")
print("Bilingual mode: Chinese / English")
print("Type 'exit' to quit.\n")

while True:

    user_input = input("You: ").strip()

    if user_input.lower() == "exit":
        print(f"{character['name']}: Goodbye!")
        break

    if not user_input:
        continue

    language = detect_language(user_input)

    language_instruction = build_language_instruction(language)

    messages.append({
        "role": "user",
        "content": user_input
    })

    # Keep the original character identity.
    # Add the current language instruction.
    # Include previous conversation history.
    request_messages = [
        messages[0],
        *messages[1:-1],
        language_instruction,
        messages[-1]
    ]

    try:
        response = chat(
            model="qwen3:1.7b",
            messages=request_messages,
            think=False,
            keep_alive="10m",
            options={
                "temperature": 0.5,
                "num_predict": 180
            }
        )

        ai_reply = response.message.content

        print(f"\n{character['name']}: {ai_reply}\n")

        messages.append({
            "role": "assistant",
            "content": ai_reply
        })

    except Exception as error:
        # The failed user message should not remain
        # in the conversation history.
        messages.pop()
        print(f"\nError: {error}\n")
