import streamlit as st
import requests
import unicodedata
import streamlit.components.v1 as components

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Quran Cards", 
    page_icon="📖", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. SESSION STATE ---
if 'chapter' not in st.session_state: st.session_state.chapter = 1 
if 'start_v' not in st.session_state: st.session_state.start_v = 1
if 'end_v' not in st.session_state: st.session_state.end_v = 7
if 'card_index' not in st.session_state: st.session_state.card_index = 0
if 'show_links' not in st.session_state: st.session_state.show_links = False
if 'view_mode' not in st.session_state: st.session_state.view_mode = 'card' 

# --- 3. HELPER FUNCTIONS ---
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

def to_arabic_numerals(number):
    # Konverterar vanliga siffror till arabiska-indiska siffror (١, ٢, ٣)
    western = '0123456789'
    arabic = '٠١٢٣٤٥٦٧٨٩'
    trans_table = str.maketrans(western, arabic)
    return str(number).translate(trans_table)

def extract_initials(text):
    words = text.split()
    processed_words = []
    
    for word in words:
        if not word: continue
        first_char_group = ""
        captured_base = False
        
        for char in word:
            category = unicodedata.category(char)
            if category != 'Mn': 
                if captured_base: break 
                captured_base = True
                first_char_group += char
            else:
                if captured_base: first_char_group += char
        
        processed_words.append({
            "full": word,
            "short": first_char_group
        })
    return processed_words

def calculate_text_settings(text):
    clean_len = get_clean_length(text)
    max_size, min_size = 7.0, 2.5
    short_threshold, long_threshold = 15, 400
    
    if clean_len <= short_threshold:
        final_size = max_size
        line_height = "2.2"
    elif clean_len >= long_threshold:
        final_size = min_size
        line_height = "1.8"
    else:
        progr = (clean_len - short_threshold) / (long_threshold - short_threshold)
        final_size = max_size - (progr * (max_size - min_size))
        line_height = f"{2.0 - (progr * 0.3):.2f}"

    return f"{final_size:.2f}vw", line_height

