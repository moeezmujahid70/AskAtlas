import os
import sys

from taipy.gui import Gui, State, notify
import google.generativeai as genai
from dotenv import load_dotenv

client = None
context = "The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly.\n\nHuman: Hello, who are you?\nAI: I am an AI created by Google. How can I help you today? "
conversation = {
    "Conversation": ["Who are you?", "Hi! I am Gemini 1.5 Pro. How can I help you today?"]
}
current_user_message = ""
past_conversations = []
selected_conv = None
selected_row = [1]


def on_init(state: State) -> None:
    """
    Initialize the app.
    """
    state.context = "The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly.\n\nHuman: Hello, who are you?\nAI: I am an AI created by Google. How can I help you today? "
    state.conversation = {
        "Conversation": ["Who are you?", "Hi! I am Gemini 1.5 Pro. How can I help you today?"]
    }
    state.current_user_message = ""
    state.past_conversations = []
    state.selected_conv = None
    state.selected_row = [1]


def request(state: State, prompt: str) -> str:
    """
    Send a prompt to Gemini API and return the response.
    """
    model = genai.GenerativeModel('gemini-2.0-flash')
    chat = model.start_chat(history=[])
    response = chat.send_message(prompt)
    return response.text.strip()


def update_context(state: State) -> None:
    """
    Update the context with the user's message and the AI's response.
    """
    state.context += f"Human: \n {state.current_user_message}\n\n AI:"
    answer = request(state, state.context).replace("\n", "")
    state.context += answer
    state.selected_row = [len(state.conversation["Conversation"]) + 1]
    return answer


def send_message(state: State) -> None:
    """
    Send the user's message to the API and update the context.
    """
    notify(state, "info", "Sending message...")
    answer = update_context(state)
    conv = state.conversation._dict.copy()
    conv["Conversation"] += [state.current_user_message, answer]
    state.current_user_message = ""
    state.conversation = conv
    notify(state, "success", "Response received!")


def style_conv(state: State, idx: int, row: int) -> str:
    """
    Apply a style to the conversation table depending on the message's author.
    """
    if idx is None:
        return None
    elif idx % 2 == 0:
        return "user_message"
    else:
        return "gpt_message"


def on_exception(state, function_name: str, ex: Exception) -> None:
    """
    Catch exceptions and notify user in Taipy GUI
    """
    notify(state, "error", f"An error occurred in {function_name}: {ex}")


def reset_chat(state: State) -> None:
    """
    Reset the chat by clearing the conversation.
    """
    state.past_conversations = state.past_conversations + [
        [len(state.past_conversations), state.conversation]
    ]
    state.conversation = {
        "Conversation": ["Who are you?", "Hi! I am Gemini 1.5 Pro. How can I help you today?"]
    }


def tree_adapter(item: list) -> list[str]:
    """
    Converts element of past_conversations to id and displayed string
    """
    identifier = item[0]
    if len(item[1]["Conversation"]) > 3:
        return (identifier, item[1]["Conversation"][2][:50] + "...")
    return (item[0], "Empty conversation")


def select_conv(state: State, var_name: str, value) -> None:
    """
    Select conversation from past_conversations
    """
    state.conversation = state.past_conversations[value[0][0]][1]
    state.context = "The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly.\n\nHuman: Hello, who are you?\nAI: I am an AI created by Google. How can I help you today? "
    for i in range(2, len(state.conversation["Conversation"]), 2):
        state.context += f"Human: \n {state.conversation['Conversation'][i]}\n\n AI:"
        state.context += state.conversation["Conversation"][i + 1]
    state.selected_row = [len(state.conversation["Conversation"]) + 1]


past_prompts = []

page = """
<|layout|columns=300px 1|
<|part|class_name=sidebar|
# Taipy **Chat**{: .color-primary} # {: .logo-text}
<|New Conversation|button|class_name=fullwidth plain|id=reset_app_button|on_action=reset_chat|>
### Previous activities ### {: .h5 .mt2 .mb-half}
<|{selected_conv}|tree|lov={past_conversations}|class_name=past_prompts_list|multiple|adapter=tree_adapter|on_change=select_conv|>
|>

<|part|class_name=p2 align-item-bottom table|
<|{conversation}|table|style=style_conv|show_all|selected={selected_row}|rebuild|>
<|part|class_name=card mt1|
<|{current_user_message}|input|label=Write your message here...|on_action=send_message|class_name=fullwidth|change_delay=-1|>
|>
|>
|>
"""

if __name__ == "__main__":
    load_dotenv()

    # Note: NOT OpenAI key now
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    Gui(page).run(debug=True, dark_mode=True, use_reloader=True,
                  title="💬 Taipy Chat with Gemini 1.5 Pro")
