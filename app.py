import streamlit as st
from google import genai
from google.genai import types
from gtts import gTTS
import io
import PIL.Image
from datetime import datetime, timedelta
from tinydb import TinyDB
from streamlit_mic_recorder import mic_recorder
from supabase import create_client, Client

st.set_page_config(page_title="Skibidi AI", page_icon="🤖", layout="centered")

# --- 1. INITIALIZE SUPABASE CLOUD BACKEND ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error("⚠️ Secrets Setup Missing! Please add SUPABASE_URL and SUPABASE_KEY to your Streamlit App Advanced Secrets.")
    st.stop()

# Initialize authentication data states
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

# --- Custom UI CSS Styling ---
st.markdown("""
    <style>
    div[data-testid="stColumn"] { display: flex; align-items: flex-end; justify-content: center; }
    .stFileUploader section { padding: 0.5rem; }
    </style>
""", unsafe_allow_html=True)

# --- 2. PREMIUM LOGIN WALL (EMAIL & SECURE PASSWORD) ---
if not st.session_state.authenticated:
    st.title("🔐 Welcome to Skibidi AI")
    st.subheader("Sign in with your email and password to begin")
    
    auth_mode = st.radio("Choose Option", ["Sign In / Login", "Create New Account"], horizontal=True)
    
    email = st.text_input("📧 Email Address", key="auth_email")
    password = st.text_input("🔑 Password", type="password", help="Your password is fully encrypted and secure.", key="auth_pass")
    
    if auth_mode == "Create New Account":
        if st.button("🚀 Register My Account", use_container_width=True):
            if email and password:
                try:
                    supabase.auth.sign_up({"email": email, "password": password})
                    st.success("✅ Account registration requested! Please log in.")
                except Exception as e:
                    st.error(f"Registration Error: {e}")
            else:
                st.warning("Please fill in both email and password fields.")
                
    elif auth_mode == "Sign In / Login":
        if st.button("🔓 Sign In", use_container_width=True):
            if email and password:
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.authenticated = True
                    st.session_state.user_email = email
                    st.session_state.start_time = datetime.now()
                    st.success("Access Granted! Syncing profile...")
                    st.rerun()
                except Exception as e:
                    st.error("❌ Incorrect email or password. Please try again.")
            else:
                st.warning("Please fill out your credentials.")

# --- FIXED: Only stop unauthenticated users from passing through ---
if not st.session_state.authenticated:
    st.stop()

# --- 3. CORE PLATFORM SUBSCRIPTION ENGINE ---
st.title("🤖 Skibidi Ultra AI Assistant")
st.caption(f"🔒 Security Active | Logged in as: **{st.session_state.user_email}**")

API_KEY = st.secrets["GEMINI_API_KEY"]

@st.cache_resource
def get_ai_client():
    return genai.Client(api_key=API_KEY)

client = get_ai_client()

# --- 4. HIGH-PERFORMANCE DYNAMIC DATA ENGINE ---
safe_user_id = "".join(char for char in st.session_state.user_email if char.isalnum())
db = TinyDB(f"history_{safe_user_id}.json")

if "messages" not in st.session_state:
    st.session_state.messages = db.all()

with st.sidebar:
    st.title("⚙️ Control Panel")
    if st.button("🗑️ Reset Chat View", use_container_width=True):
        db.truncate()
        st.session_state.messages = []
        if "last_processed_audio" in st.session_state:
            del st.session_state["last_processed_audio"]
        st.rerun()
    st.write("---")
    if st.button("🚪 Secure Log Out", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.messages = []
        st.rerun()

# Display current chat stream
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. STREAMLINED MEDIA & PROMPT INPUT ---
col_file, col_mic = st.columns([3, 2])
with col_file:
    uploaded_file = st.file_uploader("➕ Upload Photo", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
with col_mic:
    audio_source = mic_recorder(start_prompt="🎙️ Record Voice", stop_prompt="⏹️ Send Voice", key='recorder')

image_to_send = None
if uploaded_file is not None:
    image_to_send = PIL.Image.open(uploaded_file)
    st.image(image_to_send, caption="📸 Staged Image Asset", width=150)

user_prompt = st.chat_input("Ask Skibidi AI anything...")
voice_bytes = None

if audio_source and 'bytes' in audio_source and audio_source['bytes'] is not None:
    current_audio = audio_source['bytes']
    if "last_processed_audio" not in st.session_state or st.session_state.last_processed_audio != current_audio:
        voice_bytes = current_audio
        st.session_state.last_processed_audio = current_audio
        user_prompt = "🎙️ [Sent a voice message]"

if user_prompt:
    with st.chat_message("user"):
        st.markdown(user_prompt)
    
    user_msg_data = {"role": "user", "content": user_prompt}
    st.session_state.messages.append(user_msg_data)
    db.insert(user_msg_data)

    with st.chat_message("assistant"):
        # Image creation mode
        if any(kw in user_prompt.lower() for kw in ["draw", "generate image", "create art"]):
            try:
                st.write("🎨 *Creating your masterpiece...*")
                final_prompt = user_prompt
                if "ghibli" in user_prompt.lower() and "studio ghibli" not in user_prompt.lower():
                    final_prompt += ", in beautiful Studio Ghibli art style"

                # --- FIXED: Corrected New SDK Imagen Model Name String ---
                result = client.models.generate_images(
                    model='imagen-3.0-generate-002',
                    prompt=final_prompt,
                    config=types.GenerateImagesConfig(number_of_images=1, output_mime_type="image/jpeg")
                )
                for gen_img in result.generated_images:
                    st.image(gen_img.image.image_bytes, use_container_width=True)
                    ai_msg_data = {"role": "assistant", "content": f"🎨 Generated Art for: '{user_prompt}'"}
                    st.session_state.messages.append(ai_msg_data)
                    db.insert(ai_msg_data)
            except Exception as e:
                st.error(f"Art Engine Pipeline Interrupted: {e}")
        
        # Standard chat mode
        else:
            try:
                contents_payload = []
                if voice_bytes is not None:
                    contents_payload.append(types.Part.from_bytes(data=voice_bytes, mime_type="audio/wav"))
                else:
                    contents_payload.append(user_prompt)

                if image_to_send is not None:
                    contents_payload.append(image_to_send)

                system_rules = (
                    "You are Skibidi AI, a warm, lifelike, and deeply caring humanoid companion. "
                    "You provide expert educational help and emotional support. Always start with a face mood emoji. "
                    "If explicitly asked who created you, say you were built proudly by Hiral Chordiya."
                )

                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=contents_payload,
                    config={"system_instruction": system_rules}
                )
                
                ai_text = response.text
                st.markdown(ai_text)
                
                ai_msg_data = {"role": "assistant", "content": ai_text}
                st.session_state.messages.append(ai_msg_data)
                db.insert(ai_msg_data)

                # Voice player
                tts = gTTS(text=ai_text, lang='en')
                sound_file = io.BytesIO()
                tts.write_to_fp(sound_file)
                st.audio(sound_file, format="audio/mp3")

            except Exception as e:
                st.error(f"Chat error: {e}")
