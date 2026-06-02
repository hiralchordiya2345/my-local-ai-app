import streamlit as st
from google import genai

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="My AI App", page_icon="📱", layout="centered")
st.title("🤖 My Custom AI App")

# PASTE YOUR GEMINI API KEY INSIDE THE QUOTES BELOW:
API_KEY = "st.secrets["GEMINI_API_KEY"]

# Initialize the Gemini Client
@st.cache_resource
def get_ai_client():
    return genai.Client(api_key=API_KEY)

client = get_ai_client()

# --- 2. CHAT HISTORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display all previous messages on screen
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 3. CHAT INPUT AND LOGIC ---
if user_prompt := st.chat_input("Type your message here..."):
    # 1. Show user message
    with st.chat_message("user"):
        st.markdown(user_prompt)
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    # 2. Get and show AI response
    with st.chat_message("assistant"):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_prompt,
            )
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error("Error: Something went wrong. Check your API key!")
