from ollama import chat

messages = []

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