# --- 4. CSS & STYLES ---
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
    
    div[data-testid="column"]:nth-of-type(1) .nav-btn > button, 
    div[data-testid="column"]:nth-of-type(3) .nav-btn > button {
        opacity: 0 !important; height: 80vh !important; width: 0% !important; pointer-events: none !important; z-index: 10 !important;
    }

    .arabic-container {
        font-family: 'Scheherazade New', serif;
        direction: rtl;
        text-align: center;
        width: 100%;
        color: #000;
        text-rendering: geometricPrecision; 
        -webkit-font-smoothing: antialiased;
        padding: 0; margin: 0;
    }
    
    .link-hint { color: #C0C0C0; font-size: 0.60em; opacity: 0.8; font-weight: normal; }
    .top-curtain { position: fixed; top: 0; left: 0; width: 100%; height: 4vh; background: white; z-index: 100; }

    /* HIFZ GRID STYLES */
    .hifz-grid {
        direction: rtl;
        font-family: 'Scheherazade New', serif;
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 0.4em;
        padding: 20px;
        line-height: 2.5;
        font-size: 2.2rem;
    }

    .hifz-word {
        position: relative;
        cursor: pointer;
        padding: 0 2px;
        border-radius: 4px;
        transition: background 0.1s;
    }
    
    .hifz-word:active { background-color: #f0f0f0; }
    .hifz-word .full-text { display: none; color: #000; }
    .hifz-word .short-text { display: inline; color: #444; }
    .hifz-word:active .full-text { display: inline; }
    .hifz-word:active .short-text { display: none; }

    /* Snyggare vers-markör */
    .verse-sep { 
        color: #2E8B57; 
        font-size: 0.8em; 
        margin: 0 8px; 
        user-select: none;
        display: inline-block;
    }
    .verse-start .short-text { color: #2E8B57; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

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

# --- 5. DIALOGS & SETTINGS ---
@st.dialog("Settings")
def open_settings():
    new_chapter = st.slider("Chapter", 1, 114, st.session_state.chapter)
    _, _, total_verses = get_chapter_info(new_chapter)

    default_range = (1, total_verses) if new_chapter != st.session_state.chapter else (st.session_state.start_v, min(st.session_state.end_v, total_verses))
    verse_range = st.slider("Verses", 1, total_verses, default_range, key=f"v_slider_{new_chapter}")
    
    show_links = st.toggle("Connection Hints", value=st.session_state.show_links)
    
    is_grid = st.session_state.view_mode == 'grid'
    use_grid = st.toggle("Compact Hifz Mode (First Letter)", value=is_grid)

    if st.button("Load", type="primary", use_container_width=True):
        st.session_state.chapter = new_chapter
        st.session_state.start_v = verse_range[0]
        st.session_state.end_v = verse_range[1]
        st.session_state.card_index = 0
        st.session_state.show_links = show_links
        st.session_state.view_mode = 'grid' if use_grid else 'card'
        st.rerun()

# --- 6. MAIN LOGIC ---
verses_data = fetch_verses_data(st.session_state.chapter)
surah_en, surah_ar, _ = get_chapter_info(st.session_state.chapter)
selected_data = verses_data[st.session_state.start_v - 1 : st.session_state.end_v]

if selected_data:
    # --- HEADER LOGIC ---
    current_verse_data = selected_data[st.session_state.card_index] if st.session_state.card_index < len(selected_data) else selected_data[0]
    juz_num = current_verse_data['juz_number']
    
    # Skapa titel baserat på vy
    if st.session_state.view_mode == 'card':
        # Card View: Ingen versnummer i titeln, men lång sträng
        title_text = f"Juz {juz_num} | Ch {st.session_state.chapter} | {surah_en}"
    else:
        # Grid View: Visa intervall
        title_text = f"Juz {juz_num} | Ch {st.session_state.chapter} | {surah_en} | Verses {st.session_state.start_v}-{st.session_state.end_v}"

    st.markdown('<div class="top-curtain"></div>', unsafe_allow_html=True)
    
    if st.session_state.view_mode == 'card':
        pct = ((st.session_state.card_index + 1) / len(selected_data)) * 100
        st.markdown(f'<div style="position:fixed;top:0;left:0;width:100%;height:4px;background:#f0f0f0;z-index:200;"><div style="width:{pct}%;height:100%;background:#2E8B57;"></div></div>', unsafe_allow_html=True)

    hc1, hc2, hc3 = st.columns([1, 4, 1], vertical_alignment="center")
    
    with hc2: 
        if st.button(title_text, use_container_width=True):
            open_settings()

    # --- VIEW: CARD SWIPE MODE ---
    if st.session_state.view_mode == 'card':
        if st.session_state.card_index >= len(selected_data): st.session_state.card_index = 0
        current_verse = selected_data[st.session_state.card_index]
        raw_text = current_verse['text_uthmani']
        
        # Hämta versnummer och skapa symbol
        v_num = current_verse['verse_key'].split(':')[1]
        v_num_ar = to_arabic_numerals(v_num)
        end_marker = f'<span class="verse-sep" style="font-size: 0.8em;">{v_num_ar} ۝</span>'
        
        font_size, line_height = calculate_text_settings(raw_text)
        
        prev_span = ""
        next_span = ""
        if st.session_state.show_links:
            if st.session_state.card_index > 0:
                p_text = selected_data[st.session_state.card_index - 1]['text_uthmani']
                prev_span = f'<span class="link-hint">{p_text.split(" ")[-1]}</span> '
            if st.session_state.card_index < len(selected_data) - 1:
                n_text = selected_data[st.session_state.card_index + 1]['text_uthmani']
                next_span = f' <span class="link-hint">{n_text.split(" ")[0]}</span>'

        # Lägg till end_marker sist i texten
        full_html_content = f"{prev_span}{raw_text}{end_marker}{next_span}"
        
        container_style = f"font-size: {font_size}; line-height: {line_height};"
        final_html = f'<div class="arabic-container" style="{container_style}">{full_html_content}</div>'

        c_l, c_c, c_r = st.columns([1, 800, 1])
        with c_l:
            st.markdown('<div class="nav-btn">', unsafe_allow_html=True)
            if st.button("❯", key="p") and st.session_state.card_index > 0:
                st.session_state.card_index -= 1
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with c_c:
            st.markdown(f"""
            <div style="position: fixed; top: 5vh; bottom: 0; left: 0; right: 0; display: flex; align-items: center; justify-content: center; overflow-y: auto; z-index: 1;">
                <div style="max-width: 90%; width: 600px; margin: auto; padding-bottom: 5vh;">
                    {final_html}
                </div>
            </div>
            """, unsafe_allow_html=True)
        with c_r:
            st.markdown('<div class="nav-btn">', unsafe_allow_html=True)
            if st.button("❮", key="n") and st.session_state.card_index < len(selected_data) - 1:
                st.session_state.card_index += 1
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # --- VIEW: COMPACT HIFZ MODE (GRID) ---
    elif st.session_state.view_mode == 'grid':
        grid_html = '<div class="hifz-grid">'
        
        for idx, verse in enumerate(selected_data):
            verse_text = verse['text_uthmani']
            words = extract_initials(verse_text)
            
            # Hämta versnummer
            v_num = verse['verse_key'].split(':')[1]
            v_num_ar = to_arabic_numerals(v_num)
            
            for w_idx, word in enumerate(words):
                extra_class = " verse-start" if w_idx == 0 else ""
                
                word_html = (
                    f'<span class="hifz-word{extra_class}" onclick="void(0)">'
                    f'<span class="short-text">{word["short"]}</span>'
                    f'<span class="full-text">{word["full"]}</span>'
                    f'</span>'
                )
                grid_html += word_html
            
            # Lägg till vers-separator med nummer
            grid_html += f'<span class="verse-sep">{v_num_ar} ۝</span>'
        
        grid_html += '</div>'
        
        st.markdown(f"""
        <div style="margin-top: 20px; padding-bottom: 50px;">
            {grid_html}
        </div>
        """, unsafe_allow_html=True)

else:
    if st.button("Öppna inställningar", use_container_width=True): open_settings()
