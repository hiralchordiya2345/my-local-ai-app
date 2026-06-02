import streamlit as st
from google import genai
from gtts import gTTS
import io
import PIL.Image
from datetime import datetime
from tinydb import TinyDB
from streamlit_mic_recorder import mic_recorder  # NEW: Microphone recorder tool

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Skibidi AI", page_icon="⚡", layout="centered")
st.title("⚡ Skibidi AI Assistant always here to help you")

API_KEY = st.secrets["GEMINI_API_KEY"]

@st.cache_resource
def get_ai_client():
    return genai.Client(api_key=API_KEY)

client = get_ai_client()

# --- 2. PERMANENT DATABASE STORAGE ---
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

# --- 3. PHOTO UPLOADER FEATURE ---
uploaded_file = st.file_uploader("📸 Upload a photo for the AI to see!", type=["png", "jpg", "jpeg"])
image_to_send = None
if uploaded_file is not None:
    image_to_send = PIL.Image.open(uploaded_file)
    st.image(image_to_send, caption="Image ready to send!", width=250)

# --- 4. MICROPHONE RECORDER FEATURE ---
st.write("🎙️ Talk to your AI:")
# This creates a Record button that listens to the user's mic
audio_source = mic_recorder(start_prompt="🔴 Start Recording", stop_prompt="⏹️ Stop & Send Voice", key='recorder')

# --- 5. CHAT INPUT AND LOGIC ---
user_prompt = st.chat_input("Type your message here...")

# If the user used the microphone instead of typing, process the audio data!
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
            # Build payload out of text, images, or recorded voice data
            contents_payload = [user_prompt]
            if image_to_send is not None:
                contents_payload.append(image_to_send)
            if voice_bytes is not None:
                # This hands the actual raw microphone recording data over to Gemini's ears!
                contents_payload.append({"data": voice_bytes, "mime_type": "audio/wav"})

            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=contents_payload,
                config={
                    "system_instruction": "You are a helpful AI assistant. You must proudly mention in your first response, or if asked, that you were created and built by [YOUR NAME HERE]."
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
            st.audio(sound_file, format="audio/mp3", autoplay=True)

        except Exception as e:
            st.error(f"Something went wrong! Error details: {e}")
