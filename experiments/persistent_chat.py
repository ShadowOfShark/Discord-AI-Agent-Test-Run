
from ollama import chat
import json
from pathlib import Path

MEMORY_FILE = Path("memory/chat_history.json")

def save_memory(messages): ##将对话列表保存到 JSON 文件
    MEMORY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(MEMORY_FILE, "w", encoding="utf-8") as file:
        json.dump(
            messages,
            file,
            ensure_ascii=False,
            indent=2
        )

def load_memory(): ##从 JSON 文件恢复列表
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    return []
## 这段代码目前只负责保存和读取，没有连接 AI。


# Load previous conversation history
messages = load_memory()

print(f"Loaded {len(messages)} previous messages.")

while True:
    user_input = input("You: ")

    if user_input.lower() == "exit":
        break

    messages.append({
        "role": "user",
        "content": user_input
    })

    response = chat(
        model="qwen3:1.7b",
        messages=messages,
        think=False,
        keep_alive="10m"
    )

    ai_reply = response.message.content

    print(f"AI: {ai_reply}")

    messages.append({
        "role": "assistant",
        "content": ai_reply
    })

    save_memory(messages)
