import streamlit as st
import requests
import unicodedata

# --- 1. SETUP & STATE ---
st.set_page_config(
    page_title="Quran Cards", 
    page_icon="📖", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

if 'chapter' not in st.session_state: st.session_state.chapter = 1
if 'start_v' not in st.session_state: st.session_state.start_v = 1
if 'end_v' not in st.session_state: st.session_state.end_v = 7 
if 'card_index' not in st.session_state: st.session_state.card_index = 0

# --- 2. LOGIC & HELPER FUNCTIONS ---

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

def get_clean_length(text):
    """Räknar endast bas-tecken, ignorerar diakritika (Mn)."""
    return len([c for c in text if unicodedata.category(c) != 'Mn'])

def calculate_text_settings(text):
    """Beräknar fontstorlek och radhöjd dynamiskt baserat på ren textlängd."""
    clean_len = get_clean_length(text)
    
    if clean_len < 40:
        return "8.5vw", "1.3"
    elif clean_len < 80:
        return "7vw", "1.4"
    elif clean_len < 150:
        return "5.5vw", "1.5"
    elif clean_len < 300:
        return "4vw", "1.6"
    else:
        return "3vw", "1.7"

# --- 3. CSS STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Scheherazade+New:wght@400;700&display=swap');
    
    .stApp { background-color: #ffffff; }
    .block-container { padding: 0 !important; margin: 0 !important; max-width: 100% !important; }
    header, footer, [data-testid="stSidebar"] { display: none !important; }
    div[data-testid="stVerticalBlock"] { gap: 0rem !important; }

    .stButton > button {
        min-height: 0px !important;
        height: auto !important;
        padding: 4px 10px !important;
        line-height: 1.2 !important;
        border: none !important;
        background: transparent !important;
        color: #2E8B57 !important;
        font-weight: 700 !important;
    }

    /* Sidopilar för navigering */
    div[data-testid="column"]:nth-of-type(1) .stButton > button, 
    div[data-testid="column"]:nth-of-type(3) .stButton > button {
        font-size: 3rem !important;
        color: #e0e0e0 !important;
        height: 85vh !important;
        width: 100% !important;
    }

    .arabic-text {
        font-family: 'Scheherazade New', serif;
        direction: rtl;
        text-align: center;
        color: #000;
        width: 100%;
        padding: 0 30px;
    }

    .meta-tag {
        font-family: sans-serif; 
        font-size: 0.75rem;
        color: #888; 
        background: #f0f2f6; 
        padding: 3px 10px;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. DIALOG (SETTINGS) ---
@st.dialog("Inställningar")
def open_settings():
    st.markdown("### Välj Kapitel")
    new_chapter = st.slider("Kapitel", 1, 114, st.session_state.chapter)
    
    name_en, name_ar, total_verses = get_chapter_info(new_chapter)
    st.info(f"{name_en} ({name_ar}) har {total_verses} verser.")

    st.markdown("### Välj Versintervall")
    # Range slider för att välja start och slut samtidigt
    verse_range = st.slider(
        "Verser", 
        1, total_verses, 
        (st.session_state.start_v, min(st.session_state.end_v, total_verses))
    )

    if st.button("Ladda valda verser", type="primary", use_container_width=True):
        st.session_state.chapter = new_chapter
        st.session_state.start_v = verse_range[0]
        st.session_state.end_v = verse_range[1]
        st.session_state.card_index = 0
        st.rerun()

# --- 5. DATA PROCESSING & RENDER ---
verses_data = fetch_verses_data(st.session_state.chapter)
surah_en, surah_ar, _ = get_chapter_info(st.session_state.chapter)

# Filtrera ut de valda verserna
selected_data = verses_data[st.session_state.start_v - 1 : st.session_state.end_v]

if selected_data:
    # Säkerställ att indexet inte är utanför gränserna
    if st.session_state.card_index >= len(selected_data):
        st.session_state.card_index = 0
        
    current_verse = selected_data[st.session_state.card_index]
    raw_text = current_verse['text_uthmani']
    juz = current_verse['juz_number']
    verse_num = current_verse['verse_key'].split(':')[1]
    
    # Beräkna dynamisk styling
    font_size, line_height = calculate_text_settings(raw_text)
    progress_pct = ((st.session_state.card_index + 1) / len(selected_data)) * 100

    # Header
    hc1, hc2, hc3 = st.columns([1, 6, 1], vertical_alignment="center")
    with hc1: st.markdown(f'<div style="text-align:center;"><span class="meta-tag">Juz {juz}</span></div>', unsafe_allow_html=True)
    with hc2: 
        if st.button(f"{surah_en} | {surah_ar}", use_container_width=True):
            open_settings()
    with hc3: st.markdown(f'<div style="text-align:center;"><span class="meta-tag">#{verse_num}</span></div>', unsafe_allow_html=True)
    
    st.markdown(f'<div style="width:100%; height:3px; background:#f0f0f0;"><div style="width:{progress_pct}%; height:100%; background:#2E8B57;"></div></div>', unsafe_allow_html=True)

    # Main Card
    c_left, c_center, c_right = st.columns([1, 8, 1])
    
    with c_left:
        if st.button("❮", key="prev") and st.session_state.card_index > 0:
            st.session_state.card_index -= 1
            st.rerun()

    with c_center:
        st.markdown(f"""
        <div style="height: 82vh; display: flex; align-items: center; justify-content: center; overflow-y: auto;">
            <div class="arabic-text" style="font-size: {font_size}; line-height: {line_height};">
                {raw_text}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c_right:
        if st.button("❯", key="next") and st.session_state.card_index < len(selected_data) - 1:
            st.session_state.card_index += 1
            st.rerun()
else:
    st.button("Välj kapitel för att börja", on_click=open_settings)
