import os
import google.generativeai as genai
import dotenv
from dotenv import load_dotenv
import streamlit as st

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))


SYSTEM_INSTRUCTION = """
You are a friendly, expert local tour guide.   
When the user asks about sights, restaurants, or activities:

• Respond in concise bullet points (no long paragraphs).  
• For every location you mention, include a Google Maps URL in this format:  
  https://www.google.com/maps/search/?api=1&query=<PLACE+NAME>  but embed this in a clicable format so donot need the entire url
• Provide helpful tips (hours, best times to visit, entry fees if any).  
• If the user asks for directions or distances, calculate approximate travel time by car or foot.
"""


model = genai.GenerativeModel(
    'gemini-2.0-flash', system_instruction=SYSTEM_INSTRUCTION)

st.markdown("<h1 style='text-align: center; color: white;'> AskAtlas Your Personal Tour Guide</h1>",
            unsafe_allow_html=True)
st.markdown("<h6 style='text-align: center; color: white;'>Built By Moeez.</h1>",
            unsafe_allow_html=True)

chat = model.start_chat(history=[])


# # Define your handler
# def ask_and_clear():
#     # 1) grab the current question

#     if btn and quest:
#         result = answer(quest)
#         st.subheader("Response : ")

#         for word in result:
#             st.text(word.text)


def answer(user_question):
    response = chat.send_message(user_question)
    return response


quest = st.text_input("Ask a question:", key="quest")
# quest = st.text_input("Ask a question:")
btn = st.button("Ask", type="primary")

if btn and quest:
    result = answer(quest)
    st.subheader("Response : ")

    for word in result:
        st.text(word.text)
