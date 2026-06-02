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

# --- 1. INITIALIZE SUPABASE CLOUD BACKEND ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Skibidi AI", page_icon="🤖", layout="centered")

# Custom UI CSS Styling for a tight horizontal media grid
st.markdown("""
    <style>
    div[data-testid="stColumn"] { display: flex; align-items: flex-end; justify-content: center; }
    .stFileUploader section { padding: 0.5rem; }
    </style>
""", unsafe_allow_html=True)

# Keep track of login state securely in session memory
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

# --- 2. PREMIUM LOGIN WALL (EMAIL & SECURE PASSWORD) ---
if not st.session_state.authenticated:
    st.title("🔐 Welcome to Skibidi AI")
    st.subheader("Sign in with your email and password to begin")
    
    auth_mode = st.radio("Choose Option", ["Sign In / Login", "Create New Account"], horizontal=True)
    
    email = st.text_input("📧 Email Address")
    password = st.text_input("🔑 Password", type="password", help="Your password is fully encrypted and secure.")
    
    if auth_mode == "Create New Account":
        if st.button("🚀 Register My Account", use_container_width=True):
            if email and password:
                try:
                    # Registers user into your Supabase database project vault securely
                    supabase.auth.sign_up({"email": email, "password": password})
                    st.success("✅ Account registration requested! Please verify if needed or log in.")
                except Exception as e:
                    st.error(f"Registration Error: {e}")
            else:
                st.warning("Please fill in both email and password fields.")
                
    elif auth_mode == "Sign In / Login":
        if st.button("🔓 Sign In", use_container_width=True):
            if email and password:
                try:
                    # Authenticates securely against cloud records
                    supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.authenticated = True
                    st.session_state.user_email = email
                    st.session_state.start_time = datetime.now()  # 2-hour window starts upon authentication
                    st.success("Access Granted! Syncing profile...")
                    st.rerun()
                except Exception as e:
                    st.error("❌ Incorrect email or password. Please try again.")
            else:
                st.warning("Please fill out your credentials.")
                
    st.stop()  # STOPS THE ENTIRE PAGE LAYER HERE UNTIL USER IS SUCESSFULLY AUTHENTICATED!

# --- 3. CORE PLATFORM SUBSCRIPTION ENGINE ---
st.title("🤖 Skibidi Ultra AI Assistant")
st.caption(f"🛡️ Security Active | Logged in as: **{st.session_state.user_email}**")

FREE_TRIAL_HOURS = 2 
API_KEY = st.secrets["GEMINI_API_KEY"]

@st.cache_resource
def get_ai_client():
    return genai.Client(api_key=API_KEY)

client = get_ai_client()

time_elapsed = datetime.now() - st.session_state.start_time
time_left = timedelta(hours=FREE_TRIAL_HOURS) - time_elapsed

if time_elapsed >= timedelta(hours=FREE_TRIAL_HOURS):
    st.error("⚠️ **Your Free 2-Hour Trial Session Has Expired!**")
    st.info("🌟 **Unlock Infinite Scale:** Upgrade your subscription plan to bypass session restrictions and unlock higher content limits.")
    if st.button("🚪 Log Out"):
        st.session_state.authenticated = False
        st.rerun()
    st.stop()

# --- 4. HIGH-PERFORMANCE DYNAMIC DATA ENGINE ---
# Automatically builds a unique database index strictly for this specific user's email ID
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

# Render individual private streams out of high-speed system memory
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if "timestamp" in msg: st.caption(f"⏱️ {msg['timestamp']}")
        st.markdown(msg["content"])

