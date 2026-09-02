from config import client, SYSTEM_PROMPT, MODEL

# ==========================
# CHAT HISTORY
# ==========================

conversation = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]


# ==========================
# ASK AI
# ==========================

def ask_ai(question):

    conversation.append(
        {
            "role": "user",
            "content": question
        }
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=conversation
    )

    answer = response.choices[0].message.content

    conversation.append(
        {
            "role": "assistant",
            "content": answer
        }
    )

    return answer