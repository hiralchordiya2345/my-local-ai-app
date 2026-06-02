import streamlit as st
import ollama

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="My Local AI App", page_icon="📱", layout="centered")
st.title("🤖 My Custom Local AI App")

# --- 2. CHAT HISTORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 3. CHAT LOGIC ---
if user_prompt := st.chat_input("Type a message..."):
    # Show user message
    with st.chat_message("user"):
        st.markdown(user_prompt)
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    # Get response from the local Ollama model
    with st.chat_message("assistant"):
        try:
            response = ollama.chat(
                model='llama3.2:1b', 
                messages=st.session_state.messages
            )
            ai_text = response['message']['content']
            st.markdown(ai_text)
            st.session_state.messages.append({"role": "assistant", "content": ai_text})
        except Exception as e:
            st.error("Make sure the Ollama app is open and running on your computer!")import streamlit as st
import ollama

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="My Local AI App", page_icon="📱", layout="centered")
st.title("🤖 My Custom Local AI App")

# --- 2. CHAT HISTORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 3. CHAT LOGIC ---
if user_prompt := st.chat_input("Type a message..."):
    # Show user message
    with st.chat_message("user"):
        st.markdown(user_prompt)
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    # Get response from the local Ollama model
    with st.chat_message("assistant"):
        try:
            response = ollama.chat(
                model='llama3.2:1b', 
                messages=st.session_state.messages
            )
            ai_text = response['message']['content']
            st.markdown(ai_text)
            st.session_state.messages.append({"role": "assistant", "content": ai_text})
        except Exception as e:
            st.error("Make sure the Ollama app is open and running on your computer!")