# --- 5. COMPACT HORIZONTAL MEDIA HARVESTER ---
col_file, col_mic = st.columns([3, 2])
with col_file:
    uploaded_file = st.file_uploader("➕ Image Upload", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
with col_mic:
    audio_source = mic_recorder(start_prompt="🎙️ Record Voice", stop_prompt="⏹️ Submit Audio", key='recorder')

image_to_send = None
if uploaded_file is not None:
    image_to_send = PIL.Image.open(uploaded_file)
    st.image(image_to_send, caption="📸 Media asset successfully staged.", width=140)

# --- 6. UNIFIED CHAT EXECUTION HUB ---
user_prompt = st.chat_input("Type here or command: 'Draw a magical Ghibli valley'...")
voice_bytes = None

if audio_source and 'bytes' in audio_source and audio_source['bytes'] is not None:
    current_audio = audio_source['bytes']
    if "last_processed_audio" not in st.session_state or st.session_state.last_processed_audio != current_audio:
        voice_bytes = current_audio
        st.session_state.last_processed_audio = current_audio
        user_prompt = "🎙️ [Sent an audio message]"

if user_prompt:
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with st.chat_message("user"):
        st.caption(f"⏱️ {current_time}")
        st.markdown(user_prompt)
    
    user_msg_data = {"role": "user", "content": user_prompt, "timestamp": current_time}
    st.session_state.messages.append(user_msg_data)
    db.insert(user_msg_data)

    with st.chat_message("assistant"):
        # ROUTE A: HIGH-PERFORMANCE ART & GHIBLI RENDER ENGINE
        if any(keyword in user_prompt.lower() for keyword in ["draw", "generate image", "create art", "paint"]):
            try:
                st.write("🎨 *Skibidi Engine is generating digital canvas...*")
                final_prompt = user_prompt
                if "ghibli" in user_prompt.lower() and "studio ghibli" not in user_prompt.lower():
                    final_prompt += ", majestic hand-drawn aesthetic, Studio Ghibli anime style, cinematic lighting illustration"

                result = client.models.generate_images(
                    model='imagen-3.0-generate-002',
                    prompt=final_prompt,
                    config=types.GenerateImagesConfig(number_of_images=1, output_mime_type="image/jpeg", aspect_ratio="1:1")
                )
                
                for generated_image in result.generated_images:
                    image_bytes = generated_image.image.image_bytes
                    st.image(image_bytes, caption=f"Canvas Output: '{user_prompt}'", use_container_width=True)
                    
                    ai_msg_data = {"role": "assistant", "content": f"🎨 Generated Art: '{user_prompt}'", "timestamp": current_time}
                    st.session_state.messages.append(ai_msg_data)
                    db.insert(ai_msg_data)
            except Exception as e:
                st.error(f"Art Engine Pipeline Interrupted: {e}")
                
        # ROUTE B: HUMAN EMBODIED COMPASSIONATE CHAT PIPELINE (WITH SYNTAX FIXES)
        else:
            try:
                contents_payload = []
                if voice_bytes is not None:
                    audio_part = types.Part.from_bytes(data=voice_bytes, mime_type="audio/wav")
                    contents_payload.append(audio_part)
                else:
                    contents_payload.append(user_prompt)

                if image_to_send is not None:
                    contents_payload.append(image_to_send)

                system_rules = (
                    "You are Skibidi AI, a warm, lifelike, and deeply empathetic humanoid companion. "
                    "You provide comprehensive academic guidance, homework code breakdowns, and deep emotional life support. "
                    "Always prefix responses with an expressive emotional emoji displaying your human face mood (e.g. 🌟, 🤗, 🧠). "
                    "If explicitly asked who created you, proudly state you were engineered by Hiral Chordiya."
                )

                # Active Content Filtering Shield to keep it safe for kids & family usage
                safety_rules = [
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_LOW_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_LOW_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_LOW_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_LOW_AND_ABOVE"},
                ]

                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=contents_payload,
                    config={
                        "system_instruction": system_rules,
                        "safety_settings": safety_rules
                    }
                )
                
                ai_text = response.text
                ai_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                st.caption(f"⏱️ {ai_time}")
                st.markdown(ai_text)
                
                ai_msg_data = {"role": "assistant", "content": ai_text, "timestamp": ai_time}
                st.session_state.messages.append(ai_msg_data)
                db.insert(ai_msg_data)

                # Human Voice Wave Synthesizer (Safely inside the block to fix SyntaxError)
                tts = gTTS(text=ai_text, lang='en')
                sound_file = io.BytesIO()
                tts.write_to_fp(sound_file)
                st.audio(sound_file, format="audio/mp3", autoplay=False)

            except Exception as e:
                st.error(f"Core Pipeline Error: {e}")
