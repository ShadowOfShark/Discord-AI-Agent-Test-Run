
import time
from ollama import chat

for i in range(2):
    start = time.perf_counter()

    response = chat(
        model="qwen3:1.7b",
        messages=[
            {
                "role": "user",
                "content": "请只回复：你好"
            }
        ],
        think=False,
        keep_alive="10m"
    )

    elapsed = time.perf_counter() - start

    print(f"Test {i + 1}")
    print(f"Response: {response.message.content}")
    print(f"Time: {elapsed:.2f} seconds")
    print("-----------------------")
