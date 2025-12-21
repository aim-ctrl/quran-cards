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
if 'show_translation' not in st.session_state: st.session_state.show_translation = False

# --- 2. LOGIC & HELPER FUNCTIONS ---

@st.cache_data(show_spinner=False)
def get_chapter_info(chapter_id):
    try:
        resp = requests.get(f"https://api.quran.com/api/v4/chapters/{chapter_id}").json()
        return resp['chapter']['name_simple'], resp['chapter']['name_arabic'], resp['chapter']['verses_count']
    except: return "Unknown", "", 0

@st.cache_data(show_spinner=False)
def fetch_verses_data(chapter_num):
    # UPPDATERAD URL: Inkluderar translations=131 (Saheeh International)
    url = f"https://api.quran.com/api/v4/verses/by_chapter/{chapter_num}?language=en&words=false&translations=131&fields=text_uthmani,juz_number&per_page=1000"
    try: return requests.get(url).json()['verses']
    except: return []

def get_clean_length(text):
    return len([c for c in text if unicodedata.category(c) != 'Mn'])

def calculate_text_settings(text):
    clean_len = get_clean_length(text)
    
    max_size = 7.0
    min_size = 2.5
    
    short_threshold = 15
    long_threshold = 400
    
    if clean_len <= short_threshold:
        final_size = max_size
        line_height = "1.9"
    elif clean_len >= long_threshold:
        final_size = min_size
        line_height = "1.65"
    else:
        progr = (clean_len - short_threshold) / (long_threshold - short_threshold)
        size_diff = max_size - min_size
        final_size = max_size - (progr * size_diff)
        line_height_val = 1.8 - (progr * 0.3)
        line_height = f"{line_height_val:.2f}"

    return f"{final_size:.2f}vw", line_height


# --- 3. CSS STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Scheherazade+New:wght@400;700&display=swap');
    
    .stApp { background-color: #ffffff; }
    .block-container { padding: 0 !important; margin: 0 !important; max-width: 100% !important; }
    header, footer, [data-testid="stSidebar"] { display: none !important; }
    div[data-testid="stVerticalBlock"] { gap: 0rem !important; }

    /* --- VIKTIGT: Knapp-styling med högsta Z-Index --- */
    .stButton > button {
        min-height: 0px !important;
        height: auto !important;
        padding: 0px 0px !important;
        line-height: 1.0 !important;
        border: none !important;
        background: transparent !important;
        color: #2E8B57 !important;
        font-weight: 900 !important;
        
        /* Denna ser till att knappen ligger ovanpå ALLT (även progress bar) */
        position: relative !important; 
        z-index: 9999 !important; 
    }

    /* Sidopilar */
    div[data-testid="column"]:nth-of-type(1) .stButton > button, 
    div[data-testid="column"]:nth-of-type(3) .stButton > button {
        opacity: 0 !important;
        height: 80vh !important;
        width: 0% !important;
        pointer-events: none !important;
        z-index: 10 !important;
    }

    .arabic-text {
        font-family: 'Scheherazade New', serif;
        direction: rtl;
        text-align: center;
        color: #000;
        width: 100%;
        padding: 0px 0px;
    }

    /* NY CSS: Styling för översättningen */
    .translation-text {
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 1.2rem;
        line-height: 1.5;
        color: #666;
        text-align: center;
        margin-top: 2rem;
        direction: ltr;
    }
    
    /* En "gardin" som döljer texten när den scrollar upp bakom headern */
    .top-curtain {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 4vh; 
        background: white;
        z-index: 100; 
    }
</style>
""", unsafe_allow_html=True)

# --- 4. SWIPE LOGIC ---
def add_swipe_support():
    swipe_js = """
    <script>
        const doc = window.parent.document;
        let touchstartX = 0;
        let touchendX = 0;

        function handleSwipe() {
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

# --- 5. DIALOG ---
@st.dialog("Settings")
def open_settings():
    new_chapter = st.slider("Chapter", 1, 114, st.session_state.chapter)
    _, _, total_verses = get_chapter_info(new_chapter)

    if new_chapter != st.session_state.chapter:
        default_range = (1, total_verses)
    else:
        default_range = (st.session_state.start_v, min(st.session_state.end_v, total_verses))

    verse_range = st.slider(
        "Verses", 1, total_verses, default_range,
        key=f"v_slider_{new_chapter}"
    )

    # TOGGLE: Välj om översättning ska visas
    show_trans = st.toggle("Show Translation", value=st.session_state.show_translation)

    if st.button("Load", type="primary", use_container_width=True):
        st.session_state.chapter = new_chapter
        st.session_state.start_v = verse_range[0]
        st.session_state.end_v = verse_range[1]
        st.session_state.card_index = 0
        st.session_state.show_translation = show_trans # Spara inställningen
        st.rerun()

# --- 6. RENDER ---
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

    # 1. TOP CURTAIN
    st.markdown('<div class="top-curtain"></div>', unsafe_allow_html=True)

    # 2. PROGRESS BAR
    st.markdown(f"""
    <div style="
        position: fixed; 
        top: 0; 
        left: 0; 
        width: 100%; 
        height: 4px; 
        background: #f0f0f0; 
        z-index: 200;">
        <div style="width:{progress_pct}%; height:100%; background:#2E8B57;"></div>
    </div>
    """, unsafe_allow_html=True)

    # 3. HEADER
    hc1, hc2, hc3 = st.columns([1, 4, 1], vertical_alignment="center")
    with hc2: 
        if st.button(f"Juz {juz} | Chapter {st.session_state.chapter} | {surah_en} | {surah_ar} | Verse {verse_num}", use_container_width=True):
            open_settings()

    # 4. MAIN CARD
    c_left, c_center, c_right = st.columns([1, 800, 1])
    
    with c_left:
        if st.button("❮", key="prev") and st.session_state.card_index > 0:
            st.session_state.card_index -= 1
            st.rerun()

    with c_center:
        text_area_top = "5vh"    
        text_area_bottom = "0vh" 

        # Hämta översättning
        translation_div = ""
        if st.session_state.show_translation:
            try:
                # Kolla så vi har data
                trans_data = current_verse.get('translations', [])
                if trans_data:
                    trans_text = trans_data[0]['text']
                    translation_div = f'<div class="translation-text">{trans_text}</div>'
            except:
                translation_div = ""

        # VIKTIGT: Här bygger vi HTML-strängen utan indrag för att undvika Markdown-fel
        html_content = f"""
<div style="position: fixed; top: {text_area_top}; bottom: {text_area_bottom}; left: 0; right: 0; width: 100%; display: flex; align-items: center; justify-content: center; overflow-y: auto; z-index: 1;">
    <div style="max-width: 90%; width: 600px; margin: auto; padding-bottom: 5vh;">
        <div class="arabic-text" style="font-size: {font_size}; line-height: {line_height};">
            {raw_text}
        </div>
        {translation_div}
    </div>
</div>
"""
        st.markdown(html_content, unsafe_allow_html=True)

    with c_right:
        if st.button("❯", key="next") and st.session_state.card_index < len(selected_data) - 1:
            st.session_state.card_index += 1
            st.rerun()
else:
    if st.button("Öppna inställningar", use_container_width=True):
        open_settings()
