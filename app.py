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
if 'hifz_colors' not in st.session_state: st.session_state.hifz_colors = False
if 'madd_colors' not in st.session_state: st.session_state.madd_colors = False
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

def apply_hifz_coloring(text):
    """Färgar första bokstaven i varje ord orange."""
    words = text.split(" ")
    colored_words = []
    highlight_color = "#D35400" 
    
    for word in words:
        if word:
            colored_word = f'<span style="color: {highlight_color};">{word[0]}</span>{word[1:]}'
            colored_words.append(colored_word)
        else:
            colored_words.append(word)
            
    return " ".join(colored_words)

def apply_madd_coloring(text):
    """Färgar madd-tecknet (~) rosa och gör det tjockare."""
    madd_char = '\u0653'
    color = "#FF1493" # DeepPink
    
    # Här lägger vi till font-weight: bold och font-size: 1.3em
    # position: relative används för att säkerställa att tecknet inte hoppar konstigt i höjdled
    replacement = f'<span style="color: {color}; font-weight: 900; font-size: 1.3em; line-height: 0;">{madd_char}</span>'
    
    return text.replace(madd_char, replacement)

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
        padding: 0px 0px !important;
        line-height: 1.0 !important;
        border: none !important;
        background: transparent !important;
        color: #2E8B57 !important;
        font-weight: 900 !important;
        position: relative !important; 
        z-index: 9999 !important; 
    }

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
    
    .link-hint {
        color: #C0C0C0; 
        font-size: 0.60em; 
        opacity: 0.8;
        font-weight: normal;
    }
    
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
    
    col_sett_1, col_sett_2 = st.columns(2)
    with col_sett_1:
        hifz_colors = st.toggle("Hifz Colors (Start Letters)", value=st.session_state.hifz_colors)
    with col_sett_2:
        madd_colors = st.toggle("Madd Colors (Pink)", value=st.session_state.madd_colors)
        
    show_links = st.toggle("Connection Hints (Robt)", value=st.session_state.show_links)

    if st.button("Load", type="primary", use_container_width=True):
        st.session_state.chapter = new_chapter
        st.session_state.start_v = verse_range[0]
        st.session_state.end_v = verse_range[1]
        st.session_state.card_index = 0
        st.session_state.hifz_colors = hifz_colors
        st.session_state.madd_colors = madd_colors
        st.session_state.show_links = show_links
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

    # 1. PREPARERA HUVUDTEXTEN
    display_text = raw_text
    
    if st.session_state.hifz_colors:
        display_text = apply_hifz_coloring(display_text)
        
    if st.session_state.madd_colors:
        display_text = apply_madd_coloring(display_text)

    # 2. HANTERA KOPPLINGAR (ROBT) - INLINE
    prev_span = ""
    next_span = ""
    
    if st.session_state.show_links:
        if st.session_state.card_index > 0:
            prev_verse_text = selected_data[st.session_state.card_index - 1]['text_uthmani']
            last_word = prev_verse_text.split(" ")[-1]
            prev_span = f'<span class="link-hint">{last_word}</span> '
        
        if st.session_state.card_index < len(selected_data) - 1:
            next_verse_text = selected_data[st.session_state.card_index + 1]['text_uthmani']
            first_word = next_verse_text.split(" ")[0]
            next_span = f' <span class="link-hint">{first_word}</span>'

    # Slå ihop allt till en rad
    final_html_text = f"{prev_span}{display_text}{next_span}"

    # 3. GUI RENDER
    st.markdown('<div class="top-curtain"></div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div style="
        position: fixed; top: 0; left: 0; width: 100%; height: 4px; 
        background: #f0f0f0; z-index: 200;">
        <div style="width:{progress_pct}%; height:100%; background:#2E8B57;"></div>
    </div>
    """, unsafe_allow_html=True)

    hc1, hc2, hc3 = st.columns([1, 4, 1], vertical_alignment="center")
    with hc2: 
        if st.button(f"Juz {juz} | Chapter {st.session_state.chapter} | {surah_en} | {surah_ar} | Verse {verse_num}", use_container_width=True):
            open_settings()

    c_left, c_center, c_right = st.columns([1, 800, 1])
    
    with c_left:
        if st.button("❮", key="prev") and st.session_state.card_index > 0:
            st.session_state.card_index -= 1
            st.rerun()

    with c_center:
        text_area_top = "5vh"    
        text_area_bottom = "0vh" 

        html_content = f"""
<div style="position: fixed; top: {text_area_top}; bottom: {text_area_bottom}; left: 0; right: 0; width: 100%; display: flex; align-items: center; justify-content: center; overflow-y: auto; z-index: 1;">
<div style="max-width: 90%; width: 600px; margin: auto; padding-bottom: 5vh;">
<div class="arabic-text" style="font-size: {font_size}; line-height: {line_height};">
{final_html_text}
</div>
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
