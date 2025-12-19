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
    else: return "3.5vw"

# --- 3. CSS "FULLSCREEN / FILL" ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Scheherazade+New:wght@400;700&display=swap');
    
    /* 1. NOLLSTÄLLNING AV STREAMLIT LAYOUT */
    .stApp { background-color: #ffffff; }
    
    .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
    }
    
    header, footer, [data-testid="stSidebar"] { display: none !important; }

    /* Minska gapet mellan rader drastiskt */
    div[data-testid="stVerticalBlock"] {
        gap: 0rem !important; 
    }

    /* 2. AGGRESSIV KNAPP-OPTIMERING (Gäller ALLA knappar först) */
    /* Detta gör Title-knappen supertunn */
    .stButton > button {
        min-height: 0px !important;
        height: auto !important;
        padding: 4px 10px !important; /* Minimal padding */
        line-height: 1.2 !important;
        border: none !important;
        background: transparent !important;
        color: #2E8B57 !important;
        font-weight: 700 !important;
    }
    
    /* Hover för Title-knappen */
    .stButton > button:hover {
        background: #f9f9f9 !important;
    }

    /* 3. ÅTERSTÄLL PILARNA (Override för Nav-knapparna) */
    /* Vi måste tvinga tillbaka höjden på pilarna eftersom vi plattade till dem ovan */
    div[data-testid="column"]:nth-of-type(1) .stButton > button, 
    div[data-testid="column"]:nth-of-type(3) .stButton > button {
        font-size: 3rem !important;
        color: #e0e0e0 !important;
        height: 90vh !important; /* Täcker nästan hela skärmen */
        width: 100% !important;
        padding: 0 !important; /* Ingen padding på pilarna */
        background: transparent !important;
    }

    /* Hover/Focus States för PILARNA */
    div[data-testid="column"]:nth-of-type(1) .stButton > button:hover, 
    div[data-testid="column"]:nth-of-type(3) .stButton > button:hover {
        color: #2E8B57 !important;
        background: transparent !important;
    }
    
    div[data-testid="column"]:nth-of-type(1) .stButton > button:focus, 
    div[data-testid="column"]:nth-of-type(3) .stButton > button:focus,
    div[data-testid="column"]:nth-of-type(1) .stButton > button:active, 
    div[data-testid="column"]:nth-of-type(3) .stButton > button:active {
        color: #e0e0e0 !important;
        background: transparent !important;
        box-shadow: none !important;
    }

    /* 4. TEXT STYLING */
    .arabic-text {
        font-family: 'Scheherazade New', serif;
        line-height: 1.6;
        direction: rtl;
        text-align: center;
        color: #000;
        width: 100%;
        padding: 0 20px;
    }

    /* Mindre taggar för att spara höjd */
    .meta-tag {
        font-family: sans-serif; 
        font-size: 0.7rem; /* Mindre text */
        color: #aaa; 
        font-weight: 600;
        background: #f8f8f8; 
        padding: 2px 8px; /* Mindre luft */
        border-radius: 8px;
        display: inline-block;
    }
    
    /* Styling för topp-raden för att ge den lite struktur */
    div[data-testid="stHorizontalBlock"]:first-of-type {
        border-bottom: 1px solid #eee;
        padding-top: 5px;
        padding-bottom: 5px;
        background-color: #ffffff;
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
        # Justerade kolumnbredder för att tighta till det
        hc1, hc2, hc3 = st.columns([1, 6, 1], vertical_alignment="center")
        
        with hc1:
            st.markdown(f'<div style="text-align:center;"><span class="meta-tag">Juz {juz}</span></div>', unsafe_allow_html=True)
        with hc2:
            # Titeln är nu en väldigt tunn knapp
            if st.button(f"{surah_en} | {surah_ar}", key="title_btn", use_container_width=True):
                open_settings()
        with hc3:
            st.markdown(f'<div style="text-align:center;"><span class="meta-tag">#{verse_num}</span></div>', unsafe_allow_html=True)
        
        # Progress bar - ultra-slim
        st.markdown(f"""
        <div style="width:100%; height:3px; background:#f0f0f0; margin-top: 0px;">
            <div style="width:{progress_pct}%; height:100%; background:#2E8B57; transition:width 0.3s;"></div>
        </div>
        """, unsafe_allow_html=True)

    # 2. HUVUDINNEHÅLL
    c_left, c_center, c_right = st.columns([1, 8, 1])
    
    with c_left:
        st.write("") # Lite distans från toppen
        if st.button("❮", key="prev"):
            if st.session_state.card_index > 0:
                st.session_state.card_index -= 1
                st.rerun()

    with c_center:
        st.markdown(f"""
        <div style="
            height: 85vh; /* Mer plats för text nu när headern är liten */
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
        if st.button("❯", key="next"):
            if st.session_state.card_index < len(selected_data) - 1:
                st.session_state.card_index += 1
                st.rerun()

else:
    st.warning("Ingen data. Öppna inställningar.")
