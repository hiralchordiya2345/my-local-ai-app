import streamlit as st
from google import genai
from google.genai import types
from gtts import gTTS
import io
import PIL.Image
from tinydb import TinyDB
from streamlit_mic_recorder import mic_recorder
from supabase import create_client, Client

st.set_page_config(page_title="Skibidi AI", page_icon="🤖", layout="centered")

# --- 1. SUPABASE CLOUD BACKEND SETUP ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error("⚠️ Secrets Setup Missing! Add SUPABASE_URL and SUPABASE_KEY to your Streamlit Advanced Secrets.")
    st.stop()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

st.markdown("""
    <style>
    div[data-testid="stColumn"] { display: flex; align-items: flex-end; justify-content: center; }
    .stFileUploader section { padding: 0.5rem; }
    </style>
""", unsafe_allow_html=True)

# --- 2. AUTHENTICATION PROTECTION WALL ---
if not st.session_state.authenticated:
    st.title("🔐 Welcome to Skibidi AI")
    st.subheader("Sign in with your credentials to begin")
    
    auth_mode = st.radio("Choose Option", ["Sign In / Login", "Create New Account"], horizontal=True)
    
    email = st.text_input("📧 Email Address", key="auth_email")
    password = st.text_input("🔑 Password", type="password", key="auth_pass")
    
    if auth_mode == "Create New Account":
        if st.button("🚀 Register My Account", use_container_width=True):
            if email and password:
                try:
                    supabase.auth.sign_up({"email": email, "password": password})
                    st.success("✅ Account registration completed! You can now log in.")
                except Exception as e:
                    st.error(f"Registration Error: {e}")
            else:
                st.warning("Please fill in both fields.")
                
    elif auth_mode == "Sign In / Login":
        if st.button("🔓 Sign In", use_container_width=True):
            if email and password:
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.authenticated = True
                    st.session_state.user_email = email
                    st.success("Access Granted!")
                    st.rerun()
                except Exception as e:
                    st.error("❌ Incorrect email or password.")
            else:
                st.warning("Please fill out your credentials.")

if not st.session_state.authenticated:
    st.stop()

# --- 3. CORE APPLICATION PLATFORM ---
st.title("🤖 Skibidi Ultra AI Assistant")
st.caption(f"🔒 Security Active | Logged in as: **{st.session_state.user_email}**")

# --- FIXED RATE-LIMITING STRATEGY ---
with st.sidebar:
    st.title("⚙️ Control Panel")
    user_custom_key = st.text_input("🔑 Use Custom Gemini Key (Optional)", type="password", help="If the app says quota exhausted, paste your own key here.")
    st.write("---")
    if st.button("🗑️ Reset Chat View", use_container_width=True):
        safe_user_id = "".join(char for char in st.session_state.user_email if char.isalnum())
        TinyDB(f"history_{safe_user_id}.json").truncate()
        st.session_state.messages = []
        if "last_processed_audio" in st.session_state:
            del st.session_state["last_processed_audio"]
        st.rerun()
    if st.button("🚪 Secure Log Out", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.messages = []
        st.rerun()

# Prioritize custom user key over system developer key if quota runs out
FINAL_API_KEY = user_custom_key if user_custom_key else st.secrets["GEMINI_API_KEY"]

def get_ai_client(api_key):
    return genai.Client(api_key=api_key)

try:
    client = get_ai_client(FINAL_API_KEY)
except Exception as e:
    st.error("Could not load AI client. Validate API Keys.")

safe_user_id = "".join(char for char in st.session_state.user_email if char.isalnum())
db = TinyDB(f"history_{safe_user_id}.json")

if "messages" not in st.session_state:
    st.session_state.messages = db.all()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 4. MULTI-MODAL PIPELINE INPUTS ---
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
        # Image creation mode (Stable public engine)
        if any(kw in user_prompt.lower() for kw in ["draw", "generate image", "create art"]):
            try:
                st.write("🎨 *Creating your masterpiece...*")
                formatted_prompt = user_prompt.lower().replace(" ", "%20")
                if "ghibli" in formatted_prompt and "studio%20ghibli" not in formatted_prompt:
                    formatted_prompt += ",%20beautiful%20studio%20ghibli%20art%20style"
                
                art_url = f"https://image.pollinations.ai/prompt/{formatted_prompt}?width=1024&height=768&nologo=true"
                st.markdown(f"### Here is your masterpiece for: *{user_prompt}*")
                st.image(art_url, use_container_width=True)
                
                ai_msg_data = {"role": "assistant", "content": f"🎨 Generated Art for: '{user_prompt}'"}
                st.session_state.messages.append(ai_msg_data)
                db.insert(ai_msg_data)
            except Exception as e:
                st.error(f"Art Engine Pipeline Interrupted: {e}")
        
        # Text conversation processing engine
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

                tts = gTTS(text=ai_text, lang='en')
                sound_file = io.BytesIO()
                tts.write_to_fp(sound_file)
                st.audio(sound_file, format="audio/mp3")

            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    st.error("🚨 The main app free quota is completely full right now! Please wait a couple minutes or paste your own free Gemini API Key into the sidebar to bypass the block.")
                else:
                    st.error(f"Chat error: {e}")
