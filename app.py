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

# --- 2. HÄMTA DATA ---
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
    if l < 50: return "40px"
    elif l < 100: return "35px"
    elif l < 200: return "30px"
    elif l < 400: return "25px"
    elif l < 700: return "20px"
    else: return "16px"

# --- 3. CSS DESIGN (Uppdaterad för vitt kort) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Scheherazade+New:wght@400;700&display=swap');
    
    /* 1. BAKGRUND FÖR HELA APPEN (Ljusgrå för kontrast) */
    .stApp {
        background-color: #f0f2f6;
    }

    /* 2. DÖLJ MENYER */
    header {display: none !important;}
    [data-testid="stSidebar"] {display: none !important;}
    footer {display: none !important;}
    .stApp { margin-top: -50px; }

    /* 3. STYLA MITT-KOLUMNEN TILL ETT KORT */
    /* Detta väljer den andra kolumnen (där kortet ligger) */
    div[data-testid="column"]:nth-of-type(2) > div {
        background-color: #ffffff !important; /* TVINGA VIT BAKGRUND */
        border-radius: 16px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        padding: 0px !important; /* Ta bort padding så headern når kanten */
        overflow: hidden;
    }

    /* Header inuti kortet */
    .internal-header {
        background-color: #f8f9fa;
        border-bottom: 1px solid #eee;
        padding: 10px 0px;
        margin-bottom: 10px;
    }

    /* Titel-knappen (Gör den mörkgrön och tydlig) */
    div[data-testid="stButton"] button {
        border: none;
        background: transparent;
        color: #2E8B57 !important; /* Tvinga färgen */
        font-weight: 700;
        font-size: 1.3rem;
        width: 100%;
        margin-top: -5px;
    }
    div[data-testid="stButton"] button:hover {
        color: #1e5c39 !important;
        background: rgba(0,0,0,0.05);
    }
    
    /* Pilarna på sidorna (vänster/höger kolumn) */
    div[data-testid="column"]:nth-of-type(1) button, 
    div[data-testid="column"]:nth-of-type(3) button {
        color: #ccc !important;
        font-size: 3rem;
        height: 70vh;
    }
    div[data-testid="column"]:nth-of-type(1) button:hover, 
    div[data-testid="column"]:nth-of-type(3) button:hover {
        color: #2E8B57 !important;
        background-color: transparent;
    }

    /* Arabisk Text */
    .arabic-text {
        font-family: 'Scheherazade New', serif;
        line-height: 2.2;
        direction: rtl;
        text-align: center;
        color: #000000 !important; /* Tvinga SVART text */
        width: 100%;
        padding: 0 20px;
    }

    /* Meta taggar (Juz / Vers nr) */
    .meta-text {
        font-family: sans-serif; 
        font-size: 0.9rem; 
        color: #555;
        font-weight: 600; 
        background-color: #e8f5e9; 
        padding: 5px 12px; 
        border-radius: 8px;
        display: inline-block;
    }

    /* Progress bar */
    .progress-container { width: 100%; height: 4px; background-color: #eee; margin-top: -10px; margin-bottom: 20px;}
    .progress-bar { height: 100%; background-color: #2E8B57; transition: width 0.3s ease; }

</style>
""", unsafe_allow_html=True)

# --- 4. POPUP MENY ---
@st.dialog("Inställningar")
def open_settings():
    st.write("Konfigurera läsning")
    new_chapter = st.number_input("Kapitel (1-114)", 1, 114, st.session_state.chapter)
    _, _, total_verses = get_chapter_info(new_chapter)
    
    c1, c2 = st.columns(2)
    with c1:
        default_start = 1 if new_chapter != st.session_state.chapter else st.session_state.start_v
        new_start = st.number_input("Startvers", 1, total_verses, default_start)
    with c2:
        default_end = total_verses if new_chapter != st.session_state.chapter else st.session_state.end_v
        new_end = st.number_input("Slutvers", new_start, total_verses, default_end)

    if st.button("Klar", type="primary", use_container_width=True):
        st.session_state.chapter = new_chapter
        st.session_state.start_v = new_start
        st.session_state.end_v = new_end
        st.session_state.card_index = 0
        st.rerun()

# --- 5. LOGIK ---
verses_data = fetch_verses_data(st.session_state.chapter)
surah_en, surah_ar, _ = get_chapter_info(st.session_state.chapter)
start_idx = st.session_state.start_v - 1
end_idx = st.session_state.end_v
selected_data = verses_data[start_idx : end_idx]

if st.session_state.card_index >= len(selected_data): st.session_state.card_index = 0

# --- 6. RENDER UI ---
if selected_data:
    obj = selected_data[st.session_state.card_index]
    raw_text = obj['text_uthmani']
    juz = obj['juz_number']
    verse_num = obj['verse_key'].split(':')[1]
    
    progress_pct = ((st.session_state.card_index + 1) / len(selected_data)) * 100
    font_size = calculate_font_size(raw_text)

    # Layout med 3 kolumner. Mitten-kolumnen stylas via CSS att bli "kortet"
    col_l, col_c, col_r = st.columns([1, 10, 1])
    
    with col_l:
        st.write("") 
        st.write("")
        st.write("")
        if st.button("❮", key="prev", use_container_width=True):
            if st.session_state.card_index > 0:
                st.session_state.card_index -= 1
                st.rerun()

    with col_c:
        # --- HEADER PÅ KORTET ---
        # Vi skapar en "falsk" header med bakgrundsfärg via CSS på containern, 
        # men vi kan lägga till en container här för struktur.
        with st.container():
            st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True) # Spacer top
            
            # Header-rad med Juz, Titel-knapp, Versnummer
            h1, h2, h3 = st.columns([1, 4, 1], gap="small", vertical_alignment="center")
            
            with h1:
                st.markdown(f'<div style="text-align:center;"><span class="meta-text">Juz {juz}</span></div>', unsafe_allow_html=True)
            
            with h2:
                # TITEL-KNAPPEN
                label = f"{surah_en}  |  {surah_ar}"
                if st.button(label, use_container_width=True):
                    open_settings()
            
            with h3:
                st.markdown(f'<div style="text-align:center;"><span class="meta-text"># {verse_num}</span></div>', unsafe_allow_html=True)
            
            st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True) # Spacer bottom
            
            # Progress Bar
            st.markdown(f"""
            <div class="progress-container">
                <div class="progress-bar" style="width: {progress_pct}%;"></div>
            </div>
            """, unsafe_allow_html=True)

        # --- INNEHÅLL ---
        # Scrollbar container för texten
        st.markdown(f"""
        <div style="height: 55vh; display: flex; align-items: center; justify-content: center; overflow-y: auto;">
            <div class="arabic-text" style="font-size: {font_size};">{raw_text}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_r:
        st.write("")
        st.write("")
        st.write("")
        if st.button("❯", key="next", use_container_width=True):
            if st.session_state.card_index < len(selected_data) - 1:
                st.session_state.card_index += 1
                st.rerun()
else:
    st.info("Ingen data. Klicka på 'Klar' för att ladda.")
