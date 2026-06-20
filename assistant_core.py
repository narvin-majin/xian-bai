import json
from pathlib import Path

def process_message(
    user_text,
    state,
    projects,
    chat_history,
    client
):

    chat_history.append(
        {
            "role": "user",
            "text": user_text
        }
    )

    recent_chat = "\n".join(
        [
            f"{msg['role']}: {msg['text']}"
            for msg in chat_history[-10:]
        ]
    )

    prompt = f"""
You are Xian Bai.

You are a direct, practical and friendly
personal productivity assistant.

Current State:
{state}

Active Project:
{projects["active_project"]}

Recent Conversation:
{recent_chat}

Keep answers concise.
"""

    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        reply = (
            response.text
            if response.text
            else "No response generated."
        )

    except Exception as e:

        reply = f"Gemini Error: {e}"

    chat_history.append(
        {
            "role": "assistant",
            "text": reply
        }
    )
    del chat_history[:-20]
    return reply
