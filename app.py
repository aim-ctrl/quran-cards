import streamlit as st
import requests
import unicodedata
import streamlit.components.v1 as components

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
    return len([c for c in text if unicodedata.category(c) != 'Mn'])

def calculate_text_settings(text):
    # Vi antar att denna funktion finns definierad någon annanstans i din kod
    clean_len = get_clean_length(text)
    
    # Beräkna storleken baserat på din formel: (7.5 - 0.01 * längd)
    size_value = 7.5 - (0.02 * clean_len)
    
    # Returnera det beräknade värdet med "vw" och den konstanta höjden "2.0"
    return f"{size_value}vw", "1.85"


# --- 3. CSS STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Scheherazade+New:wght@400;700&display=swap');
    
    .stApp { background-color: #ffffff; }
    .block-container { padding: 0 !important; margin: 0 !important; max-width: 100% !important; }
    header, footer, [data-testid="stSidebar"] { display: none !important; }
    div[data-testid="stVerticalBlock"] { gap: 0rem !important; }

    /* Knapp-styling för titeln */
    .stButton > button {
        min-height: 0px !important;
        height: auto !important;
        padding: 0px 0px !important;
        line-height: 1.0 !important;
        border: none !important;
        background: transparent !important;
        color: #2E8B57 !important;
        font-weight: 900 !important;
    }

    /* Sidopilar (Dolda men aktiva för Swipe-skriptet) */
    div[data-testid="column"]:nth-of-type(1) .stButton > button, 
    div[data-testid="column"]:nth-of-type(3) .stButton > button {
        opacity: 0 !important;
        height: 80vh !important;
        width: 100% !important;
        pointer-events: none !important;
    }

    .arabic-text {
        font-family: 'Scheherazade New', serif;
        direction: rtl;
        text-align: center;
        color: #000;
        width: 100%;
        padding: 0 10px;
    }
    
    .header-wrapper {
        padding-top: 20px;
        padding-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. SWIPE LOGIC (JAVASCRIPT) ---
def add_swipe_support():
    swipe_js = """
    <script>
        const doc = window.parent.document;
        let touchstartX = 0;
        let touchendX = 0;

        function handleSwipe() {
            // Blockera swipe om dialogrutan (Settings) är öppen
            if (doc.querySelector('div[data-testid="stDialog"]')) return;

            const diff = touchendX - touchstartX;
            if (Math.abs(diff) > 60) {
                if (diff > 0) {
                    const prevBtn = Array.from(doc.querySelectorAll('button')).find(el => el.innerText === '❮');
                    if (prevBtn) prevBtn.click();
                } else {
                    const nextBtn = Array.from(doc.querySelectorAll('button')).find(el => el.innerText === '❯');
                    if (nextBtn) nextBtn.click();
                }
            }
        }
        doc.addEventListener('touchstart', e => { touchstartX = e.changedTouches[0].screenX; }, false);
        doc.addEventListener('touchend', e => { touchendX = e.changedTouches[0].screenX; handleSwipe(); }, false);
    </script>
    """
    components.html(swipe_js, height=0, width=0)

add_swipe_support()

# --- 5. DIALOG (SETTINGS) ---
@st.dialog("Settings")
def open_settings():
    # Enkel slider med bara siffror (exkluderar kapitelnamn-logiken)
    new_chapter = st.slider("Chapter", 1, 114, st.session_state.chapter)
    
    _, _, total_verses = get_chapter_info(new_chapter)

    if new_chapter != st.session_state.chapter:
        default_range = (1, total_verses)
    else:
        default_range = (st.session_state.start_v, min(st.session_state.end_v, total_verses))

    # Vers-slider med unik key för att undvika krasch vid kapitelbyte
    verse_range = st.slider(
        "Verses", 1, total_verses, default_range,
        key=f"v_slider_{new_chapter}"
    )

    if st.button("Load", type="primary", use_container_width=True):
        st.session_state.chapter = new_chapter
        st.session_state.start_v = verse_range[0]
        st.session_state.end_v = verse_range[1]
        st.session_state.card_index = 0
        st.rerun()

# --- 6. DATA PROCESSING & RENDER ---
verses_data = fetch_verses_data(st.session_state.chapter)
surah_en, surah_ar, _ = get_chapter_info(st.session_state.chapter)
selected_data = verses_data[st.session_state.start_v - 1 : st.session_state.end_v]

if selected_data:
    if st.session_state.card_index >= len(selected_data):
        st.session_state.card_index = 0
        
    current_verse = selected_data[st.session_state.card_index]
    raw_text = current_verse['text_uthmani']
    juz = current_verse['juz_number']
    verse_num = current_verse['verse_key'].split(':')[1]
    
    font_size, line_height = calculate_text_settings(raw_text)
    progress_pct = ((st.session_state.card_index + 1) / len(selected_data)) * 100

    # 1. Progress Bar
    st.markdown(f'<div style="width:100%; height:3px; background:#f0f0f0;"><div style="width:{progress_pct}%; height:100%; background:#2E8B57;"></div></div>', unsafe_allow_html=True)

    # 2. Header (hc1: Juz, hc2: Namn, hc3: Vers)
    st.markdown('<div class="header-wrapper">', unsafe_allow_html=True)
    hc1, hc2, hc3 = st.columns([1, 4, 1], vertical_alignment="center")
    with hc2: 
        if st.button(f"Juz {juz} | Chapter {st.session_state.chapter} | {surah_en} | {surah_ar} | Verse {verse_num}", use_container_width=True):
            open_settings()
    st.markdown('</div>', unsafe_allow_html=True)

    # 3. Main Card
    c_left, c_center, c_right = st.columns([1, 20, 1])
    
    with c_left:
        if st.button("❮", key="prev") and st.session_state.card_index > 0:
            st.session_state.card_index -= 1
            st.rerun()

    with c_center:
        st.markdown(f"""
        <div style="height: 80vh; display: flex; align-items: center; justify-content: center; overflow-y: auto;">
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
    if st.button("Öppna inställningar", use_container_width=True):
        open_settings()
