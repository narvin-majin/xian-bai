
MAX_CONTEXT = 10
MAX_HISTORY = 20

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
            for msg in chat_history[-MAX_CONTEXT:]
        ]
    )

    prompt = build_prompt(
        state,
        projects,
        recent_chat
    )
    

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

        reply = (
            "Gemini is currently unavailable.\n"
            f"Error: {e}"
        )

    chat_history.append(
        {
            "role": "assistant",
            "text": reply
        }
    )
    chat_history[:] = chat_history[-MAX_HISTORY:]
    return reply


def build_prompt(state, projects, recent_chat):

    return f"""
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