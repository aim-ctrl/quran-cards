import streamlit as st
import requests
import unicodedata
import streamlit.components.v1 as components
import re

# --- 1. SETUP & STATE ---
st.set_page_config(
    page_title="Quran Cards", 
    page_icon="📖", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

if 'chapter' not in st.session_state: st.session_state.chapter = 112 
if 'start_v' not in st.session_state: st.session_state.start_v = 1
if 'end_v' not in st.session_state: st.session_state.end_v = 4
if 'card_index' not in st.session_state: st.session_state.card_index = 0
if 'hifz_colors' not in st.session_state: st.session_state.hifz_colors = False
if 'qalqalah_mode' not in st.session_state: st.session_state.qalqalah_mode = True 
if 'show_links' not in st.session_state: st.session_state.show_links = False

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
    clean_len = get_clean_length(text)
    # Justerat storlekar något för bättre passform
    max_size, min_size = 7.0, 2.5
    short_threshold, long_threshold = 15, 400
    
    if clean_len <= short_threshold:
        final_size = max_size
        line_height = "2.0" 
    elif clean_len >= long_threshold:
        final_size = min_size
        line_height = "1.7"
    else:
        progr = (clean_len - short_threshold) / (long_threshold - short_threshold)
        final_size = max_size - (progr * (max_size - min_size))
        line_height = f"{1.9 - (progr * 0.3):.2f}"

    return f"{final_size:.2f}vw", line_height

# --- 3. MARKUP LOGIC ---

def apply_qalqalah_markup(text):
    qalqalah_letters = "\u0642\u0637\u0628\u062c\u062f"
    sukoon_marks = "\u0652\u06E1" 
    
    # 1. Sughra
    regex_sughra = f"([{qalqalah_letters}])([{sukoon_marks}])"
    text = re.sub(regex_sughra, r'<span class="q-sughra">\1\2</span>', text)

    # 2. Kubra
    regex_kubra = f"([{qalqalah_letters}])([\u064B-\u065F]*)$"
    text = re.sub(regex_kubra, r'<span class="q-kubra">\1\2</span>', text)
    
    return text

def apply_hifz_markup(text):
    words = text.split(" ")
    colored_words = []
    for word in words:
        if word:
            colored_words.append(f'<span class="h-start">{word[0]}</span>{word[1:]}')
        else:
            colored_words.append(word)
    return " ".join(colored_words)

# --- 4. CSS (CLEAN & TIGHT) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Scheherazade+New:wght@400;700&display=swap');
    
    .stApp { background-color: #ffffff; }
    .block-container { padding: 0 !important; margin: 0 !important; max-width: 100% !important; }
    header, footer, [data-testid="stSidebar"] { display: none !important; }
    div[data-testid="stVerticalBlock"] { gap: 0rem !important; }

    .stButton > button {
        min-height: 0px !important; height: auto !important; padding: 0px !important;
        line-height: 1.0 !important; border: none !important; background: transparent !important;
        color: #2E8B57 !important; font-weight: 900 !important; position: relative !important; z-index: 9999 !important; 
    }
    div[data-testid="column"]:nth-of-type(1) .stButton > button, 
    div[data-testid="column"]:nth-of-type(3) .stButton > button {
        opacity: 0 !important; height: 80vh !important; width: 0% !important; pointer-events: none !important; z-index: 10 !important;
    }

    /* CONTAINER */
    .arabic-container {
        font-family: 'Scheherazade New', serif;
        direction: rtl;
        text-align: center;
        width: 100%;
        position: relative;
        text-rendering: geometricPrecision; 
        -webkit-font-smoothing: antialiased;
        padding: 0;
        margin: 0;
    }
    
    /* LAGER - NOLLSTÄLL ALLT */
    .layer {
        position: absolute;
        top: 0;
        left: 0;
        right: 0; /* Tvinga full bredd */
        direction: rtl;
        text-align: center;
        white-space: normal; /* Inga konstiga radbrytningar */
        margin: 0;
        padding: 0;
        border: 0;
    }

    /* LAGER 1: HIGHLIGHT (Botten) */
    .layer-highlight {
        z-index: 1;
        /* Osynligt bläck-metoden */
        color: rgba(0, 0, 0, 0.01); 
    }
    .layer-highlight .q-sughra {
        background-color: #B3E5FC;
        border-radius: 4px;
        box-shadow: 2px 0 0 #B3E5FC, -2px 0 0 #B3E5FC; 
    }
    .layer-highlight .q-kubra {
        background-color: #FFCDD2;
        border-radius: 4px;
        box-shadow: 2px 0 0 #FFCDD2, -2px 0 0 #FFCDD2;
    }
    .layer-highlight .h-start { background-color: transparent; }

    /* LAGER 2: TEXT (Toppen) */
    .layer-text {
        color: #000;
        z-index: 2;
        pointer-events: none;
        background: transparent;
    }
    .layer-text .q-sughra, .layer-text .q-kubra { background-color: transparent; }
    .layer-text .h-start { color: #D35400; }

    .link-hint { color: #C0C0C0; font-size: 0.60em; opacity: 0.8; font-weight: normal; }
    .top-curtain { position: fixed; top: 0; left: 0; width: 100%; height: 4vh; background: white; z-index: 100; }
</style>
""", unsafe_allow_html=True)

# --- 5. SWIPE ---
add_swipe_js = """
<script>
    const doc = window.parent.document;
    let touchstartX = 0; let touchendX = 0;
    function handleSwipe() {
        if (doc.querySelector('div[data-testid="stDialog"]')) return;
        const diff = touchendX - touchstartX;
        if (Math.abs(diff) > 60) {
            if (diff > 0) { const b = Array.from(doc.querySelectorAll('button')).find(e => e.innerText === '❮'); if(b) b.click(); } 
            else { const b = Array.from(doc.querySelectorAll('button')).find(e => e.innerText === '❯'); if(b) b.click(); }
        }
    }
    doc.addEventListener('touchstart', e => { touchstartX = e.changedTouches[0].screenX; }, false);
    doc.addEventListener('touchend', e => { touchendX = e.changedTouches[0].screenX; handleSwipe(); }, false);
</script>
"""
components.html(add_swipe_js, height=0, width=0)

# --- 6. DIALOG ---
@st.dialog("Settings")
def open_settings():
    new_chapter = st.slider("Chapter", 1, 114, st.session_state.chapter)
    _, _, total_verses = get_chapter_info(new_chapter)

    default_range = (1, total_verses) if new_chapter != st.session_state.chapter else (st.session_state.start_v, min(st.session_state.end_v, total_verses))
    verse_range = st.slider("Verses", 1, total_verses, default_range, key=f"v_slider_{new_chapter}")
    
    c1, c2 = st.columns(2)
    with c1: hifz_val = st.toggle("Hifz Colors", value=st.session_state.hifz_colors)
    with c2: qalqala_val = st.toggle("Tajweed: Qalqalah", value=st.session_state.qalqalah_mode)
    show_links = st.toggle("Connection Hints", value=st.session_state.show_links)

    if st.button("Load", type="primary", use_container_width=True):
        st.session_state.chapter = new_chapter
        st.session_state.start_v = verse_range[0]
        st.session_state.end_v = verse_range[1]
        st.session_state.card_index = 0
        st.session_state.hifz_colors = hifz_val
        st.session_state.qalqalah_mode = qalqala_val
        st.session_state.show_links = show_links
        st.rerun()

# --- 7. RENDER ---
verses_data = fetch_verses_data(st.session_state.chapter)
surah_en, surah_ar, _ = get_chapter_info(st.session_state.chapter)
selected_data = verses_data[st.session_state.start_v - 1 : st.session_state.end_v]

if selected_data:
    if st.session_state.card_index >= len(selected_data): st.session_state.card_index = 0
    current_verse = selected_data[st.session_state.card_index]
    raw_text = current_verse['text_uthmani']
    
    font_size, line_height = calculate_text_settings(raw_text)
    
    processed_text = raw_text
    if st.session_state.qalqalah_mode:
        processed_text = apply_qalqalah_markup(processed_text)
    if st.session_state.hifz_colors and not st.session_state.qalqalah_mode:
        processed_text = apply_hifz_markup(processed_text)
    
    # Länkar
    prev_span = ""
    next_span = ""
    if st.session_state.show_links:
        if st.session_state.card_index > 0:
            p_text = selected_data[st.session_state.card_index - 1]['text_uthmani']
            prev_span = f'<span class="link-hint">{p_text.split(" ")[-1]}</span> '
        if st.session_state.card_index < len(selected_data) - 1:
            n_text = selected_data[st.session_state.card_index + 1]['text_uthmani']
            next_span = f' <span class="link-hint">{n_text.split(" ")[0]}</span>'

    # SAMMANFOGA ALLT PÅ EN ENDA RAD (Inga \n)
    full_html_content = f"{prev_span}{processed_text}{next_span}"
    
    container_style = f"font-size: {font_size}; line-height: {line_height};"
    
    # VIKTIGT: Här tar vi bort alla radbrytningar i f-strängen för att undvika spök-element
    layer_highlight = f'<div class="layer layer-highlight">{full_html_content}</div>'
    layer_text = f'<div class="layer layer-text">{full_html_content}</div>'

    final_html = f'<div class="arabic-container" style="{container_style}">{layer_highlight}{layer_text}</div>'

    # --- UI RENDER ---
    st.markdown('<div class="top-curtain"></div>', unsafe_allow_html=True)
    pct = ((st.session_state.card_index + 1) / len(selected_data)) * 100
    st.markdown(f'<div style="position:fixed;top:0;left:0;width:100%;height:4px;background:#f0f0f0;z-index:200;"><div style="width:{pct}%;height:100%;background:#2E8B57;"></div></div>', unsafe_allow_html=True)

    hc1, hc2, hc3 = st.columns([1, 4, 1], vertical_alignment="center")
    with hc2: 
        if st.button(f"Juz {current_verse['juz_number']} | Ch {st.session_state.chapter} | {surah_en} | Verse {current_verse['verse_key'].split(':')[1]}", use_container_width=True):
            open_settings()

    c_l, c_c, c_r = st.columns([1, 800, 1])
    with c_l:
        if st.button("❮", key="p") and st.session_state.card_index > 0:
            st.session_state.card_index -= 1
            st.rerun()
    with c_c:
        # Centrerings-container utanför HTML-blocket
        st.markdown(f"""
        <div style="position: fixed; top: 5vh; bottom: 0; left: 0; right: 0; display: flex; align-items: center; justify-content: center; overflow-y: auto; z-index: 1;">
            <div style="max-width: 90%; width: 600px; margin: auto; padding-bottom: 5vh;">
                {final_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c_r:
        if st.button("❯", key="n") and st.session_state.card_index < len(selected_data) - 1:
            st.session_state.card_index += 1
            st.rerun()
else:
    if st.button("Öppna inställningar", use_container_width=True): open_settings()
