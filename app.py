import streamlit as st
import requests

st.set_page_config(
    page_title="Quran Cards", 
    page_icon="📖", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 1. SETUP & STATE ---
# Initiera variabler i minnet om de inte finns
if 'chapter' not in st.session_state: st.session_state.chapter = 1
if 'start_v' not in st.session_state: st.session_state.start_v = 1
if 'end_v' not in st.session_state: st.session_state.end_v = 7 # Standardvärde
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

# --- 3. CSS DESIGN ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Scheherazade+New:wght@400;700&display=swap');
    
    /* DÖLJ ALLT STANDARD-UI */
    header {display: none !important;}
    [data-testid="stSidebar"] {display: none !important;}
    footer {display: none !important;}
    .stApp { margin-top: -60px; } /* Dra upp innehållet eftersom headern är borta */

    /* STYLING FÖR KORT-CONTAINER */
    .quran-card-container {
        background-color: #ffffff;
        border-radius: 16px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        padding: 0;
        overflow: hidden;
        margin-top: 20px;
    }

    /* HEADER INUTI KORTET (Streamlit columns) */
    .card-header-area {
        background-color: #f8f9fa;
        border-bottom: 1px solid #eee;
        padding: 10px 5px;
    }

    /* Gör så att titel-knappen ser ut som text */
    div[data-testid="stButton"] button {
        border: none;
        background: transparent;
        color: #2E8B57;
        font-weight: 700;
        font-size: 1.2rem;
        width: 100%;
    }
    div[data-testid="stButton"] button:hover {
        color: #1e5c39;
        background: rgba(0,0,0,0.05);
    }
    div[data-testid="stButton"] button:focus {
        border: none;
        color: #2E8B57;
        outline: none; 
        box-shadow: none;
    }

    /* NAVIGATION KNAPPAR (Vänster/Höger pilar) */
    .nav-btn {
        font-size: 40px; 
        background: transparent; 
        border: none; 
        color: #ccc; 
        cursor: pointer;
        width: 100%;
        height: 70vh;
    }
    .nav-btn:hover { color: #2E8B57; background: rgba(0,0,0,0.02); }

    /* ARABISK TEXT */
    .arabic-text {
        font-family: 'Scheherazade New', serif;
        line-height: 2.2;
        direction: rtl;
        text-align: center;
        color: #000;
        width: 100%;
        padding: 20px;
    }

    /* PROGRESS BAR */
    .progress-track { width: 100%; height: 4px; background-color: #eee; }
    .progress-fill { height: 100%; background-color: #2E8B57; transition: width 0.3s ease; }
    
    /* Justeringar för metataggar */
    .meta-text {
        font-family: sans-serif; 
        font-size: 0.8rem; 
        color: #555;
        font-weight: 600; 
        background-color: #e8f5e9; 
        padding: 4px 10px; 
        border-radius: 8px;
        display: inline-block;
        text-align: center;
    }

</style>
""", unsafe_allow_html=True)

# --- 4. POPUP MENY (DIALOG) ---
@st.dialog("Inställningar")
def open_settings():
    st.write("Välj vad du vill läsa")
    
    # Val av kapitel
    new_chapter = st.number_input("Kapitel (1-114)", 1, 114, st.session_state.chapter)
    
    # Uppdatera info baserat på valt kapitel (för att veta max antal verser)
    _, _, total_verses = get_chapter_info(new_chapter)
    
    c1, c2 = st.columns(2)
    with c1:
        # Om vi bytt kapitel, återställ start till 1, annars behåll nuvarande
        default_start = 1 if new_chapter != st.session_state.chapter else st.session_state.start_v
        new_start = st.number_input("Startvers", 1, total_verses, default_start)
    with c2:
        default_end = total_verses if new_chapter != st.session_state.chapter else st.session_state.end_v
        # Se till att slut inte är mindre än start
        new_end = st.number_input("Slutvers", new_start, total_verses, default_end)

    if st.button("Spara & Ladda", type="primary", use_container_width=True):
        st.session_state.chapter = new_chapter
        st.session_state.start_v = new_start
        st.session_state.end_v = new_end
        st.session_state.card_index = 0 # Återställ kort till början
        st.rerun()

# --- 5. LOGIK ---
# Hämta data baserat på session_state (som satts i popupen)
verses_data = fetch_verses_data(st.session_state.chapter)
surah_en, surah_ar, _ = get_chapter_info(st.session_state.chapter)

# Filtrera data
max_verses_in_selection = len(verses_data)
# Justera indexering eftersom listor är 0-baserade men verser 1-baserade
start_idx = st.session_state.start_v - 1
end_idx = st.session_state.end_v
selected_data = verses_data[start_idx : end_idx]

# Säkerställ index
if st.session_state.card_index >= len(selected_data): st.session_state.card_index = 0

# --- 6. RENDER UI ---

if selected_data:
    obj = selected_data[st.session_state.card_index]
    raw_text = obj['text_uthmani']
    juz = obj['juz_number']
    verse_key = obj['verse_key']
    verse_num = verse_key.split(':')[1]
    
    # Framsteg i den valda sektionen
    current_step = st.session_state.card_index + 1
    total_steps = len(selected_data)
    progress_pct = (current_step / total_steps) * 100
    
    font_size = calculate_font_size(raw_text)

    col_l, col_c, col_r = st.columns([1, 10, 1])
    
    # VÄNSTER PIL
    with col_l:
        st.write("") # Spacer
        st.write("")
        st.write("")
        if st.button("❮", key="prev"):
            if st.session_state.card_index > 0:
                st.session_state.card_index -= 1
                st.rerun()

    # KORTET (MITTEN)
    with col_c:
        # Vi bygger kortet visuellt med en container
        with st.container():
            st.markdown('<div class="quran-card-container">', unsafe_allow_html=True)
            
            # --- HEADER DELEN (som nu är interaktiv) ---
            st.markdown('<div class="card-header-area">', unsafe_allow_html=True)
            h_col1, h_col2, h_col3 = st.columns([1, 3, 1], gap="small")
            
            with h_col1:
                st.markdown(f'<div style="text-align:center; margin-top: 5px;"><span class="meta-text">Juz {juz}</span></div>', unsafe_allow_html=True)
            
            with h_col2:
                # DETTA ÄR KNAPPEN SOM ÖPPNAR POPUP
                # Vi visar både engelska och arabiska namnet på knappen
                label = f"{surah_en}  |  {surah_ar}"
                if st.button(label, use_container_width=True):
                    open_settings()
            
            with h_col3:
                st.markdown(f'<div style="text-align:center; margin-top: 5px;"><span class="meta-text"># {verse_num}</span></div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True) 
            # --- SLUT HEADER ---

            # Progress Bar
            st.markdown(f"""
            <div class="progress-track">
                <div class="progress-fill" style="width: {progress_pct}%;"></div>
            </div>
            """, unsafe_allow_html=True)

            # Innehåll
            st.markdown(f"""
            <div style="height: 60vh; display: flex; align-items: center; justify-content: center; overflow-y: auto;">
                <div class="arabic-text" style="font-size: {font_size};">{raw_text}</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True) # Stänger quran-card-container

    # HÖGER PIL
    with col_r:
        st.write("")
        st.write("")
        st.write("")
        if st.button("❯", key="next"):
            if st.session_state.card_index < len(selected_data) - 1:
                st.session_state.card_index += 1
                st.rerun()

else:
    st.info("Ingen data laddad. Klicka på inställningar.")
