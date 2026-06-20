from assistant_core import process_message
from command_router import handle_command


def start_terminal(
    state,
    projects,
    chat_history,
    client,
    save_chat_history
):

    print("Xian Bai Terminal Mode")
    print("Type 'exit' to quit")

    while True:

        user_input = input("\nYou > ")

        if user_input.lower() == "exit":
            break

        if user_input.startswith("/"):

            reply = handle_command(
                user_input,
            )

        else:

            reply = process_message(
                user_input,
                state,
                projects,
                chat_history,
                client
            )

        save_chat_history(chat_history)

        print(f"\nXian Bai > {reply}")