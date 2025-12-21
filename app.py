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
    max_size, min_size = 7.0, 2.5
    short_threshold, long_threshold = 15, 400
    
    if clean_len <= short_threshold:
        final_size, line_height = max_size, "1.9"
    elif clean_len >= long_threshold:
        final_size, line_height = min_size, "1.65"
    else:
        progr = (clean_len - short_threshold) / (long_threshold - short_threshold)
        final_size = max_size - (progr * (max_size - min_size))
        line_height = f"{1.8 - (progr * 0.3):.2f}"

    return f"{final_size:.2f}vw", line_height

def normalize_text(text):
    """
    Separerar bokstäver från diakritiska tecken (NFD).
    Gör att 'Alif med Madd' (1 tecken) blir 'Alif' + 'Madd' (2 tecken).
    Detta krävs för att kunna färga bara vågen.
    """
    return unicodedata.normalize('NFD', text)

def apply_hifz_coloring(text):
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

def inject_madd_spans(text):
    """
    Oavsett om vi ska färga eller inte, sätter vi in en span-tagg runt madd-tecknen.
    Varför? För att HTML-strukturen MÅSTE vara identisk i båda lagren för att 
    de ska ligga exakt ovanpå varandra.
    """
    # Lista på tecken som ser ut som vågor (Maddah, Small High Madda etc)
    madd_chars = ['\u0653', '\u06E4', '\u0622'] 
    
    # Eftersom vi kör NFD-normalisering innan, letar vi främst efter \u0653
    target_char = '\u0653'
    
    # Vi markerar tecknet med en klass. 
    # CSS styr sedan om den är svart (lager 1) eller rosa (lager 2).
    replacement = f'<span class="madd-mark">{target_char}</span>'
    
    return text.replace(target_char, replacement)

