import streamlit as st
import requests

st.set_page_config(
    page_title="Quran Cards", 
    page_icon="📖", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 1. SETUP & STATE ---
if 'chapter' not in st.session_state: st.session_state.chapter = 1
if 'start_v' not in st.session_state: st.session_state.start_v = 1
if 'end_v' not in st.session_state: st.session_state.end_v = 7 
if 'card_index' not in st.session_state: st.session_state.card_index = 0

# --- 2. DATA FUNCTIONS ---
@st.cache_data(show_spinner=False)
def get_chapter_info(chapter_id):
    try:
        resp = requests.get(f"https://api.quran.com/api/v4/chapters/{chapter_id}").json()
        return resp['chapter']['name_simple'], resp['chapter']['name_arabic'], resp['chapter']['verses_count']
    except: return "Unknown", "", 0

@st.cache_data(show_spinner=False)
def fetch_verses_data(chapter_num):
    url = f"https://api.quran.com/api/v4/verses/by_chapter/{chapter_num}?language=en&words=false&fields=text_uthmani,juz_number&per_page=1000"
    try: return requests.get(url).json()['verses']
    except: return []

def calculate_font_size(text):
    l = len(text)
    if l < 40: return "8vw"
    elif l < 80: return "7vw"
    elif l < 150: return "5.5vw"
    elif l < 300: return "4.5vw"
    else: return "3.5vw"

# --- 3. CSS "FULLSCREEN / FILL" ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Scheherazade+New:wght@400;700&display=swap');
    
    /* 1. NOLLSTÄLLNING AV STREAMLIT LAYOUT */
    .stApp { background-color: #ffffff; }
    
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        max-width: 100% !important;
        margin: 0 !important;
    }
    
    header, footer, [data-testid="stSidebar"] { display: none !important; }

    /* 2. HEADER (Uppdaterad höjd) */
    .top-bar {
        flex: 0 0 5px; /* <-- Minskad höjd här (var 60px) */
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 20px;
        background-color: #f8f9fa;
        border-bottom: 1px solid #eee;
        z-index: 10;
    }

    /* 3. KNAPP-STYLING */
    div[data-testid="column"]:nth-of-type(1) .stButton > button, 
    div[data-testid="column"]:nth-of-type(3) .stButton > button {
        background-color: transparent !important;
        border: none !important;
        font-size: 3rem !important;
        color: #e0e0e0 !important;
        height: 80vh !important; 
        width: 100% !important;
        box-shadow: none !important;
        outline: none !important;
    }

    div[data-testid="column"]:nth-of-type(1) .stButton > button:focus, 
    div[data-testid="column"]:nth-of-type(3) .stButton > button:focus,
    div[data-testid="column"]:nth-of-type(1) .stButton > button:active, 
    div[data-testid="column"]:nth-of-type(3) .stButton > button:active {
        background-color: transparent !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: #e0e0e0 !important;
    }

    div[data-testid="column"]:nth-of-type(1) .stButton > button:hover, 
    div[data-testid="column"]:nth-of-type(3) .stButton > button:hover,
    div[data-testid="column"]:nth-of-type(1) .stButton > button:focus:hover, 
    div[data-testid="column"]:nth-of-type(3) .stButton > button:focus:hover {
        color: #2E8B57 !important;
        background-color: transparent !important;
    }

    /* 4. TEXT STYLING */
    .arabic-text {
        font-family: 'Scheherazade New', serif;
        line-height: 1.8;
        direction: rtl;
        text-align: center;
        color: #000;
        width: 100%;
        padding: 0 20px;
    }

    .meta-tag {
        font-family: sans-serif; font-size: 0.8rem; color: #888; font-weight: 600;
        background: #f1f1f1; padding: 4px 10px; border-radius: 12px;
    }

</style>
""", unsafe_allow_html=True)

# --- 4. POPUP MENY ---
@st.dialog("Inställningar")
def open_settings():
    st.write("Navigering")
    new_chapter = st.number_input("Kapitel (1-114)", 1, 114, st.session_state.chapter)
    _, _, total_verses = get_chapter_info(new_chapter)
    
    c1, c2 = st.columns(2)
    with c1:
        default_start = 1 if new_chapter != st.session_state.chapter else st.session_state.start_v
        new_start = st.number_input("Start", 1, total_verses, default_start)
    with c2:
        default_end = total_verses if new_chapter != st.session_state.chapter else st.session_state.end_v
        new_end = st.number_input("Slut", new_start, total_verses, default_end)

    if st.button("Ladda", type="primary", use_container_width=True):
        st.session_state.chapter = new_chapter
        st.session_state.start_v = new_start
        st.session_state.end_v = new_end
        st.session_state.card_index = 0
        st.rerun()

# --- 5. LOGIC & RENDER ---
verses_data = fetch_verses_data(st.session_state.chapter)
surah_en, surah_ar, _ = get_chapter_info(st.session_state.chapter)

start_idx = st.session_state.start_v - 1
end_idx = st.session_state.end_v
selected_data = verses_data[start_idx : end_idx]

if st.session_state.card_index >= len(selected_data): st.session_state.card_index = 0

if selected_data:
    obj = selected_data[st.session_state.card_index]
    raw_text = obj['text_uthmani']
    juz = obj['juz_number']
    verse_num = obj['verse_key'].split(':')[1]
    
    # Progress
    progress_pct = ((st.session_state.card_index + 1) / len(selected_data)) * 100
    font_size = calculate_font_size(raw_text)

    # 1. HEADER CONTAINER
    header_container = st.container()
    with header_container:
        # vertical_alignment="center" sköter centreringen nu när padding är borta
        hc1, hc2, hc3 = st.columns([1, 4, 1], vertical_alignment="center")
        
        with hc1:
            # Tog bort padding-top:15px här för att passa den lägre listen
            st.markdown(f'<div style="text-align:center;"><span class="meta-tag">Juz {juz}</span></div>', unsafe_allow_html=True)
        with hc2:
            if st.button(f"{surah_en} | {surah_ar}", key="title_btn", use_container_width=True):
                open_settings()
        with hc3:
            # Tog bort padding-top:15px här också
            st.markdown(f'<div style="text-align:center;"><span class="meta-tag">#{verse_num}</span></div>', unsafe_allow_html=True)
        
        # Progress bar - tog bort margin-top för att den ska ligga tajt
        st.markdown(f"""
        <div style="width:100%; height:4px; background:#f0f0f0; margin-top: 0px;">
            <div style="width:{progress_pct}%; height:100%; background:#2E8B57; transition:width 0.3s;"></div>
        </div>
        """, unsafe_allow_html=True)

    # 2. HUVUDINNEHÅLL
    c_left, c_center, c_right = st.columns([1, 8, 1])
    
    with c_left:
        st.write("")
        st.write("")
        if st.button("❮", key="prev"):
            if st.session_state.card_index > 0:
                st.session_state.card_index -= 1
                st.rerun()

    with c_center:
        st.markdown(f"""
        <div style="
            height: 80vh; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            overflow-y: auto;">
            <div class="arabic-text" style="font-size: {font_size};">
                {raw_text}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c_right:
        st.write("")
        st.write("")
        if st.button("❯", key="next"):
            if st.session_state.card_index < len(selected_data) - 1:
                st.session_state.card_index += 1
                st.rerun()

else:
    st.warning("Ingen data. Öppna inställningar.")
