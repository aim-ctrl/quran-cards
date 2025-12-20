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
def get_chapters_map():
    """Hämtar en lista med alla kapitelnamn för slidern."""
    try:
        resp = requests.get("https://api.quran.com/api/v4/chapters").json()
        return {c['id']: c['name_simple'] for c in resp['chapters']}
    except:
        return {i: f"Chapter {i}" for i in range(1, 115)}

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
    clean_len = get_clean_length(text)
    if clean_len < 40: return "8.5vw", "1.6"
    elif clean_len < 80: return "7vw", "1.7"
    elif clean_len < 150: return "5.5vw", "1.8"
    elif clean_len < 300: return "4vw", "1.9"
    else: return "3vw", "2.0"

# --- 3. CSS STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Scheherazade+New:wght@400;700&display=swap');
    
    .stApp { background-color: #ffffff; }
    .block-container { padding: 0 !important; margin: 0 !important; max-width: 100% !important; }
    header, footer, [data-testid="stSidebar"] { display: none !important; }
    div[data-testid="stVerticalBlock"] { gap: 0rem !important; }

    /* Central header-knapp */
    .stButton > button {
        min-height: 0px !important;
        height: auto !important;
        padding: 4px 0px !important;
        line-height: 1.2 !important;
        border: none !important;
        background: transparent !important;
        color: #2E8B57 !important;
        font-weight: 700 !important;
        font-size: 1.2rem !important;
    }

    /* Dölj pilar men behåll dem för Swipe-JS */
    .hidden-btn button {
        opacity: 0 !important;
        width: 0px !important;
        height: 0px !important;
        padding: 0 !important;
        pointer-events: none !important;
    }

    .arabic-text {
        font-family: 'Scheherazade New', serif;
        direction: rtl;
        text-align: center;
        color: #000;
        width: 100%;
        padding: 0 15px;
    }
    
    .header-wrapper {
        padding-top: 25px;
        padding-bottom: 10px;
        border-bottom: 1px solid #f0f0f0;
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
            // Blockera swipe om dialogen är öppen
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
    ch_map = get_chapters_map()
    
    # Slider som visar namnet på kapitlet
    new_chapter = st.slider(
        "Select Chapter", 
        1, 114, 
        st.session_state.chapter,
        format_func=lambda x: f"{x}. {ch_map.get(x, '')}"
    )
    
    _, _, total_verses = get_chapter_info(new_chapter)
    
    if new_chapter != st.session_state.chapter:
        default_range = (1, total_verses)
    else:
        default_range = (st.session_state.start_v, min(st.session_state.end_v, total_verses))

    verse_range = st.slider("Verses", 1, total_verses, default_range)

    if st.button("Load", type="primary", use_container_width=True):
        st.session_state.chapter = new_chapter
        st.session_state.start_v = verse_range[0]
        st.session_state.end_v = verse_range[1]
        st.session_state.card_index = 0
        st.rerun()

# --- 6. RENDER ---
verses_data = fetch_verses_data(st.session_state.chapter)
surah_en, surah_ar, _ = get_chapter_info(st.session_state.chapter)
selected_data = verses_data[st.session_state.start_v - 1 : st.session_state.end_v]

if selected_data:
    current_verse = selected_data[st.session_state.card_index]
    raw_text = current_verse['text_uthmani']
    juz = current_verse['juz_number']
    verse_num = current_verse['verse_key'].split(':')[1]
    
    font_size, line_height = calculate_text_settings(raw_text)
    progress_pct = ((st.session_state.card_index + 1) / len(selected_data)) * 100

    # Progress bar
    st.markdown(f'<div style="width:100%; height:3px; background:#f0f0f0;"><div style="width:{progress_pct}%; height:100%; background:#2E8B57; transition: 0.3s;"></div></div>', unsafe_allow_html=True)

    # Header (Sammanslagen info)
    st.markdown('<div class="header-wrapper">', unsafe_allow_html=True)
    header_label = f"Juz {juz} | {surah_en} | {surah_ar} | #{verse_num}"
    if st.button(header_label, use_container_width=True):
        open_settings()
    st.markdown('</div>', unsafe_allow_html=True)

    # Main Card area
    c_left, c_main, c_right = st.columns([0.1, 9.8, 0.1])
    
    with c_left:
        st.markdown('<div class="hidden-btn">', unsafe_allow_html=True)
        if st.button("❮", key="prev") and st.session_state.card_index > 0:
            st.session_state.card_index -= 1
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with c_main:
        st.markdown(f"""
        <div style="height: 80vh; display: flex; align-items: center; justify-content: center;">
            <div class="arabic-text" style="font-size: {font_size}; line-height: {line_height};">
                {raw_text}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c_right:
        st.markdown('<div class="hidden-btn">', unsafe_allow_html=True)
        if st.button("❯", key="next") and st.session_state.card_index < len(selected_data) - 1:
            st.session_state.card_index += 1
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.button("Öppna inställningar", on_click=open_settings)