# --- 3. CSS STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Scheherazade+New:wght@400;700&display=swap');
    
    .stApp { background-color: #ffffff; }
    .block-container { padding: 0 !important; margin: 0 !important; max-width: 100% !important; }
    header, footer, [data-testid="stSidebar"] { display: none !important; }
    div[data-testid="stVerticalBlock"] { gap: 0rem !important; }

    .stButton > button {
        color: #2E8B57 !important;
        background: transparent !important;
        border: none !important;
        font-weight: 900 !important;
        z-index: 9999 !important; 
    }
    div[data-testid="column"]:nth-of-type(1) .stButton > button, 
    div[data-testid="column"]:nth-of-type(3) .stButton > button {
        height: 80vh !important; width: 100% !important; opacity: 0;
    }

    /* CONTAINER FÖR LAGREN */
    .quran-container {
        position: relative;
        direction: rtl;
        text-align: center;
        width: 100%;
        font-family: 'Scheherazade New', serif;
        color: #000;
    }

    /* LAGER 1: BOTTEN (Svart text) */
    .layer-base {
        position: relative;
        z-index: 1;
        color: black;
    }
    /* I baslagret ska madd-markeringen ärva färgen (svart eller hifz-orange) */
    .layer-base .madd-mark {
        color: inherit; 
    }

    /* LAGER 2: TOPPEN (Overlay) */
    .layer-overlay {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        z-index: 2;
        pointer-events: none; 
        color: transparent; /* All text osynlig som standard */
    }

    /* I topplagret ska allt vara osynligt UTOM madd-markeringen om switchen är på */
    .layer-overlay * { color: transparent !important; }

    /* Här sätter vi den ROSA färgen. 
       Vi använder text-shadow för att garantera att den syns även om tecknet är tunt. */
    .layer-overlay.show-pink .madd-mark {
        color: #FF1493 !important; 
        text-shadow: 0 0 1px #FF1493;
        opacity: 1 !important;
    }

    .link-hint { color: #C0C0C0; font-size: 0.60em; opacity: 0.8; font-weight: normal; }
    .top-curtain { position: fixed; top: 0; left: 0; width: 100%; height: 4vh; background: white; z-index: 100; }
</style>
""", unsafe_allow_html=True)

# --- 4. SWIPE LOGIC ---
components.html("""
<script>
    const doc = window.parent.document;
    let touchstartX = 0, touchendX = 0;
    doc.addEventListener('touchstart', e => { touchstartX = e.changedTouches[0].screenX; });
    doc.addEventListener('touchend', e => { 
        touchendX = e.changedTouches[0].screenX; 
        if (Math.abs(touchendX - touchstartX) > 60) {
            const btn = doc.querySelectorAll('button')[touchendX < touchstartX ? 2 : 0]; // 0=Prev, 2=Next (approx)
            if (btn) btn.click();
        }
    });
</script>
""", height=0, width=0)

# --- 5. DIALOG ---
@st.dialog("Settings")
def open_settings():
    new_chapter = st.slider("Chapter", 1, 114, st.session_state.chapter)
    _, _, total_verses = get_chapter_info(new_chapter)
    default_range = (1, total_verses) if new_chapter != st.session_state.chapter else (st.session_state.start_v, min(st.session_state.end_v, total_verses))
    
    verse_range = st.slider("Verses", 1, total_verses, default_range, key=f"v_{new_chapter}")
    c1, c2 = st.columns(2)
    hifz = c1.toggle("Hifz Colors", st.session_state.hifz_colors)
    madd = c2.toggle("Madd Colors (Pink)", st.session_state.madd_colors)
    links = st.toggle("Connection Hints", st.session_state.show_links)

    if st.button("Load", type="primary", use_container_width=True):
        st.session_state.chapter = new_chapter
        st.session_state.start_v, st.session_state.end_v = verse_range
        st.session_state.card_index = 0
        st.session_state.hifz_colors = hifz
        st.session_state.madd_colors = madd
        st.session_state.show_links = links
        st.rerun()

# --- 6. RENDER ---
verses_data = fetch_verses_data(st.session_state.chapter)
surah_en, surah_ar, _ = get_chapter_info(st.session_state.chapter)
selected_data = verses_data[st.session_state.start_v - 1 : st.session_state.end_v]

if selected_data:
    if st.session_state.card_index >= len(selected_data): st.session_state.card_index = 0
    curr = selected_data[st.session_state.card_index]
    
    # 1. Normalisera (separera Alif och Madd till två tecken)
    normalized_text = normalize_text(curr['text_uthmani'])
    
    font_size, line_height = calculate_text_settings(normalized_text)
    
    # 2. Applicera Hifz-färgning (på hela texten först)
    processed_text = normalized_text
    if st.session_state.hifz_colors:
        processed_text = apply_hifz_coloring(processed_text)
        
    # 3. Injicera Madd-spans i texten.
    # Vi gör detta oavsett om färgen är på eller av, för att båda lagren ska ha SAMMA struktur.
    final_structure = inject_madd_spans(processed_text)
    
    # Bestäm om overlay ska visa rosa eller inte via en CSS-klass
    overlay_class = "show-pink" if st.session_state.madd_colors else ""

    # Hints Logic
    prev_h, next_h = "", ""
    if st.session_state.show_links:
        if st.session_state.card_index > 0:
            w = selected_data[st.session_state.card_index-1]['text_uthmani'].split(" ")[-1]
            prev_h = f'<span class="link-hint">{w}</span> '
        if st.session_state.card_index < len(selected_data)-1:
            w = selected_data[st.session_state.card_index+1]['text_uthmani'].split(" ")[0]
            next_h = f' <span class="link-hint">{w}</span>'

    # HTML Output
    html_content = f"""
    <div style="position: fixed; top: 5vh; bottom: 0; left: 0; right: 0; display: flex; align-items: center; justify-content: center; overflow-y: auto; z-index: 1;">
        <div style="max-width: 90%; width: 600px; margin: auto; padding-bottom: 5vh;">
            <div class="quran-container" style="font-size: {font_size}; line-height: {line_height};">
                {prev_h}
                <span style="position: relative; display: inline-block;">
                    <span class="layer-base">{final_structure}</span>
                    <span class="layer-overlay {overlay_class}">{final_structure}</span>
                </span>
                {next_h}
            </div>
        </div>
    </div>
    """

    st.markdown('<div class="top-curtain"></div>', unsafe_allow_html=True)
    pct = ((st.session_state.card_index + 1) / len(selected_data)) * 100
    st.markdown(f'<div style="position:fixed;top:0;left:0;width:100%;height:4px;background:#f0f0f0;z-index:200;"><div style="width:{pct}%;height:100%;background:#2E8B57;"></div></div>', unsafe_allow_html=True)

    hc1, hc2, hc3 = st.columns([1, 4, 1], vertical_alignment="center")
    with hc2: 
        if st.button(f"Juz {curr['juz_number']} | Ch {st.session_state.chapter} | {surah_en} | Verse {curr['verse_key'].split(':')[1]}", use_container_width=True): open_settings()

    c1, c2, c3 = st.columns([1, 800, 1])
    with c1: 
        if st.button("❮", key="prev") and st.session_state.card_index > 0: st.session_state.card_index -= 1; st.rerun()
    with c2: st.markdown(html_content, unsafe_allow_html=True)
    with c3: 
        if st.button("❯", key="next") and st.session_state.card_index < len(selected_data)-1: st.session_state.card_index += 1; st.rerun()
else:
    if st.button("Öppna inställningar"): open_settings()
