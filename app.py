import streamlit as st
from google import genai
from google.genai import types
from gtts import gTTS
import io
import PIL.Image
from datetime import datetime, timedelta
from tinydb import TinyDB
from streamlit_mic_recorder import mic_recorder

# --- 1. CONFIGURATION & TIME LIMITS ---
st.set_page_config(page_title="Skibidi AI", page_icon="⚡", layout="centered")
st.title("🤖 Skibidi AI Assistant")
st.subheader("Always here to help you!")

# CHANGE THIS VALUE: Set how many hours a user can chat for free
FREE_TRIAL_HOURS = 2 

API_KEY = st.secrets["GEMINI_API_KEY"]

@st.cache_resource
def get_ai_client():
    return genai.Client(api_key=API_KEY)

client = get_ai_client()

# --- 2. TIME TRACKING LOGIC ---
# Tracks when the user started interacting with the app
if "start_time" not in st.session_state:
    st.session_state.start_time = datetime.now()

# Calculate if the user has run out of time
current_time_check = datetime.now()
time_elapsed = current_time_check - st.session_state.start_time
time_left = timedelta(hours=FREE_TRIAL_HOURS) - time_elapsed

# --- 3. HARD LOCK CHECK ---
# If the time elapsed is greater than our limit, block the whole app!
if time_elapsed >= timedelta(hours=FREE_TRIAL_HOURS):
    st.error("⚠️ **Your Free Trial Has Expired!**")
    st.write(f"You have used your {FREE_TRIAL_HOURS}-hour free session allocation for Skibidi AI.")
    st.info("🌟 **Unlock Unlimited Access:** Upgrade to our **Premium Plan** right now to clear this block, unlock higher quality responses, and chat forever!")
    st.stop() # This completely STOPS the code from loading the chat boxes below!

# --- 4. SHOW TIME REMINDER ---
else:
    # Optional: Shows a small countdown tracker at the top so they know their limit
    minutes_left = int(time_left.total_seconds() / 60)
    st.caption(f"⏳ Free session active. Remaining time: {minutes_left} minutes.")

# --- 5. PERMANENT DATABASE STORAGE ---
db = TinyDB("chat_history.json")

if "messages" not in st.session_state:
    st.session_state.messages = db.all()

# Display historical messages step-by-step
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if "timestamp" in msg:
            st.caption(f"⏱️ {msg['timestamp']}")
        st.markdown(msg["content"])
        if "image_path" in msg and msg["image_path"]:
            st.image(msg["image_path"], caption="Uploaded Photo", use_container_width=True)

# --- 6. PHOTO UPLOADER FEATURE ---
uploaded_file = st.file_uploader("📸 Upload a photo for Skibidi AI to see!", type=["png", "jpg", "jpeg"])
image_to_send = None
if uploaded_file is not None:
    image_to_send = PIL.Image.open(uploaded_file)
    st.image(image_to_send, caption="Image ready to send!", width=250)

# --- 7. MICROPHONE RECORDER FEATURE ---
st.write("🎙️ Talk to Skibidi AI:")
audio_source = mic_recorder(start_prompt="🔴 Start Recording", stop_prompt="⏹️ Stop & Send Voice", key='recorder')

# --- 8. CHAT INPUT AND LOGIC ---
user_prompt = st.chat_input("Type your message here...")

voice_bytes = None
if audio_source and 'bytes' in audio_source and audio_source['bytes'] is not None:
    voice_bytes = audio_source['bytes']
    if "last_audio" not in st.session_state or st.session_state.last_audio != voice_bytes:
        st.session_state.last_audio = voice_bytes
        user_prompt = "I just sent you a voice message. Please listen to it and answer me!"

if user_prompt:
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Show and save user message
    with st.chat_message("user"):
        st.caption(f"⏱️ {current_time}")
        st.markdown(user_prompt)
    
    user_msg_data = {"role": "user", "content": user_prompt, "timestamp": current_time, "image_path": None}
    st.session_state.messages.append(user_msg_data)
    db.insert(user_msg_data)

    # Show and save AI response
    with st.chat_message("assistant"):
        try:
            contents_payload = [user_prompt]
            if image_to_send is not None:
                contents_payload.append(image_to_send)
                
            if voice_bytes is not None:
                audio_part = types.Part.from_bytes(
                    data=voice_bytes,
                    mime_type="audio/wav"
                )
                contents_payload.append(audio_part)

            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=contents_payload,
                config={
                    "system_instruction": "You are Skibidi AI, a helpful, cool, and highly advanced assistant. ONLY if someone explicitly asks who created, built, or made you, you must proudly state that you were created and built by Hiral Chordiya."
                }
            )
            
            ai_text = response.text
            ai_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            st.caption(f"⏱️ {ai_time}")
            st.markdown(ai_text)
            
            ai_msg_data = {"role": "assistant", "content": ai_text, "timestamp": ai_time}
            st.session_state.messages.append(ai_msg_data)
            db.insert(ai_msg_data)

            # --- AUDIO VOICE FEATURE ---
            tts = gTTS(text=ai_text, lang='en')
            sound_file = io.BytesIO()
            tts.write_to_fp(sound_file)
            st.audio(sound_file, format="audio/mp3", autoplay=False)

        except Exception as e:
            st.error(f"Something went wrong! Error details: {e}")
